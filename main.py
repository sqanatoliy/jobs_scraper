
"""
This script checks for new job postings on different websites 
and sends them to a specified Telegram chat.

Environment Variables:
- TELEGRAM_TOKEN: The token for the Telegram bot.
- CHAT_ID: The chat ID where the job postings will be sent.

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
NO_EXP_TOKEN: str | None = os.getenv("NO_EXP_TELEGRAM_TOKEN")
CHAT_ID: str | None = os.getenv("CHAT_ID")
NO_EXP_CHAT_ID: str | None = os.getenv("NO_EXP_CHAT_ID")
DB_PATH: str | None = os.getenv("DB_PATH")

# Check new jobs for experience level 0-1 years on GlobalLogic
GlobalLogicJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    db_path=DB_PATH,
    keywords="python",
    experience="0-1+years",
    locations="ukraine",
).check_and_add_jobs()

# Check new jobs for experience level 1-3 years on GlobalLogic
GlobalLogicJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    db_path=DB_PATH,
    keywords="python",
    experience="1-3+years",
    locations="ukraine",
).check_and_add_jobs()


# Check new jobs for experience level 0-1 years on DOU
DouJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    db_path=DB_PATH,
    category="Python",
    experience="0-1",
).check_and_add_jobs()

# Check new jobs for experience level 1-3 years on DOU
DouJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    db_path=DB_PATH,
    category="Python",
    experience="1-3",
).check_and_add_jobs()

# Check new jobs for no experience level on DOU
DouJobScraper(
    telegram_token=NO_EXP_TOKEN,
    chat_id=NO_EXP_CHAT_ID,
    db_path=DB_PATH,
    no_exp=True,
).check_and_add_jobs()
