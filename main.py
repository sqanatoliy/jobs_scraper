from dotenv import load_dotenv
import os

from scrapers.gb_lg_jobs_scraper import GlobalLogicJobScraper
from scrapers.dou_jobs_scraper import DouJobScraper

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Check new jobs for experience level 0-1 years
GlobalLogicJobScraper(
    csv_file="./csv_files/gl_logic_0_1.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="0-1+years",
    locations="ukraine",
).send_new_jobs_to_telegram()


# Check new jobs for experience level 1-3 years
GlobalLogicJobScraper(
    csv_file="./csv_files/gl_logic_1_3.csv",
    telegram_token=TOKEN,
    chat_id=CHAT_ID,
    keywords="python",
    experience="1-3+years",
    locations="ukraine",
).send_new_jobs_to_telegram()


# dou_scraper_01 = DouJobScraper(
#     telegram_token=TOKEN,
#     chat_id=CHAT_ID,
#     csv_file="./csv_files/dou_0_1.csv",
#     category="Python",
#     experience="0-1",
# )
# dou_job_offers_01 = dou_scraper_01.get_list_jobs()
# new_dou_jobs_01 = dou_scraper_01.check_and_add_jobs(dou_job_offers_01)
# if new_dou_jobs_01:
#     dou_scraper_01.send_new_jobs_to_telegram(new_dou_jobs_01)

# dou_scraper_13 = DouJobScraper(
#     telegram_token=TOKEN,
#     chat_id=CHAT_ID,
#     csv_file="./csv_files/dou_1_3.csv",
#     category="Python",
#     experience="1-3",
# )
# dou_job_offers_13 = dou_scraper_13.get_list_jobs()
# new_dou_jobs_13 = dou_scraper_13.check_and_add_jobs(dou_job_offers_13)
# if new_dou_jobs_13:
#     dou_scraper_13.send_new_jobs_to_telegram(new_dou_jobs_13)
