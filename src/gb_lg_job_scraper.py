import sqlite3
import time
import re
import logging
from typing import Any, List, Dict, Optional

import requests
from bs4 import BeautifulSoup, Tag, ResultSet

from config.scraper_config import GlobalLogicScraperConfig
from config.settings import TELEGRAM_TOKEN, DB_PATH, CHAT_ID

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GlobalLogicJobScraper:
    """
    A class used to scrape job offers
    """
    BASE_URL = "https://www.globallogic.com/career-search-page/?"
    TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"

    def __init__(
            self,
            config: GlobalLogicScraperConfig
    ) -> None:
        self.config = config
        self.base_url = self.BASE_URL
        self.full_url: str = self._construct_full_url()
        self._initialize_database()
        self._create_indexes()

    def _initialize_database(self) -> None:
        """Creates a database table if it doesn't exist."""
        with sqlite3.connect(self.config.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gl_lg_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    link TEXT,
                    requirements TEXT,
                    UNIQUE(title, link)
                )
            """)
            conn.commit()

    def _create_indexes(self) -> None:
        """Creates indexes for the database table."""
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS title_index ON gl_lg_jobs (title)")
            cursor.execute("CREATE INDEX IF NOT EXISTS link_index ON gl_lg_jobs (link)")
            conn.commit()

    def _construct_full_url(self) -> str:
        """
        Builds the full URL for job scraping based on initialized filters.
        
        Returns:
            str: The constructed full URL with specified filters.
        """
        url: str = (
            f"{self.base_url}keywords={self.config.keywords}&experience={self.config.experience}&locations={self.config.locations}&c="
        )
        if self.config.freelance:
            url += "&freelance=yes"

        work_models: list = []
        if self.config.remote:
            work_models.append("Remote")
        if self.config.hybrid:
            work_models.append("Hybrid")
        if self.config.on_site:
            work_models.append("On-site")
        if work_models:
            url += "&workmodel=" + ",".join(work_models)

        return url

    @staticmethod
    def _clean_text_for_telegram(text: str) -> str:
        """Cleans text for Telegram compatibility."""
        return text.replace("`", "'").replace("’", "'").strip()

    def get_list_jobs(self) -> List[Dict[str, Optional[str]]]:
        job_offers: list = []
        try:
            response: requests.Response = requests.get(
                self.full_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards: ResultSet[Tag] = soup.select("div.career-pagelink")

            for job_card in job_cards:
                job: Dict[str, Optional[str]] = self._extract_job_data(job_card)
                if job:
                    job_offers.append(job)

        except requests.RequestException as err:
            logging.error("Error retrieving data from the site: %s", err)

        return job_offers[::-1]

    def _extract_job_data(self, job_card: Tag) -> Optional[Dict[str, Optional[str]]]:
        """Extracts job data from a single job card."""
        try:
            title_element: Tag | None = job_card.select_one("p > a")
            if title_element:
                title: str = title_element.text.strip()
                link: str | List[str] | None = title_element.get("href")

                requirements_element: Tag | None = job_card.select_one("p.id-num")
                requirements: str | None = (
                    re.sub(r"\s+", " ", requirements_element.text.strip())
                    if requirements_element
                    else None
                )
                return {"title": title, "link": link, "requirements": requirements}
        except AttributeError as err:
            logging.error("Error extracting job data: %s", err)
            return None

    @staticmethod
    def _normalize_job_data(job: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
        """Normalizes job data before inserting into the database."""
        job['title'] = job['title'].strip().lower() if job['title'] else None
        job['link'] = job['link'].strip() if job['link'] else None
        return job

    def check_and_add_jobs(self) -> List[Dict[str, Optional[str]]]:
        """
        Retrieves job offers, inserts new jobs into the database, and sends them to Telegram.
        This method performs the following steps:
        1. Retrieves a list of job offers.
        2. Connects to the SQLite database specified by `self.db_path`.
        3. Iterates over the job offers and attempts to insert each job into the `gl_lg_jobs` table.
        4. If a job is successfully inserted, it is added to the `new_jobs` list and sent to Telegram.
        5. If a job already exists in the database (based on a unique title constraint), it is skipped.
        6. Commits the transaction to the database.
        7. Returns the list of new jobs that were added to the database.
        Returns:
            List[Dict[str, Optional[str]]]: A list of dictionaries representing the new jobs that were added to the database.
        """
        job_offers: List[Dict[str, str | None]] = self.get_list_jobs()
        new_jobs: list = []

        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()

            for job in job_offers:
                try:
                    job: Dict[str, str | None] = self._normalize_job_data(job)
                    cursor.execute("""
                        SELECT 1 FROM gl_lg_jobs WHERE title = :title AND link = :link
                    """, job)
                    if not cursor.fetchone():
                        try:
                            cursor.execute("""
                                INSERT INTO gl_lg_jobs (title, link, requirements)
                                VALUES (:title, :link, :requirements)
                            """, job)
                            new_jobs.append(job)
                            self._send_job_to_telegram(job)
                        except sqlite3.IntegrityError as err:
                            logging.warning("Duplicate job entry detected: %s - %s - %s", job['title'], job['link'], err)
                        except sqlite3.Error as err:
                            logging.error("Error inserting job into the database: %s - %s", job, err)
                    conn.commit()
                except Exception as err:
                    logging.error("Error occurred while checking and adding jobs: %s", err)
                    conn.rollback()
        if not new_jobs:
            logging.info("No new jobs found at GlobalLogic.")
        return new_jobs

    def _create_telegram_message(self, job: Dict[str, Optional[str]]) -> str:
        """Creates a formatted message for Telegram."""
        return (
            "GLOBAL LOGIC PRESENT \n"
            f"[{job['title']}]({job['link']})\n"
            f"*Requirements:* {self._clean_text_for_telegram(job['requirements']) or 'N/A'}\n"
        )

    def _send_job_to_telegram(self, job: Dict[str, Optional[str]]) -> None:
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
                        "Telegram API rate limit exceeded. Waiting and retrying after %s seconds.", retry_time
                    )
                    time.sleep(retry_time)
                    continue
                response.raise_for_status()
                logging.info("Job sent to Telegram successfully.")
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

    def list_jobs_in_db(self) -> List[Dict[str, str]]:
        """Returns a list of all jobs in the database."""
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("SELECT * FROM gl_lg_jobs")
            return cursor.fetchall()


if __name__ == "__main__":

    gb_lg_scraper_python_config_0_1 = GlobalLogicScraperConfig(
        db_path=DB_PATH,
        telegram_token=TELEGRAM_TOKEN,
        chat_id=CHAT_ID,
        keywords="python",
        experience="0-1+years",
        locations="ukraine",
    )
    gb_lg_scraper_python_0_1 = GlobalLogicJobScraper(gb_lg_scraper_python_config_0_1)
    # gb_lg_scraper_python_0_1.check_and_add_jobs()
    for gl_lg_job in gb_lg_scraper_python_0_1.list_jobs_in_db():
        print(gl_lg_job)
