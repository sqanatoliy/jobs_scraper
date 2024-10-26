from dotenv import load_dotenv
import os

from scrapers.gb_lg_jobs_scraper import GlobalLogicJobScraper

load_dotenv()

TOKEN = os.getenv("telegram_token")
CHAT_ID = os.getenv("chat_id")

scraper_0_1 = GlobalLogicJobScraper(
    csv_file="./csv_files/gl_logic_0_1.csv",
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
    csv_file="./csv_files/gl_logic_1_3.csv",
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
