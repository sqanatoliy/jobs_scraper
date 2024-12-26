
"""
This script checks for new job postings on different websites 
and sends them to a specified Telegram chat.

Environment Variables:
- TELEGRAM_TOKEN: The token for the Telegram bot.
- CHAT_ID: The chat ID where the job postings will be sent.

Functions:
- send_new_jobs_to_telegram: Sends new job postings to the specified Telegram chat.

Usage:
1. Ensure that the .env file contains the TELEGRAM_TOKEN and CHAT_ID.
2. Run the script to check for new job postings and send them to the specified Telegram chat.
"""
import os
from dotenv import load_dotenv


from scrapers.gb_lg_jobs_scraper import GlobalLogicJobScraper
from scrapers.dou_jobs_scraper import DouJobScraper

load_dotenv()

TOKEN: str | None = os.getenv("TELEGRAM_TOKEN")
CHAT_ID: str | None = os.getenv("CHAT_ID")

# Check new jobs for experience level 0-1 years on GlobalLogic
GlobalLogicJobScraper(
    csv_file="./csv_files/gl_logic_0_1.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="0-1+years",
    locations="ukraine",
).send_new_jobs_to_telegram()


# Check new jobs for experience level 1-3 years on GlobalLogic
GlobalLogicJobScraper(
    csv_file="./csv_files/gl_logic_1_3.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="1-3+years",
    locations="ukraine",
).send_new_jobs_to_telegram()


# Check new jobs for experience level 0-1 years on DOU
DouJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    csv_file="./csv_files/dou_0_1.csv",
    category="Python",
    experience="0-1",
).send_new_jobs_to_telegram()

# Check new jobs for experience level 1-3 years on DOU
DouJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    csv_file="./csv_files/dou_1_3.csv",
    category="Python",
    experience="1-3",
).send_new_jobs_to_telegram()
