import logging
import sqlite3
import time
from html import unescape
from typing import List, Dict, Any

import feedparser
import requests
from bs4 import BeautifulSoup
from config.scraper_config import DjinniScraperConfig
from config.settings import TELEGRAM_TOKEN, CHAT_ID, NO_EXP_TELEGRAM_TOKEN, NO_EXP_CHAT_ID, DB_PATH, DJINNI_PYTHON_URL
from models.djinni_job import DjinniJob

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DjinniJobScraper:
    TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"

    def __init__(self, config: DjinniScraperConfig) -> None:
        self.config = config
        self.db = config.db_path
        self.telegram_token = config.telegram_token
        self.chat_id = config.chat_id
        self.djinni_url = config.djinni_url
        self.djinni_category = config.djinni_category
        self._initialize_database()
        self._create_indexes()

    def _initialize_database(self) -> None:
        """Creates a database table if it doesn't exist."""
        with sqlite3.connect(self.config.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS djinni_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    title TEXT,
                    link TEXT,
                    description TEXT,
                    category TEXT,
                    UNIQUE(date, link)
                )
            """)
            conn.commit()

    def _create_indexes(self) -> None:
        """Creates indexes on relevant columns to optimize database queries."""
        with sqlite3.connect(self.config.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_link ON djinni_jobs (date, link)")
            conn.commit()

    @staticmethod
    def _clean_text_for_telegram(text: str) -> str:
        """Cleans text for Telegram compatibility."""
        return text.replace("`", "'").replace("’", "'").strip()

    def get_list_jobs(self) -> List[DjinniJob]:
        job_offers: List[DjinniJob] = []
        try:
            # Завантаження і розбір RSS
            feed = feedparser.parse(self.djinni_url)

            # Обробка вакансій
            for entry in feed.entries[:]:
                # Назва вакансії
                title = entry.title

                # Лінк на вакансію
                link = entry.link

                # Опис вакансії (з HTML декодуванням)
                raw_description = unescape(entry.summary)
                description = BeautifulSoup(raw_description, "html.parser").get_text()
                description = description[:300]

                # Дата публікації
                pub_date = entry.published

                # Категорії (якщо є)
                categories = entry.get("tags", [])
                category_list = [tag.term for tag in categories]
                category_result = ", ".join(category_list)
                job: DjinniJob = DjinniJob(pub_date, title, link, description, category_result)
                if job:
                    job_offers.append(job)
            return job_offers[::-1]
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return job_offers[::-1]

    def _normalize_job_data(self, job: DjinniJob) -> DjinniJob:
        """Normalizes job data before adding it to the database."""
        job.date = job.date.strip() if job.date else None
        job.title = job.title.strip().lower() if job.title else None
        job.link = job.link.strip().lower() if job.link else None
        job.description = job.description.strip().lower() if job.description else None
        job.category = job.category.strip().lower() if job.category else None
        return job

    def check_and_add_jobs(self) -> List[DjinniJob]:
        """Checks for new jobs and adds them to the database."""
        new_jobs: list = []
        job_offers: List[DjinniJob] = self.get_list_jobs()

        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            for job in job_offers:
                try:
                    job: DjinniJob = self._normalize_job_data(job)

                    cursor.execute("""
                        SELECT 1 FROM djinni_jobs WHERE date = :date AND link = :link
                    """, job.__dict__)
                    if not cursor.fetchone():
                        try:
                            cursor.execute("""
                                INSERT INTO djinni_jobs (date, title, link, description, category)
                                VALUES (:date, :title, :link, :description, :category)
                            """, job.__dict__)
                            new_jobs.append(job)
                            self._send_job_to_telegram(job)
                        except sqlite3.IntegrityError as e:
                            logging.warning("Duplicate job entry detected: %s - %s - %s", job.title, job.link, e)
                        except sqlite3.Error as e:
                            logging.error("Error inserting job into database: %s - %s", job, e)
                    conn.commit()
                except Exception as e:  # Catch all exceptions
                    logging.error("An unexpected error occurred: %s", e)
                    conn.rollback()
        if not new_jobs:
            logging.info(f"No new jobs found at Djinni {job.category} category.")
        return new_jobs

    def _create_telegram_message(self, job: DjinniJob) -> str:
        """Creates a formatted message for Telegram."""
        djinni_category: str = self.djinni_category or "N/A"
        return (
            ""
            f"*djinni.co in category:* {djinni_category} \n"
            f"*Date:* {job.date}\n"
            f"[{job.title}]({job.link})\n"
            f"*Description:* {job.description}\n"
            f"*Category:* {self._clean_text_for_telegram(job.category or 'N/A')}\n"
        )

    def _send_job_to_telegram(self, job: DjinniJob) -> None:
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
                logging.info(f"Job sent to Telegram successfully at Djinni {job.category} category.")
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


if __name__ == "__main__":
    python_config = DjinniScraperConfig(
        db_path=DB_PATH,
        telegram_token=TELEGRAM_TOKEN,
        chat_id=CHAT_ID,
        djinni_url=DJINNI_PYTHON_URL,
        djinni_category="Python",
    )
    scraper = DjinniJobScraper(python_config)
    for item in scraper.get_list_jobs():
        print(item)
        print("=============================================")
