import os
from os import path
from os.path import join
from pathlib import Path
from dotenv import load_dotenv


load_dotenv(dotenv_path='.env')

ROOT_PATH: Path = Path(path.abspath(__file__)).parent.parent

# Database
DB_PATH = join(ROOT_PATH, "data/job_data.db")

# Telegram API
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NO_EXP_TELEGRAM_TOKEN = os.getenv("NO_EXP_TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
NO_EXP_CHAT_ID = os.getenv("NO_EXP_CHAT_ID")

# Logging
LOG_FILE = os.getenv("LOG_FILE", "logs/scraper.log")

# other settings
USER_AGENT = "Mozilla/5.0"
REQUEST_TIMEOUT = 30

# DJINNI URLS
DJINNI_NO_EXP_URL = "https://djinni.co/jobs/rss/?exp_level=no_exp&english_level=no_english&english_level=basic&english_level=pre&english_level=intermediate"
DJINNI_OTHER_URL = "https://djinni.co/jobs/rss/?primary_keyword=Other&exp_level=no_exp&exp_level=1y&english_level=no_english&english_level=basic&english_level=pre&english_level=intermediate"
DJINNI_SUPPORT_URL = "https://djinni.co/jobs/rss/?primary_keyword=Support&exp_level=no_exp&exp_level=1y&english_level=no_english&english_level=basic&english_level=pre&english_level=intermediate"
DJINNI_PYTHON_URL = "https://djinni.co/jobs/rss/?primary_keyword=Python&exp_level=no_exp&exp_level=1y&exp_level=2y&english_level=no_english&english_level=basic&english_level=pre&english_level=intermediate"
