"""
dou_jobs_scraper.py

This module defines the DouJobScraper class, which is used to scrape job 
listings from the Dou.ua website and send notifications to a Telegram chat. 
The script can be run as a standalone program to check for new job listings 
and send them to a specified Telegram chat.

Classes:
    DouJobScraper: A class to scrape job listings from the Dou.ua 
    website and send notifications to a Telegram chat.

Functions:
    main(): The main function that initializes the DouJobScraper and checks for new job listings.

Usage:
    Set the following environment variables before running the script:
        TELEGRAM_TOKEN: The Telegram bot token.
        NO_EXP_TELEGRAM_TOKEN: The Telegram bot token for no experience jobs.
        CHAT_ID: The Telegram chat ID.
        NO_EXP_CHAT_ID: The Telegram chat ID for no experience jobs.
        DB_PATH: The path to the SQLite database file.

    Example:
        $ export TELEGRAM_TOKEN="your_telegram_token"
        $ export NO_EXP_TELEGRAM_TOKEN="your_no_exp_telegram_token"
        $ export CHAT_ID="your_chat_id"
        $ export NO_EXP_CHAT_ID="your_no_exp_chat_id"
        $ export DB_PATH="path_to_your_db.sqlite"
        $ python dou_jobs_scraper.py
"""
import sqlite3
import time
import os
import logging
from typing import Any, List, Dict, Optional
from dotenv import load_dotenv

