"""
This module contains the `GlobalLogicJobScraper` class, which allows for scraping job offers
from GlobalLogic's career page based on various parameters and saving them in a CSV file.
The module includes functions to retrieve job offers and to check for and add new job listings.

Dependencies:
    - requests
    - BeautifulSoup (from bs4)
    - csv
    - re
    - logging
"""

import csv
import os
import re
import logging
from typing import Any, List, Dict, Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class GlobalLogicJobScraper:
    """
    A scraper for retrieving job offers from GlobalLogic's career page based on specified criteria.

    Attributes:
        csv_file (str): Path to the CSV file where job offers will be saved.
        keywords (str): Keywords to filter job offers.
        experience (str): Experience level to filter job offers.
        locations (str): Location to filter job offers.
        freelance (bool): Filter for freelance job offers.
        remote (bool): Filter for remote job offers.
        hybrid (bool): Filter for hybrid job offers.
        on_site (bool): Filter for on-site job offers.
    """

    def __init__(
        self,
        csv_file: str,
        telegram_token: str,
        chat_id: str,
        keywords: str = "",
        experience: str = "",
        locations: str = "",
        freelance: Optional[bool] = None,
        remote: Optional[bool] = None,
        hybrid: Optional[bool] = None,
        on_site: Optional[bool] = None,
    ) -> None:
        """
        Initializes the GlobalLogicJobScraper with search parameters for job filtering.

        Args:
            csv_file (str): Path to the CSV file to save job offers.
            keywords (str): Keywords for job search.
            experience (str): Experience level filter.
            locations (str): Location filter.
            freelance (bool): Filter for freelance jobs.
            remote (bool): Filter for remote jobs.
            hybrid (bool): Filter for hybrid jobs.
            on_site (bool): Filter for on-site jobs.
        """
        self.base_url = "https://www.globallogic.com/career-search-page/?"
        self.csv_file: str = csv_file
        self.telegram_token: str = telegram_token
        self.chat_id: str = chat_id
        self.keywords: str = keywords
        self.experience: str = experience
        self.locations: str = locations
        self.freelance: bool | None = freelance
        self.remote: bool | None = remote
        self.hybrid: bool | None = hybrid
        self.on_site: bool | None = on_site
        self.full_url: str = self._construct_full_url()
        # Ensure the CSV directory exists
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)

    def _construct_full_url(self) -> str:
        """
        Builds the full URL for job scraping based on initialized filters.
        
        Returns:
            str: The constructed full URL with specified filters.
        """
        url: str = (
            f"{self.base_url}keywords={self.keywords}&experience={self.experience}&locations={self.locations}&c="
        )
        if self.freelance:
            url += "&freelance=yes"

        work_models: list = []
        if self.remote:
            work_models.append("Remote")
        if self.hybrid:
            work_models.append("Hybrid")
        if self.on_site:
            work_models.append("On-site")
        if work_models:
            url += "&workmodel=" + ",".join(work_models)

        return url

    def get_list_jobs(self) -> List[Dict[str, Optional[str]]]:
        """
        Retrieves job offers by scraping the GlobalLogic career page based on initialized filters.

        Returns:
            list: A list of dictionaries where each dictionary represents a job offer with:
                - "title" (str): Job title.
                - "link" (str): URL to the job listing.
                - "requirements" (str or None): Job requirements or None if unavailable.
        """
        job_offers_list:list = []

        try:
            response: requests.Response = requests.get(self.full_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.select("div.career-pagelink")

            for job_card in job_cards:
                title_element = job_card.select_one("p > a")
                if title_element:
                    title = title_element.text.strip()
                    link: str | List[str] | None = title_element.get("href")

                    requirements_element = job_card.select_one("p.id-num")
                    requirements: str | None = (
                        re.sub(r"\s+", " ", requirements_element.text.strip())
                        if requirements_element
                        else None
                    )

                    job_offers_list.append(
                        {"title": title, "link": link, "requirements": requirements}
                    )

        except requests.RequestException as e:
            logging.error("Error retrieving data from the site: %s", e)

        return job_offers_list

    def check_and_add_jobs(self) -> List[Dict[str, Optional[str]]]:
        """
        Checks if each job offer already exists in the CSV file based on the job title.
        If a job offer is not found, it is added to the file.

        Args:
            job_offers_lst (list): A list of dictionaries containing job offers to check and add.

        Returns:
            list: A list of new job offers (dictionaries) that were added to the CSV file.
        """

        job_offers_lst: List[Dict[str, str | None]] = self.get_list_jobs()
        existing_titles = set()
        new_jobs_lst: list = []

        try:
            with open(self.csv_file, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames and "title" in reader.fieldnames:
                    existing_titles = {row["title"] for row in reader}
        except FileNotFoundError:
            pass

        with open(self.csv_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["title", "link", "requirements"])
            if file.tell() == 0:
                writer.writeheader()

            for job in job_offers_lst:
                if job["title"] not in existing_titles:
                    writer.writerow(job)
                    new_jobs_lst.append(job)

        return new_jobs_lst

    def send_new_jobs_to_telegram(self) -> None:
        """
        Send new job offers to Telegram chat.

        Args:
            new_jobs (list): List of vacancies for sending.
        """
        base_url: str = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

        new_jobs: List[Dict[str, str | None]] = self.check_and_add_jobs()

        # If there are no new jobs, log a message and return
        if not new_jobs:
            logging.info("No new jobs to send to Telegram.")
            return

        for job in new_jobs:
            message: str = (
                "GLOBAL LOGIC PRESENT \n"
                f"[{job['title']}]({job['link']})\n"
                f"Requirements: {job['requirements'] or 'N/A'}"
            )
            payload: dict[str | Any] = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
            try:
                response: requests.Response = requests.post(base_url, data=payload, timeout=10)
                response.raise_for_status()
                logging.info("Job sent to Telegram successfully!")
            except requests.RequestException as e:
                logging.error("Failed to send job to Telegram: %s", e)

if __name__ == "__main__":
    TOKEN: str | None = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID: str | None = os.getenv("CHAT_ID")
    scraper = GlobalLogicJobScraper(
        csv_file="./csv_files/gl_logic_0_1.csv",
        telegram_token=TOKEN,
        chat_id=CHAT_ID,
        keywords="python",
        experience="0-1+years",
        locations="ukraine",
    )
    scraper.send_new_jobs_to_telegram()
