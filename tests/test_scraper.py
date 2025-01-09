import sqlite3
import unittest
from unittest.mock import MagicMock

from config.scraper_config import DouScraperConfig
from config.settings import TELEGRAM_TOKEN, CHAT_ID, DB_PATH
from src.dou_job_scraper import DouJobScraper


class TestDouJobScraper(unittest.TestCase):
    # Configuration for checking new jobs for experience level 0-1 years on DOU
    dou_config_0_1 = DouScraperConfig(
        db_path=DB_PATH,
        telegram_token=TELEGRAM_TOKEN,
        chat_id=CHAT_ID,
        category="Python",
        experience="0-1",
        city="Kyiv",
    )

    def setUp(self) -> None:
        # Connect to the in-memory database
        self.conn: sqlite3.Connection = sqlite3.connect(':memory:')
        self.cursor: sqlite3.Cursor = self.conn.cursor()

        # Create table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dou_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                title TEXT,
                link TEXT,
                company TEXT,
                salary TEXT,
                cities TEXT,
                sh_info TEXT,
                category TEXT,
                experience TEXT,
                UNIQUE(title, date, company, category)
            )
        """)
        self.conn.commit()

        # Create indexes
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_title_date_company_category ON dou_jobs (title, date, company, category)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON dou_jobs (category)")
        self.conn.commit()

        # Mock the _initialize_database method
        self.scraper = DouJobScraper(self.dou_config_0_1)
        self.scraper._initialize_database = MagicMock()

    def tearDown(self):
        # Close the connection to the in-memory database
        self.conn.close()

    def test_construct_full_url(self) -> None:
        """
        Full URL should contain all the parameters
        """
        self.assertIn("city=Kyiv", self.scraper._construct_full_url())
        self.assertIn("category=Python", self.scraper._construct_full_url())
        print(self.scraper._construct_full_url())