import requests
from bs4 import BeautifulSoup, Tag, ResultSet

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DouJobScraper:
    """
    A class to scrape job listings from the Dou.ua website and 
    send notifications to a Telegram chat.
    Attributes:
        BASE_URL (str): The base URL for job listings.
        BASE_URL_NO_EXP (str): The base URL for job listings with no experience required.
        TELEGRAM_API_URL (str): The URL for the Telegram API to send messages.
    Methods:
        __init__(
        telegram_token, chat_id, db_path, 
        category=None, experience=None, city=None, 
        remote=False, relocation=False, no_exp=False
        ):
            Initializes the DouJobScraper with the given parameters.
        _initialize_database():
            Creates a database table if it doesn't exist.
        _construct_full_url():
            Constructs the full URL for job scraping based on filters.
        _clean_text_for_telegram(text):
            Cleans text for Telegram compatibility.
        get_list_jobs():
            Scrapes job offers and returns a list of dictionaries.
        _extract_job_data(job_card):
            Extracts job data from a single job card.
        check_and_add_jobs():
            Checks for new jobs and adds them to the database.
        _create_telegram_message(job):
            Creates a formatted message for Telegram.
        _send_job_to_telegram(job):
            Sends a job offer to a Telegram chat.
        _get_retry_time(response):
            Extracts retry time from the Telegram API response.
        list_jobs_in_db():
            Returns a list of all jobs in the database.
    """

    BASE_URL = "https://jobs.dou.ua/vacancies/"
    BASE_URL_NO_EXP = "https://jobs.dou.ua/first-job/"
    TELEGRAM_API_URL = "https://api.telegram.org/bot{}/sendMessage"

    def __init__(
        self,
        telegram_token: str,
        chat_id: str,
        db_path: str,
        category: Optional[str] = None,
        experience: Optional[str] = None,
        city: Optional[str] = None,
        remote: bool = False,
        relocation: bool = False,
        no_exp: bool = False,
    ) -> None:
        self.telegram_token: str = telegram_token
        self.chat_id: str = chat_id
        self.db_path: str = db_path
        self.category: str | None = category
        self.experience: str | None = experience
        self.city: str | None = city
        self.remote: bool = remote
        self.relocation: bool = relocation
        self.no_exp: bool = no_exp

        self.base_url = self.BASE_URL_NO_EXP if no_exp else self.BASE_URL
        self.full_url: str = self._construct_full_url()
        self._initialize_database()
        self._create_indexes()

    def _initialize_database(self) -> None:
        """Creates a database table if it doesn't exist."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
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
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_title_date_company_category ON dou_jobs (title, date, company, category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON dou_jobs (category)")
            conn.commit()

    def _construct_full_url(self) -> str:
        """Constructs the full URL for job scraping based on filters."""
        if sum(map(bool, [self.remote, self.relocation, self.city])) > 1:
            raise ValueError("Only one of 'remote', 'relocation', or 'city' can be specified.")

        filters: list = []
        if self.remote and not self.no_exp:
            filters.append("remote")
        if self.relocation and not self.no_exp:
            filters.append("relocation")
        if self.city:
            filters.append(f"city={self.city}")
        if self.category and not self.no_exp:
            filters.append(f"category={self.category}")
        if self.experience and not self.no_exp:
            filters.append(f"exp={self.experience}")

        return self.base_url + "?" + "&".join(filters)

    def _clean_text_for_telegram(self, text: str) -> str:
        """Cleans text for Telegram compatibility."""
        return text.replace("`", "'").replace("’", "'").strip()

    def get_list_jobs(self) -> List[Dict[str, Optional[str]]]:
        """Scrapes job offers and returns a list of dictionaries."""
        job_offers: list = []
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
                job: Dict[str, str | None] | None = self._extract_job_data(job_card)
                if job:
                    job_offers.append(job)

        except requests.RequestException as err:
            logging.error("Error retrieving data from the site: %s", err)

        return job_offers[::-1]

    def _extract_job_data(self, job_card: Tag) -> Optional[Dict[str, Optional[str]]]:
        """Extracts job data from a single job card."""
        try:
            date: str = job_card.select_one("div.date").text.strip()
            title_tag: Tag | None = job_card.select_one("div.title > a")
            company_tag: Tag | None = job_card.select_one("div.title > strong")
            salary_tag: Tag | None = job_card.select_one("span.salary")
            cities_tag: Tag | None = job_card.select_one("span.cities")
            short_info_tag: Tag | None = job_card.select_one("div.sh-info")
            category_job: str = self.category if self.category else "No category"
            experience_job: str = self.experience if self.experience else "No experience"

            return {
                "date": date,
                "title": title_tag.text.strip() if title_tag else None,
                "link": title_tag.get("href") if title_tag else None,
                "company": company_tag.text.strip() if company_tag else None,
                "salary": salary_tag.text.strip() if salary_tag else None,
                "cities": cities_tag.text.strip() if cities_tag else None,
                "sh_info": short_info_tag.text.strip() if short_info_tag else None,
                "category": category_job,
                "experience": experience_job,
            }
        except AttributeError as err:
            logging.error("Error extracting job data: %s", err)
            return None

    def _normalize_job_data(self, job: Dict[str, str | None]) -> Dict[str, str | None]:
        """Normalizes job data before adding it to the database."""
        job['title'] = job['title'].strip().lower() if job['title'] else None
        job['company'] = job['company'].strip().lower() if job['company'] else None
        job['category'] = job['category'].strip().lower() if job['category'] else None
        job['date'] = job['date'].strip() if job['date'] else None
        return job

    def check_and_add_jobs(self) -> List[Dict[str, Optional[str]]]:
        """Checks for new jobs and adds them to the database."""
        new_jobs: list = []
        job_offers: List[Dict[str, str | None]] = self.get_list_jobs()

        with sqlite3.connect(self.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            for job in job_offers:
                try:
                    cursor.execute("BEGIN")
                    job = self._normalize_job_data(job)

                    cursor.execute("""
                        SELECT 1 FROM dou_jobs WHERE title = :title AND date = :date AND company = :company AND category = :category
                    """, job)

                    if not cursor.fetchone():
                        try:
                            cursor.execute("""
                                INSERT INTO dou_jobs (date, title, link, company, salary, cities, sh_info, category, experience)
                                VALUES (:date, :title, :link, :company, :salary, :cities, :sh_info, :category, :experience)
                            """, job)
                            new_jobs.append(job)
                            self._send_job_to_telegram(job)
                        except sqlite3.IntegrityError as e:
                            logging.warning("Duplicate job entry detected: %s - %s - %s", job['title'], job['company'], e)
                        except sqlite3.Error as e:
                            logging.error("Error inserting job into database: %s - %s", job, e)

                    conn.commit()
                except Exception as e:  # Catch all exceptions
                    conn.rollback()
                    logging.error("An unexpected error occurred: %s", e)

        return new_jobs

    def _create_telegram_message(self, job: Dict[str, Optional[str]]) -> str:
        """Creates a formatted message for Telegram."""
        experience: str = self.experience.replace("+", " ") if self.experience else "No experience"
        return (
            f"*Date:* {job['date']}\n"
            f"[{job['title']}]({job['link']}) *{job['company']}*\n"
            f"*Experienced:* {experience} years\n"
            f"*Category:* {job['category']}\n"
            f"*Salary:* {job['salary'] or 'N/A'}\n"
            f"*Cities:* {job['cities']}\n"
            f"*Info:* {self._clean_text_for_telegram(job['sh_info'] or 'N/A')}"
        )

    def _send_job_to_telegram(self, job: Dict[str, Optional[str]]) -> None:
        """Sends a job offer to a Telegram chat."""
        message: str = self._create_telegram_message(job)
        payload: Dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        while True:
            try:
                response: requests.Response = requests.post(
                    self.TELEGRAM_API_URL.format(self.telegram_token),
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

    def _get_retry_time(self, response: requests.Response) -> int:
        """Extracts retry time from the Telegram API response."""
        try:
            return int(response.json().get("parameters", {}).get("retry_after", 5))
        except (ValueError, KeyError):
            return 5

    def list_all_jobs_in_db(self) -> List[Dict[str, str]]:
        """Returns a list of all jobs in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("SELECT * FROM dou_jobs")
            return cursor.fetchall()
    def list_no_category_jobs_in_db(self) -> List[Dict[str, str]]:
        """Returns a list of jobs in the database where category is 'No category'."""
        with sqlite3.connect(self.db_path) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute("SELECT * FROM dou_jobs WHERE category = ?", ("No category",))
            return cursor.fetchall()

