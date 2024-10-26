"""
This module contains the `GlobalLogicJobScraper` class, which allows for scraping job offers
from GlobalLogic's career page based on various parameters and saving them in a CSV file.
The module includes functions to retrieve job offers and to check for and add new job listings.

Dependencies:
    - requests
    - BeautifulSoup (from bs4)
    - csv
    - re
"""

import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


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
        csv_file,
        telegram_token,
        chat_id,
        keywords="",
        experience="",
        locations="",
        freelance=None,
        remote=None,
        hybrid=None,
        on_site=None,
    ):
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
        self.csv_file = csv_file
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.keywords = keywords
        self.experience = experience
        self.locations = locations
        self.freelance = freelance
        self.remote = remote
        self.hybrid = hybrid
        self.on_site = on_site
        self.full_url = self._construct_full_url()

    def _construct_full_url(self) -> str:
        """
        Builds the full URL for job scraping based on initialized filters.
        
        Returns:
            str: The constructed full URL with specified filters.
        """
        url = (
            self.base_url
            + f"keywords={self.keywords}&experience={self.experience}&locations={self.locations}&c="
        )
        if self.freelance:
            url += "&freelance=yes"

        work_models = []
        if self.remote:
            work_models.append("Remote")
        if self.hybrid:
            work_models.append("Hybrid")
        if self.on_site:
            work_models.append("On-site")
        if work_models:
            url += "&workmodel=" + ",".join(work_models)

        return url

    def get_list_jobs(self) -> list:
        """
        Retrieves job offers by scraping the GlobalLogic career page based on initialized filters.

        Returns:
            list: A list of dictionaries where each dictionary represents a job offer with:
                - "title" (str): Job title.
                - "link" (str): URL to the job listing.
                - "requirements" (str or None): Job requirements or None if unavailable.
        """

        job_offers_list = []

        # Scraping job offers from the constructed URL
        try:
            response = requests.get(self.full_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.select("div.career-pagelink")

            for job_card in job_cards:
                title_element = job_card.select_one("p > a")
                if title_element:
                    title = title_element.text.strip()
                    link = title_element.get("href")

                    requirements_element = job_card.select_one("p.id-num")
                    requirements = (
                        re.sub(r"\s+", " ", requirements_element.text.strip())
                        if requirements_element
                        else None
                    )

                    job_offers_list.append(
                        {"title": title, "link": link, "requirements": requirements}
                    )

        except requests.RequestException as e:
            print("Error retrieving data from the site:", e)

        return job_offers_list

    def check_and_add_jobs(self, job_offers_lst: list) -> list:
        """
        Checks if each job offer already exists in the CSV file based on the job title.
        If a job offer is not found, it is added to the file.

        Args:
            job_offers_lst (list): A list of dictionaries containing job offers to check and add.

        Returns:
            list: A list of new job offers (dictionaries) that were added to the CSV file.
        """
        existing_titles = set()
        new_jobs_lst = []

        # Read existing job titles from CSV file
        try:
            with open(self.csv_file, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames and "title" in reader.fieldnames:
                    existing_titles = {row["title"] for row in reader}
        except FileNotFoundError:
            # File will be created if not found
            pass

        # Check for new jobs and add them to the CSV file if needed
        with open(self.csv_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["title", "link", "requirements"])
            if file.tell() == 0:
                writer.writeheader()  # Write header if file is empty

            for job in job_offers_lst:
                if job["title"] not in existing_titles:
                    writer.writerow(job)
                    new_jobs_lst.append(job)

        return new_jobs_lst

    def send_new_jobs_to_telegram(self, new_jobs: list) -> None:
        """
        Send new job offers to  Telegram-chat.

        Args:
            new_jobs (list): List of vacancies for sending.
        """
        base_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

        for job in new_jobs:
            message = (
                "GLOBAL LOGIC PRESENT \n"
                f"[{job['title']}]({job['link']})\n"
                f"Requirements: {job['requirements'] or 'N/A'}"
            )
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(base_url, data=payload)

            if response.status_code == 200:
                print("Job sent to Telegram successfully!")
            else:
                print("Failed to send job to Telegram:", response.json().get("description"))


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("telegram_token")
    CHAT = os.getenv("chat_id")

    # Example usage for job offers with 0-1 years experience
    scraper_0_1 = GlobalLogicJobScraper(
        "gl_logic_0_1.csv",
        telegram_token=TOKEN,
        chat_id=CHAT,
        keywords="python",
        experience="0-1+years",
        locations="ukraine",
    )
    job_offers_0_1 = scraper_0_1.get_list_jobs()
    new_jobs_0_1 = scraper_0_1.check_and_add_jobs(job_offers_0_1)

    # Example usage for job offers with 1-3 years experience
    scraper_1_3 = GlobalLogicJobScraper(
        "gl_logic_1_3.csv",
        telegram_token=TOKEN,
        chat_id=CHAT,
        keywords="python",
        experience="1-3+years",
        locations="ukraine",
    )
    job_offers_1_3 = scraper_1_3.get_list_jobs()
    new_jobs_1_3 = scraper_1_3.check_and_add_jobs(job_offers_1_3)

    # Output new job offers added to the file
    if new_jobs_0_1:
        print()
        print("Constructed URL for scraping: ", scraper_0_1.full_url)
        print("New job offers added to the file:", new_jobs_0_1)
        scraper_0_1.send_new_jobs_to_telegram(new_jobs_0_1)
    else:
        print()
        print("Constructed URL for scraping: ", scraper_0_1.full_url)
        print("No new job offers available.")

    if new_jobs_1_3:
        print()
        print("Constructed URL for scraping: ", scraper_1_3.full_url)
        print("New job offers added to the file:", new_jobs_1_3)
        scraper_1_3.send_new_jobs_to_telegram(new_jobs_1_3)
    else:
        print()
        print("Constructed URL for scraping: ", scraper_1_3.full_url)
        print("No new job offers available.")
