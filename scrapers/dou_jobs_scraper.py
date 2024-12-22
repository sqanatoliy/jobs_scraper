"""
This module contains the `DouJobScraper` class, which allows for scraping job offers
from dou.ua Jobs page based on various parameters and saving them in a CSV file.
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
import time
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DouJobScraper:
    """
    A scraper for retrieving job offers from Dou Jobs page based on specified criteria.

    Attributes:
        csv_file (str): Path to the CSV file where job offers will be saved.
        category (str): category to filter job offers.
        experience (str): Experience level to filter job offers.
        city (str): Location to filter job offers.
        remote (bool): Filter for remote job offers.
        relocation (bool): Filter for relocation job offers.
    """

    def __init__(
        self,
        telegram_token: str,
        chat_id: str,
        csv_file: str,
        category: str,
        experience: str = None,
        city: str = None,
        remote: bool = False,
        relocation: bool = False,
    ):
        """
        Initializes the DouJobScraper with search parameters for job filtering.

        Args:
            csv_file (str): Path to the CSV file to save job offers.
            category (str): category for job search: Python, JavaScript, etc.
            experience (str): Experience level filter: 0-1, 1-3, 3-5, 5plus.
            city (str): Location filter: Київ, Львів, Одеса etc.
            remote (bool): Filter for remote jobs: remote.
            relocation (bool): Filter for relocation jobs: relocation.
        """
        self.base_url = "https://jobs.dou.ua/vacancies/?"
        self.csv_file = csv_file
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.category = category   # Python, JavaScript, etc.
        self.experience = experience  # 0-1, 1-3, 3-5, 5plus
        self.city = city   # Київ, Львів, Одеса etc.
        self.remote = remote   # remote
        self.relocation = relocation   # relocation
        self.full_url = self._construct_full_url()
        # Ensure the CSV directory exists
        if not os.path.exists(os.path.dirname(self.csv_file)):
            os.makedirs(os.path.dirname(self.csv_file))

    def _construct_full_url(self) -> str:
        """
        Builds the full URL for job scraping based on initialized filters.
        Ensures only one of `remote`, `relocation`, or `city` is specified.
        
        Returns:
            str: The constructed full URL with specified filters.
        
        Raises:
            ValueError: If more than one of `remote`, `relocation`, or `city` is specified.
        """
        # Ensure only one of 'remote', 'relocation', or 'city' is specified
        filters: list[bool | str | None] = [self.remote, self.relocation, self.city]
        if sum(map(bool, filters)) > 1:
            raise ValueError("Only one of 'remote', 'relocation', or 'city' can be specified at a time.")
        
        url: list[str] = self.base_url

        if self.remote:
            url += "remote&"
        if self.relocation:
            url += "relocation&"
        if self.city:
            url += f"city={self.city}&"
        if self.category:
            url += f"category={self.category}&"
        if self.experience:
            url += f"exp={self.experience}"
        if url[-1] == "&":
            url = url[:-1]
        return url

    def get_list_jobs(self) -> List[Dict[str, Optional[str]]]:
        """
        Retrieves job offers by scraping the Dou Job page based on initialized filters.

        Returns:
            list: A list of dictionaries where each dictionary represents a job offer with:
                - "date" (str): Job publication date.
                - "title" (str): Job title.
                - "link" (str): URL to the job listing.
                - "company" (str): Company name.
                - "salary" (str): Salary or None if unavailable.
                - "cities" (str): Job location.
                - "sh_info" (str): Short information about the job.
        """
        job_offers_list = []

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(self.full_url, headers=headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.select("ul > li.l-vacancy")

            for job_card in job_cards:
                date_posted = job_card.select_one("div.date").text.strip()
                title_element = job_card.select_one("div.title")
                if title_element:
                    title = title_element.select_one("a").text.strip()
                    link = title_element.select_one("a").get("href")
                    company_element = title_element.select_one("strong")
                    company = (
                        re.sub(r"\s+", " ", company_element.text.strip())
                        if company_element
                        else None
                    )
                    salary_element = title_element.select_one("span.salary")
                    if salary_element:
                        salary = salary_element.text.strip()
                    else:
                        salary = None
                    cities = title_element.select_one("span.cities").text.strip()

                    short_info_element = job_card.select_one("div.sh-info")
                    short_info = (
                        re.sub(r"\s+", " ", short_info_element.text.strip())
                        if short_info_element
                        else None
                    )

                    job_offers_list.append(
                        {"date": date_posted, "title": title, "link": link, "company": company, "salary": salary, "cities": cities, "sh_info": short_info}
                    )

        except requests.RequestException as e:
            logging.error("Error retrieving data from the site: %s", e)

        return job_offers_list

    def check_and_add_jobs(self, job_offers_lst: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
        """
        Checks if each job offer already exists in the CSV file based on title, date, and company.
        If a job offer is not found, it is added to the file.

        Args:
            job_offers_lst (list): A list of dictionaries containing job offers to check and add.

        Returns:
            list: A list of new job offers (dictionaries) that were added to the CSV file.
        """
        existing_jobs = set()  # Stores unique identifiers (title, date, company) of existing jobs
        new_jobs_lst = []

        # Load existing jobs from the CSV file
        try:
            with open(self.csv_file, mode="r", newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                if reader.fieldnames and {"title", "date", "company"}.issubset(reader.fieldnames):
                    existing_jobs = {(row["title"], row["date"], row["company"]) for row in reader}
        except FileNotFoundError:
            pass

        # Open the CSV file in append mode and add new jobs
        with open(self.csv_file, mode="a", newline="", encoding="utf-8") as file:
            # Ensure the CSV file has headers for all fields
            writer = csv.DictWriter(file, fieldnames=["date", "title", "link", "company", "salary", "cities", "sh_info"])
            if file.tell() == 0:  # Write headers only if the file is empty
                writer.writeheader()

            for job in job_offers_lst:
                # Create a unique identifier for the job (title, date, company)
                job_identifier = (job["title"], job["date"], job["company"])

                # Add the job to the CSV file if it's not already present
                if job_identifier not in existing_jobs:
                    writer.writerow(job)  # Save all job fields
                    new_jobs_lst.append(job)

        return new_jobs_lst

    def send_new_jobs_to_telegram(self, new_jobs: List[Dict[str, Optional[str]]]) -> None:
        """
        Send new job offers to Telegram chat.

        Args:
            new_jobs (list): List of vacancies for sending.
        """
        base_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

        for job in new_jobs:
            message = (
                "DOU PRESENT \n"
                f"Date: {job['date']}\n"
                f"[{job['title']}]({job['link']}) {job['company'] or 'N/A'} \n"
                f"Experience: {self.experience}\n"
                f"Salary: {job['salary'] or 'N/A'}\n"
                f"Cities: {job['cities']}\n"
                f"Short Info: {job['sh_info'] or 'N/A'}"
            )
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
            while True:
                try:
                    response = requests.post(base_url, data=payload, timeout=30)
                    if response.status_code == 429:  # Too Many Requests
                        retry_after = int(response.json().get("parameters", {}).get("retry_after", 1))
                        logging.warning("Rate limit exceeded. Retrying after %d seconds...", retry_after)
                        time.sleep(retry_after)
                        continue  # Retry sending the same message
                    response.raise_for_status()
                    logging.info("Job sent to Telegram successfully!")
                    time.sleep(1)  # Delay to avoid rate limiting
                    break  # Move to the next message
                except requests.RequestException as e:
                    logging.error("Failed to send job to Telegram: %s", e)
                    time.sleep(5)

