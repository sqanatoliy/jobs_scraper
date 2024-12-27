"""
This module contains the `DouJobScraper` class, which allows for scraping job offers
from dou.ua Jobs page based on various parameters and saving them in a CSV file.

Dependencies:
    - requests
    - BeautifulSoup (from bs4)
    - csv
    - re
    - logging
"""

import os
import csv
import logging
import time
from typing import Any, List, Dict, Optional

import requests
from bs4 import BeautifulSoup, Tag, ResultSet

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class DouJobScraper:
    """
    A scraper for retrieving job offers from Dou Jobs page based on specified criteria.

    Attributes:
        telegram_token (str): Telegram bot token for notifications.
        chat_id (str): Telegram chat ID.
        csv_file (str): Path to the CSV file where job offers will be saved.
        category (str): Job category filter.
        experience (str): Experience level filter.
        city (str): Location filter.
        remote (bool): Filter for remote jobs.
        relocation (bool): Filter for relocation jobs.
        no_exp (bool): If True, scrapes jobs from the "Без досвіду" page.
    """

    BASE_URL = "https://jobs.dou.ua/vacancies/"
    BASE_URL_NO_EXP = "https://jobs.dou.ua/first-job/"

    def __init__(
        self,
        telegram_token: str,
        chat_id: str,
        csv_file: str,
        category: Optional[str] = None,
        experience: Optional[str] = None,
        city: Optional[str] = None,
        remote: bool = False,
        relocation: bool = False,
        no_exp: bool = False,
    ) -> None:
        self.telegram_token: str = telegram_token
        self.chat_id: str = chat_id
        self.csv_file: str = csv_file
        self.category: str | None = category
        self.experience: str | None = experience
        self.city: str | None = city
        self.remote: bool = remote
        self.relocation: bool = relocation
        self.no_exp: bool = no_exp

        self.base_url = self.BASE_URL_NO_EXP if no_exp else self.BASE_URL
        self.full_url: str = self._construct_full_url()

        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)

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
        return text.replace("`", "'").replace("’", "'").replace("'", "&#39;").strip()

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

        except requests.RequestException as e:
            logging.error("Error retrieving data from the site: %s", e)

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

            return {
                "date": date,
                "title": title_tag.text.strip() if title_tag else None,
                "link": title_tag.get("href") if title_tag else None,
                "company": company_tag.text.strip() if company_tag else None,
                "salary": salary_tag.text.strip() if salary_tag else None,
                "cities": cities_tag.text.strip() if cities_tag else None,
                "sh_info": short_info_tag.text.strip() if short_info_tag else None,
            }
        except AttributeError:
            return None

    def check_and_add_jobs(self) -> List[Dict[str, Optional[str]]]:
        """Checks for new jobs and adds them to the CSV if not present."""
        new_jobs: list = []
        existing_jobs: set = self._load_existing_jobs()

        with open(self.csv_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["date", "title", "link", "company", "salary", "cities", "sh_info"])
            if file.tell() == 0:
                writer.writeheader()

            for job in self.get_list_jobs():
                job_id: tuple[str | None, str | None, str | None] = (job["title"], job["date"], job["company"])
                if job_id not in existing_jobs:
                    self._send_job_to_telegram(job)
                    writer.writerow(job)
                    new_jobs.append(job)

        return new_jobs

    def _load_existing_jobs(self) -> set:
        """Loads existing jobs from the CSV file."""
        try:
            with open(self.csv_file, mode="r", encoding="utf-8") as file:
                return {
                    (row["title"], row["date"], row["company"])
                    for row in csv.DictReader(file)
                }
        except FileNotFoundError:
            return set()

    def _send_job_to_telegram(self, job: Dict[str, Optional[str]]) -> None:
        """Sends a job offer to a Telegram chat."""
        experience: str = self.experience.replace("+", " ") if self.experience else "No experience"
        message: str = (
            f"*Date:* {job['date']}\n"
            f"[{job['title']}]({job['link']}) *{job['company']}*\n"
            f"*Experienced:* {experience} years\n"
            f"*Salary:* {job['salary'] or 'N/A'}\n"
            f"*Cities:* {job['cities']}\n"
            f"*Info:* {self._clean_text_for_telegram(job['sh_info'] or 'N/A')}"
        )
        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        while True:
            try:
                response: requests.Response = requests.post(
                    f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                    data=payload,
                    timeout=60,
                )
                if response.status_code == 429:
                    try:
                        # Отримуємо час очікування з відповіді API, якщо доступно
                        retry_time = int(response.json().get("retry_after", 5))  # За замовчуванням 5 секунд
                    except ValueError:
                        # Якщо відповідь не JSON або параметр не знайдено
                        retry_time = 5

                    logging.warning(
                        "Telegram API rate limit exceeded. Waiting and retrying after %s seconds.", retry_time
                    )
                    time.sleep(retry_time)
                    continue
                response.raise_for_status()
                logging.info("Job sent to Telegram successfully.")
                break
            except requests.RequestException as e:
                logging.error("Failed to send job to Telegram: %s", e)
                time.sleep(10)