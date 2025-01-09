"""
This script automates job scraping from GlobalLogic and DOU platforms, 
categorizing postings by experience level and type, 
and sending notifications via Telegram when new jobs matching specific configurations are found.

Modules Imported:
- `config.scraper_config`: Configuration classes for GlobalLogic and DOU scrapers.
- `src.gb_lg_job_scraper`: Scraping jobs from GlobalLogic.
- `src.dou_job_scraper`: Scraping jobs from DOU.
- `config.settings`: Environment variables for Telegram tokens, chat IDs, and database path.

Configurations:
1. **GlobalLogic**:
   - Python jobs for 0-1 and 1-3 years of experience.
   - Configurations include Telegram credentials, database path, keywords, and location.

2. **DOU**:
   - Python jobs (0-1 and 1-3 years of experience).
   - Remote jobs for no-experience category.
   - Remote Support jobs (0-1 years of experience).

Workflow:
- `GlobalLogicJobScraper`: Scrapes GlobalLogic jobs by experience level.
- `DouJobScraper`: Scrapes DOU jobs by category and experience level.
- Sends Telegram notifications for new jobs and prevents duplicates using a database.

Features:
- Automated scraping from multiple platforms.
- Flexible configurations for job categories and levels.
- Real-time notifications via Telegram.
"""
from config.scraper_config import DouScraperConfig, GlobalLogicScraperConfig
from config.settings import TELEGRAM_TOKEN, CHAT_ID, NO_EXP_TELEGRAM_TOKEN, NO_EXP_CHAT_ID, DB_PATH
from src.gb_lg_job_scraper import GlobalLogicJobScraper
from src.dou_job_scraper import DouJobScraper


# GLOBAL LOGIC CONFIGURATIONS ==========================================================
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
# END GLOBAL LOGIC CONFIGURATIONS ======================================================

# DOU CONFIGURATIONS ==================================================================
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
# END DOU CONFIGURATIONS ============================================================

# GLOBAL LOGIC JOB SCRAPING ==========================================================
# Check new Python jobs for experience level 0-1 years on GlobalLogic
GlobalLogicJobScraper(gl_lg_python_0_1).check_and_add_jobs()

# Check new Python jobs for experience level 1-3 years on GlobalLogic
GlobalLogicJobScraper(gl_lg_python_1_3).check_and_add_jobs()
# END GLOBAL LOGIC JOB SCRAPING ======================================================

# DOU JOB SCRAPING ===================================================================
# Check new Python jobs for experience level 0-1 years on DOU
DouJobScraper(dou_python_config_0_1).check_and_add_jobs()

# Check new Python jobs for experience level 1-3 years on DOU
DouJobScraper(dou_python_config_1_3).check_and_add_jobs()

# Check new jobs for all remote category of no experience level on DOU
# For the “No experience” category only, set city='remote' to select remote offers
DouJobScraper(dou_no_exp_remote_config).check_and_add_jobs()

# Check new Support remote jobs for experience level 0-1 years on DOU
DouJobScraper(dou_support_remote_config_0_1).check_and_add_jobs()
# END DOU JOB SCRAPING ===============================================================
