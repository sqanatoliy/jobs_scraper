
"""
This script checks for new job postings on different websites 
and sends them to a specified Telegram chat.

Usage:
1. Ensure that the .env file contains the TELEGRAM_TOKEN and CHAT_ID.
2. Run the script to check for new job postings and send them to the specified Telegram chat.
"""
import os
from dotenv import load_dotenv

from config.scraper_config import DouScraperConfig, GlobalLogicScraperConfig
from src.gb_lg_job_scraper import GlobalLogicJobScraper
from src.dou_job_scraper import DouJobScraper
from config.settings import TELEGRAM_TOKEN, CHAT_ID, NO_EXP_TELEGRAM_TOKEN, NO_EXP_CHAT_ID, DB_PATH

load_dotenv()


# Configuration for checking new jobs for experience level 0-1 years on GlobalLogic
gl_lg_python_0_1 = GlobalLogicScraperConfig(
    telegram_token=TELEGRAM_TOKEN,
    chat_id=CHAT_ID,
    db_path=DB_PATH,
    keywords="python",
    experience="0-1+years",
    locations="ukraine",
)

# Configuration for checking new jobs for experience level 1-3 years on GlobalLogic
gl_lg_python_1_3 = GlobalLogicScraperConfig(
    telegram_token=TELEGRAM_TOKEN,
    chat_id=CHAT_ID,
    db_path=DB_PATH,
    keywords="python",
    experience="1-3+years",
    locations="ukraine",
)

# Configuration for checking new jobs for experience level 0-1 years on DOU
dou_python_config_0_1 = DouScraperConfig(
    db_path=DB_PATH,
    telegram_token=TELEGRAM_TOKEN,
    chat_id=CHAT_ID,
    category="Python",
    experience="0-1",
)

# Configuration for checking new jobs for experience level 1-3 years on DOU
dou_python_config_1_3 = DouScraperConfig(
    db_path=DB_PATH,
    telegram_token=TELEGRAM_TOKEN,
    chat_id=CHAT_ID,
    category="Python",
    experience="1-3",
)

# Configuration for checking new jobs for no experience level on DOU
dou_no_exp_remote_config = DouScraperConfig(
    db_path=DB_PATH,
    telegram_token=NO_EXP_TELEGRAM_TOKEN,
    chat_id=NO_EXP_CHAT_ID,
    city="remote",
    no_exp=True,
)

# Configuration for checking new Support jobs for experience level 0-1 years on DOU
dou_support_remote_config_0_1 = DouScraperConfig(
    db_path=DB_PATH,
    telegram_token=NO_EXP_TELEGRAM_TOKEN,
    chat_id=NO_EXP_CHAT_ID,
    category="Support",
    experience="0-1",
    remote=True,
)

#####################################################################################################
# Check new Python jobs for experience level 0-1 years on GlobalLogic
GlobalLogicJobScraper(gl_lg_python_0_1).check_and_add_jobs()

# Check new Python jobs for experience level 1-3 years on GlobalLogic
GlobalLogicJobScraper(gl_lg_python_1_3).check_and_add_jobs()

# Check new Python jobs for experience level 0-1 years on DOU
DouJobScraper(dou_python_config_0_1).check_and_add_jobs()

# Check new Python jobs for experience level 1-3 years on DOU
DouJobScraper(dou_python_config_1_3).check_and_add_jobs()

# Check new jobs for all remote category of no experience level on DOU
# For the “No experience” category only, set city='remote' to select remote offers
DouJobScraper(dou_no_exp_remote_config).check_and_add_jobs()

# Check new Support remote jobs for experience level 0-1 years on DOU
DouJobScraper(dou_support_remote_config_0_1).check_and_add_jobs()