if __name__ == "__main__":
    load_dotenv(dotenv_path='.env')

    TOKEN: str | None = os.getenv("TELEGRAM_TOKEN")
    NO_EXP_TOKEN: str | None = os.getenv("NO_EXP_TELEGRAM_TOKEN")
    CHAT_ID: str | None = os.getenv("CHAT_ID")
    NO_EXP_CHAT_ID: str | None = os.getenv("NO_EXP_CHAT_ID")
    DB_PATH: str | None = os.getenv("DB_PATH")

    # Check new jobs for no experience level on DOU
    dou_scraper = DouJobScraper(
        telegram_token=NO_EXP_TOKEN,
        chat_id=NO_EXP_CHAT_ID,
        db_path=DB_PATH,
        no_exp=True,
    )
    dou_scraper.check_and_add_jobs()

    # # Check new jobs for experience level 0-1 years on DOU
    # dou_scraper_0_1 = DouJobScraper(
    #     telegram_token=TOKEN,
    #     chat_id=CHAT_ID,
    #     db_path=DB_PATH,
    #     category="Python",
    #     experience="0-1",
    # )
    # dou_scraper_0_1.check_and_add_jobs()

    # # Check new jobs for experience level 1-3 years on DOU
    # dou_scraper_1_3 = DouJobScraper(
    #     telegram_token=TOKEN,
    #     chat_id=CHAT_ID,
    #     db_path=DB_PATH,
    #     category="Python",
    #     experience="1-3",
    # )
    # dou_scraper_1_3.check_and_add_jobs()

    # for job_dou in dou_scraper.list_jobs_in_db():
    #     print("ID:", job_dou[0], "\n", "Data:", job_dou[1], "\n", job_dou[2], job_dou[4])
    #     print("Salary:", job_dou[5], "\n", "Place:", job_dou[6])
    #     print(job_dou[7])
    #     print(job_dou[8], "\n" + job_dou[9])
    #     print()

    job_title_on_site = []
    job_list_on_site = dou_scraper.get_list_jobs()
    for job_on_site in job_list_on_site:
        job_title_on_site.append(job_on_site["title"])

    job_title_in_db = []
    job_list_in_db = dou_scraper.list_no_category_jobs_in_db()
    for job_db in job_list_in_db:
        job_title_in_db.append(job_db[2])

    missing_jobs = list(set(job_title_on_site) - set(job_title_in_db))
    print(len(job_title_on_site))
    print(len(job_title_in_db))
    print(missing_jobs)
    print(job_title_in_db)
