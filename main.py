from dotenv import load_dotenv
import os

from scrapers.gb_lg_jobs_scraper import GlobalLogicJobScraper
from scrapers.dou_jobs_scraper import DouJobScraper

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

gl_lg_scraper_0_1 = GlobalLogicJobScraper(
    csv_file="./csv_files/gl_logic_0_1.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="0-1+years",
    locations="ukraine",
)
job_offers_0_1 = gl_lg_scraper_0_1.get_list_jobs()
new_jobs_0_1 = gl_lg_scraper_0_1.check_and_add_jobs(job_offers_0_1)
if new_jobs_0_1:
    gl_lg_scraper_0_1.send_new_jobs_to_telegram(new_jobs_0_1)

# Repeat for experience level 1-3 years
gl_lg_scraper_1_3 = GlobalLogicJobScraper(
    csv_file="./csv_files/gl_logic_1_3.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="1-3+years",
    locations="ukraine",
)
job_offers_1_3 = gl_lg_scraper_1_3.get_list_jobs()
new_jobs_1_3 = gl_lg_scraper_1_3.check_and_add_jobs(job_offers_1_3)
if new_jobs_1_3:
    gl_lg_scraper_1_3.send_new_jobs_to_telegram(new_jobs_1_3)

dou_scraper_01 = DouJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    csv_file="./csv_files/dou_0_1.csv",
    category="Python",
    experience="0-1",
)
dou_job_offers_01 = dou_scraper_01.get_list_jobs()
new_dou_jobs_01 = dou_scraper_01.check_and_add_jobs(dou_job_offers_01)
if new_dou_jobs_01:
    dou_scraper_01.send_new_jobs_to_telegram(new_dou_jobs_01)

dou_scraper_13 = DouJobScraper(
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    csv_file="./csv_files/dou_1_3.csv",
    category="Python",
    experience="1-3",
)
dou_job_offers_13 = dou_scraper_13.get_list_jobs()
new_dou_jobs_13 = dou_scraper_13.check_and_add_jobs(dou_job_offers_13)
if new_dou_jobs_13:
    dou_scraper_13.send_new_jobs_to_telegram(new_dou_jobs_13)
