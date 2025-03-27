"""A module to scrape job listings from the DOU website 
and send notifications to a Telegram chat."""
import re
import sqlite3
import time
import logging
from typing import Any, List, Dict, Optional

import requests
from bs4 import BeautifulSoup, Tag, ResultSet
from config.scraper_config import DouScraperConfig
from config.settings import TELEGRAM_TOKEN, CHAT_ID, NO_EXP_TELEGRAM_TOKEN, NO_EXP_CHAT_ID, DB_PATH
from models.dou_job import DouJob

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DouJobScraper:
    """A class to scrape job listings from the DOU website 
    and send notifications to a Telegram chat."""
    BASE_URL = "https://jobs.dou.ua/vacancies/"
    BASE_URL_NO_EXP = "https://jobs.dou.ua/first-job/"
    TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"

    def __init__(
            self,
            config: DouScraperConfig
    ) -> None:
        self.config = config
        self.base_url = self.BASE_URL_NO_EXP if self.config.no_exp else self.BASE_URL
        self.full_url: str = self._construct_full_url()
        self._initialize_database()
        self._create_indexes()

    def _initialize_database(self) -> None:
        """Creates a database table if it doesn't exist."""
        with sqlite3.connect(self.config.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dou_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    title TEXT,
                    link TEXT,
                    company TEXT,
                    salary TEXT,
                    cities TEXT,
                    sh_info TEXT,
                    category TEXT,
                    experience TEXT,
                    UNIQUE(title, date, company, category)
                )
            """)
            conn.commit()

    def _create_indexes(self) -> None:
        """Creates indexes on relevant columns to optimize database queries."""
        with sqlite3.connect(self.config.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_title_date_company_category ON dou_jobs (title, date, company, category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON dou_jobs (category)")
            conn.commit()

    def _construct_full_url(self) -> str:
        """Constructs the full URL for job scraping based on filters."""
        if sum(map(bool, [self.config.remote, self.config.relocation, self.config.city])) > 1:
            raise ValueError("Only one of 'remote', 'relocation', or 'city' can be specified.")

        filters: list = []
        if self.config.remote and not self.config.no_exp:
            filters.append("remote")
        if self.config.relocation and not self.config.no_exp:
            filters.append("relocation")
        if self.config.city:
            filters.append(f"city={self.config.city}")
        if self.config.category and not self.config.no_exp:
            filters.append(f"category={self.config.category}")
        if self.config.experience and not self.config.no_exp:
            filters.append(f"exp={self.config.experience}")

        return self.base_url + "?" + "&".join(filters)

    @staticmethod
    def _clean_text_for_telegram(text: str) -> str:
        """
        Escapes special characters and formats multiline text for Telegram MarkdownV2.
        """
        if not text:
            return ""

        # Normalize new lines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r'\n{2,}', r'\n', text)  # Remove extra empty lines

        # Replace em dash and en dash
        text = text.replace("—", "-").replace("–", "-")

        # Escape backslash first
        text = text.replace("\\", "\\\\")

        # Escape all markdown v2 special characters
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        text = re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

        return text.strip()

    def get_list_jobs(self) -> List[DouJob]:
        """Scrapes job offers and returns a list of DouJob objects."""
        job_offers: List[DouJob] = []
        try:
            response: requests.Response = requests.get(
                self.full_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=30,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards: ResultSet[Tag] = soup.select("ul > li.l-vacancy")

            for job_card in job_cards:
                job: DouJob | None = self._extract_job_data(job_card)
                if job:
                    job_offers.append(job)

        except requests.RequestException as err:
            logging.error("Error retrieving data from the site: %s", err)

        return job_offers[::-1]

    def _extract_job_data(self, job_card: Tag) -> Optional[DouJob]:
        """Extracts job data from a single job card."""
        try:
            date: str = job_card.select_one("div.date").text.strip()
            title_tag: Tag | None = job_card.select_one("div.title > a")
            company_tag: Tag | None = job_card.select_one("div.title > strong")
            salary_tag: Tag | None = job_card.select_one("span.salary")
            cities_tag: Tag | None = job_card.select_one("span.cities")
            short_info_tag: Tag | None = job_card.select_one("div.sh-info")
            category_job: str = self.config.category if self.config.category else "No category"
            experience_job: str = self.config.experience if self.config.experience else "No experience"

            return DouJob(
                date=date,
                title=title_tag.text.strip() if title_tag else None,
                link=title_tag.get("href") if title_tag else None,
                company=company_tag.text.strip() if company_tag else None,
                salary=salary_tag.text.strip() if salary_tag else None,
                cities=cities_tag.text.strip() if cities_tag else None,
                sh_info=short_info_tag.text.strip() if short_info_tag else None,
                category=category_job,
                experience=experience_job,
            )
        except AttributeError as err:
            logging.error("Error extracting job data: %s", err)
            return None

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalizes the date format for consistency."""
        try:
            # Check if the date contains the year 2024 or 2025
            if any(year in date_str for year in ["2024", "2025", "2026", "2027", "2028", "2029", "2030"]):
                # Delete the year from the date
                date_str = date_str.split()[:2]  # Leave only day and month
                date_str = " ".join(date_str)
            return date_str
        except ValueError as err:
            raise ValueError(f"Impossible processing date: {date_str}. Error: {err}") from err

    def _normalize_job_data(self, job: DouJob) -> DouJob:
        """Normalizes job data before adding it to the database."""
        job.title = job.title.strip().lower() if job.title else None
        job.company = job.company.strip().lower() if job.company else None
        job.category = job.category.strip().lower() if job.category else None
        job.date = self._normalize_date(job.date.strip()) if job.date else None
        return job

    def check_and_add_jobs(self) -> List[DouJob]:
        """Checks for new jobs and adds them to the database."""
        new_jobs: list = []
        job_offers: List[DouJob] = self.get_list_jobs()

        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            for job in job_offers:
                try:
                    job: DouJob = self._normalize_job_data(job)

                    cursor.execute("""
                        SELECT 1 FROM dou_jobs WHERE title = :title AND date = :date AND company = :company AND category = :category
                    """, job.__dict__)
                    if not cursor.fetchone():
                        try:
                            cursor.execute("""
                                INSERT INTO dou_jobs (date, title, link, company, salary, cities, sh_info, category, experience)
                                VALUES (:date, :title, :link, :company, :salary, :cities, :sh_info, :category, :experience)
                            """, job.__dict__)
                            new_jobs.append(job)
                            self._send_job_to_telegram(job)
                        except sqlite3.IntegrityError as e:
                            logging.warning("Duplicate job entry detected: %s - %s - %s", job.title, job.company, e)
                        except sqlite3.Error as e:
                            logging.error("Error inserting job into database: %s - %s", job, e)
                    conn.commit()
                except Exception as e:  # Catch all exceptions
                    logging.error("An unexpected error occurred: %s", e)
                    conn.rollback()
        if not new_jobs:
            logging.info(f"No new jobs found at Dou {job.category} category with experience {self.config.experience}.")
        return new_jobs

    def _create_telegram_message(self, job: DouJob) -> str:
        """Creates a formatted message for Telegram."""
        experience: str = self.config.experience.replace("+", " ") if self.config.experience else "No experience"

        title = self._clean_text_for_telegram(job.title or "No title")
        company = self._clean_text_for_telegram(job.company or "No company")
        category = self._clean_text_for_telegram(job.category or "No category")
        salary = self._clean_text_for_telegram(job.salary or "N/A")
        cities = self._clean_text_for_telegram(job.cities or "N/A")
        sh_info = self._clean_text_for_telegram((job.sh_info or "N/A")[:1000])
        date = self._clean_text_for_telegram(job.date or "N/A")
        experience_clean = self._clean_text_for_telegram(experience)

        return (
            "DOU.UA PRESENT \n"
            f"*Date:* {date}\n"
            f"[{title}]({job.link}) *{company}*\n"
            f"*Experienced:* {experience_clean} years\n"
            f"*Category:* {category}\n"
            f"*Salary:* {salary}\n"
            f"*Cities:* {cities}\n"
            f"*Info:* {sh_info}"
        )

    def _send_job_to_telegram(self, job: DouJob) -> None:
        """Sends a job offer to a Telegram chat."""
        message: str = self._create_telegram_message(job)
        payload: Dict[str, Any] = {
            "chat_id": self.config.chat_id,
            "text": message,
            "parse_mode": None,
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
                logging.info(f"Job sent to Telegram successfully at Dou {job.category} category with experience {self.config.experience}.")
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
            cursor.execute("SELECT * FROM dou_jobs")
            return cursor.fetchall()

    def list_no_category_jobs_in_db(self) -> List[Dict[str, str]]:
        """Returns a list of jobs in the database where category is 'No category'."""
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("SELECT * FROM dou_jobs WHERE category = ?", ("No category",))
            return cursor.fetchall()

    def list_same_title_jobs_in_db(self, title: str) -> List[Dict[str, str]]:
        """Returns a list of jobs in the database with the same title."""
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()

            # Execute a query to find jobs with the same title
            cursor.execute("SELECT * FROM dou_jobs WHERE title = ?", (title,))

            # Get all results
            rows = cursor.fetchall()

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Convert each row into a dictionary
            return [dict(zip(column_names, row)) for row in rows]

    def list_jobs_by_category(self, category: str) -> List[Dict[str, str]]:
        """Returns a list of jobs in the database belonging to the specified category."""
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()

            # Execute a query to find jobs by category
            cursor.execute("SELECT * FROM dou_jobs WHERE category = ?", (category,))

            # Get all results
            rows = cursor.fetchall()

            # Get column names
            column_names = [desc[0] for desc in cursor.description]

            # Convert each row into a dictionary
            return [dict(zip(column_names, row)) for row in rows]

    def duplicate_jobs_in_db(self) -> List[Dict[str, str]]:
        """
        Returns a list of duplicate jobs in the database based on title, 
        date, company, and category.
        """
        with sqlite3.connect(self.config.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()

            # SQL query to find duplicates
            cursor.execute("""
                SELECT * 
                FROM dou_jobs
                WHERE (title, date, company, category) IN (
                    SELECT title, date, company, category
                    FROM dou_jobs
                    GROUP BY title, date, company, category
                    HAVING COUNT(*) > 1
                )
                ORDER BY title, date, company, category
            """)

            # Fetch all duplicates
            duplicates = cursor.fetchall()
            # Get column names for returning data as a list of dictionaries
            column_names = [desc[0] for desc in cursor.description]
            return [dict(zip(column_names, row)) for row in duplicates]


if __name__ == "__main__":

    # Configuration for checking new jobs for experience level 0-1 years on DOU
    dou_config_0_1 = DouScraperConfig(
        db_path=DB_PATH,
        telegram_token=TELEGRAM_TOKEN,
        chat_id=CHAT_ID,
        category="Python",
        experience="0-1",
    )

    # Configuration for checking new jobs for experience level 1-3 years on DOU
    dou_config_1_3 = DouScraperConfig(
        db_path=DB_PATH,
        telegram_token=TELEGRAM_TOKEN,
        chat_id=CHAT_ID,
        category="Python",
        experience="1-3",
    )

    # Configuration for checking new jobs for no experience level on DOU
    dou_config_no_exp = DouScraperConfig(
        db_path=DB_PATH,
        telegram_token=NO_EXP_TELEGRAM_TOKEN,
        chat_id=NO_EXP_CHAT_ID,
        no_exp=True,
    )

    # Initialize the scraper with the configuration
    dou_scraper_0_1 = DouJobScraper(dou_config_0_1)
    dou_scraper_0_1.check_and_add_jobs()
    # print(dou_scraper_0_1.list_same_title_jobs_in_db("customer support agent with english and german (everhelp)"))
