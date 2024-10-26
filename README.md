# GlobalLogic Job Scraper

This project provides a class `GlobalLogicJobScraper` for scraping job offers from GlobalLogic's career page, saving them to a CSV file, and optionally sending new job postings to a Telegram channel or group.

## Features
- Scrapes job offers from [GlobalLogic's career page](https://www.globallogic.com/career-search-page/).
- Filters job offers based on keywords, experience, location, and work type (freelance, remote, hybrid, on-site).
- Saves new job offers to a CSV file and prevents duplicates.
- Sends new job offers to a specified Telegram chat.

## Requirements

- Python 3.11+
- Install dependencies from `requirements.txt`:

  ```bash
  pip install -r requirements.txt
  ```

## Dependencies
	•	requests - For making HTTP requests to the GlobalLogic career page and Telegram API.
	•	beautifulsoup4 - For parsing and extracting data from the HTML content.
	•	python-dotenv - For managing environment variables for security.
	•	csv and re - For handling CSV file operations and processing text data.

## Installation
	1.	Clone the repository:

        ```bash
        git clone ...
        ```
    2.	Install the required dependencies:

        ```bash
        pip install -r requirements.txt
        ```

    3.	Set up your .env file with the following variables:

        ```yml
        telegram_token=YOUR_TELEGRAM_BOT_TOKEN
        chat_id=YOUR_CHAT_ID
        ```

        Replace YOUR_TELEGRAM_BOT_TOKEN and YOUR_CHAT_ID with the token for your Telegram bot 
        and the chat ID of your Telegram group or channel.

## Usage

### Example Script

The following example demonstrates how to use the GlobalLogicJobScraper to scrape job offers for Python developers with experience levels of 0-1 and 1-3 years, store them in separate CSV files, and send new jobs to a Telegram chat.

```python
from globallogic_scraper import GlobalLogicJobScraper
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("telegram_token")
CHAT_ID = os.getenv("chat_id")

scraper_0_1 = GlobalLogicJobScraper(
    csv_file="gl_logic_0_1.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="0-1+years",
    locations="ukraine",
)
job_offers_0_1 = scraper_0_1.get_list_jobs()
new_jobs_0_1 = scraper_0_1.check_and_add_jobs(job_offers_0_1)
if new_jobs_0_1:
    scraper_0_1.send_new_jobs_to_telegram(new_jobs_0_1)

# Repeat for experience level 1-3 years
scraper_1_3 = GlobalLogicJobScraper(
    csv_file="gl_logic_1_3.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="1-3+years",
    locations="ukraine",
)
job_offers_1_3 = scraper_1_3.get_list_jobs()
new_jobs_1_3 = scraper_1_3.check_and_add_jobs(job_offers_1_3)
if new_jobs_1_3:
    scraper_1_3.send_new_jobs_to_telegram(new_jobs_1_3)
```

### Running the Script
Run the script from the command line:
```bash
python your_script_name.py
```

### Class GlobalLogicJobScraper
**Initialization**
```python
scraper = GlobalLogicJobScraper(
    csv_file="jobs.csv",
    telegram_token="YOUR_TELEGRAM_TOKEN",
    chat_id="YOUR_CHAT_ID",
    keywords="python",
    experience="1-3+years",
    locations="ukraine",
    freelance=False,
    remote=True,
    hybrid=False,
    on_site=False,
)
```

	•	csv_file (str): Path to the CSV file where job data will be saved.
	•	telegram_token (str): Telegram bot token.
	•	chat_id (str): Telegram chat ID.
	•	keywords, experience, locations (str): Job search filters.
	•	freelance, remote, hybrid, on_site (bool): Additional filters for work models.

**Methods**
	•	get_list_jobs(): Scrapes job offers from GlobalLogic’s page.
	•	check_and_add_jobs(job_offers_lst: list): Checks for new job offers and adds them to the CSV file.
	•	send_new_jobs_to_telegram(new_jobs: list): Sends new job offers to the specified Telegram chat.

## License
This project is licensed under the MIT License.