import logging
import re
import sqlite3
import time
from typing import Any, List, Dict

import cloudscraper
import requests
from bs4 import BeautifulSoup

from config.scraper_config import BlackHatWorldScraperConfig
from config.settings import TELEGRAM_TOKEN, CHAT_ID, DB_PATH
from models.blackhatworld_job import BlackHatWorldJob

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class BlackHatWorldJobScraper:
    """A class to scrape job listings from the blackhatworld.com/forums/hire-a-freelancer.76/ website
    and send notifications to a Telegram chat."""
    BASE_URL = "https://www.blackhatworld.com"
    TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"
    keywords = ["scraping", "parsing", "scraper", "parser"]

    def __init__(
            self,
            config: BlackHatWorldScraperConfig
    ) -> None:
        self.config = config
        self.base_url = self.BASE_URL
        self._initialize_database()
        self._create_indexes()

    def _initialize_database(self) -> None:
        """Creates a database table if it doesn't exist."""
        with sqlite3.connect(self.config.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS black_hat_world_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    link TEXT,
                    UNIQUE(link)
                )
            """)
            conn.commit()

    def _create_indexes(self) -> None:
        """Creates indexes on relevant columns to optimize database queries."""
        with sqlite3.connect(self.config.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_title_link ON black_hat_world_jobs (title, link)")
            conn.commit()

    @staticmethod
    def _clean_text_for_telegram(text: str) -> str:
        """Cleans text for Telegram compatibility."""
        return text.replace("`", "'").replace("’", "'").strip()

    def get_list_jobs(self) -> List[BlackHatWorldJob]:
        """Scrapes job offers and returns a list of BlackHatWorldJob objects."""
        job_offers: List[BlackHatWorldJob] = []
        url = self.BASE_URL + "/forums/hire-a-freelancer.76/?order=post_date&direction=desc"
        scraper = cloudscraper.create_scraper()
        try:
            response = scraper.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            ad_cards = soup.select("div.structItem.structItem--thread.js-inlineModContainer")
            logging.info(f"There are a : {len(ad_cards)} job offers on page.")
            for card in ad_cards:
                title_element = card.select_one("div.structItem-title a")
                if title_element:
                    link = self.BASE_URL + title_element.get("href")
                    title = title_element.text.strip()
                    title = re.sub(r"\s+", " ", title)
                    logging.info(f"There are a : {title} job offer")
                    for word in self.keywords:
                        if word in title.lower():
                            job_offers.append(
                                BlackHatWorldJob(title=title, link=link)
                            )
        except scraper.RequestsException as err:
            logging.error(f"An error occurred: {err}")
        except AttributeError as error:
            logging.error("Error extracting job data: %s", error)
        return job_offers

    def _normalize_job_data(self, job: BlackHatWorldJob) -> BlackHatWorldJob:
        """Normalizes job data before adding it to the database."""
        job.title = job.title.strip().lower() if job.title else None
        job.link = job.link.strip().lower() if job.link else None
        return job

    def check_and_add_jobs(self) -> List[BlackHatWorldJob]:
        """Checks for new jobs and adds them to the database."""
        new_jobs: List[BlackHatWorldJob] = []
        job_offers: List[BlackHatWorldJob] = self.get_list_jobs()
        logging.info(f"Scraped jobs: {job_offers}")
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            for job in job_offers:
                try:
                    job: BlackHatWorldJob = self._normalize_job_data(job)

                    cursor.execute("""
                        SELECT 1 FROM black_hat_world_jobs WHERE title = :title AND link = :link
                    """, (job.title, job.link))
                    if not cursor.fetchone():
                        try:
                            logging.info(f"Trying to insert job: {job.title} - {job.link}")
                            cursor.execute("""
                                INSERT INTO black_hat_world_jobs (title, link)
                                VALUES (:title, :link)
                            """, (job.title, job.link))
                            new_jobs.append(job)
                            logging.info(f"New job list: {new_jobs}")
                            self._send_job_to_telegram(job)
                        except sqlite3.IntegrityError as e:
                            logging.warning("Duplicate job entry detected: %s - %s - %s", job.title, job.link, e)
                        except sqlite3.Error as e:
                            logging.error("Error inserting job into database: %s - %s", job, e)
                    conn.commit()
                    logging.info(f"Successfully inserted: {job.title}")
                except Exception as e:  # Catch all exceptions
                    logging.error("An unexpected error occurred: %s", e)
                    conn.rollback()
        if not new_jobs:
            logging.info(f"No new jobs found at BlackHatWorld.")
        return new_jobs

    def _create_telegram_message(self, job: BlackHatWorldJob) -> str:
        """Creates a formatted message for Telegram."""
        return (
            "BlackHatWorld  Freelance \n"
            f"[{self._clean_text_for_telegram(job.title)}]({job.link})\n"
        )

    def _send_job_to_telegram(self, job: BlackHatWorldJob) -> None:
        """Sends a job offer to a Telegram chat."""
        message: str = self._create_telegram_message(job)
        payload: Dict[str, Any] = {
            "chat_id": self.config.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        while True:
            try:
                response: requests.Response = requests.post(
                    self.TELEGRAM_API_URL.format(self.config.telegram_token),
                    data=payload,
                    timeout=60,
                )
                if response.status_code == 429:
                    retry_time = self._get_retry_time(response)
                    logging.warning(
                        "Telegram API rate limit exceeded. Waiting and retrying after %s seconds.",
                        retry_time
                    )
                    time.sleep(retry_time)
                    continue
                response.raise_for_status()
                logging.info(f"Job sent to Telegram successfully at BlackHatWorld.")
                break
            except requests.exceptions.HTTPError as err:
                logging.error("HTTP error occurred: %s", err)
                time.sleep(10)
            except requests.exceptions.ConnectionError as err:
                logging.error("Connection error occurred: %s", err)
                time.sleep(10)
            except requests.exceptions.Timeout as err:
                logging.error("Timeout error occurred: %s", err)
                time.sleep(10)
            except requests.exceptions.RequestException as err:
                logging.error("Failed to send job to Telegram: %s", err)
                time.sleep(10)

    @staticmethod
    def _get_retry_time(response: requests.Response) -> int:
        """Extracts retry time from the Telegram API response."""
        try:
            return int(response.json().get("parameters", {}).get("retry_after", 5))
        except (ValueError, KeyError):
            return 5

    def list_all_jobs_in_db(self) -> List[Dict[str, str]]:
        """Returns a list of all jobs in the database."""
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("SELECT * FROM black_hat_world_jobs")
            return cursor.fetchall()


if __name__ == "__main__":
    # Configuration for checking new scraping freelance offers on BlackHatWorld
    black_hat_world_config = BlackHatWorldScraperConfig(
        db_path=DB_PATH,
        telegram_token=TELEGRAM_TOKEN,
        chat_id=CHAT_ID,
    )
    black_hat_world_scraper = BlackHatWorldJobScraper(black_hat_world_config)
    print(black_hat_world_scraper.check_and_add_jobs())
    # print(black_hat_world_scraper.list_all_jobs_in_db())
