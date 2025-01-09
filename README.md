# Job Scraper
This project is designed to scrape job postings from popular job boards and send new listings to a Telegram channel.

---

###  Features
- **Scraping**: Collects job postings from the DOU website, including categories like Python, remote work, and jobs requiring no experience.
- **Database Integration**: Stores job postings in a SQLite database, ensuring no duplicates.
- **Telegram Notifications**: Sends real-time notifications for new job postings to Telegram chats.
- **Customizable Configurations**: Supports filtering by experience, category, city, and job type (remote/relocation).
- **Duplicate Detection**: Prevents duplicate job entries in the database.

---

### Technologies Used
- **Python 3.11**: Programming language.
- **Libraries**:
  - `requests`: For sending HTTP requests.
  - `BeautifulSoup` (from `bs4`): For parsing and extracting data from HTML.
  - `sqlite3`: For database operations.
  - `logging`: For tracking errors and activities.

---

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/dou-job-scraper.git
    cd dou-job-scraper
    python3.11 -m venv venv
    source venv/bin/activate  # For Linux/MacOS
    venv\Scripts\activate     # For Windows
    pip install -r requirements.txt
    ```
2. Set up environment variables in config/settings.py:
    ```bash
    TELEGRAM_TOKEN = "your_telegram_bot_token"
    CHAT_ID = "your_telegram_chat_id"
    NO_EXP_TELEGRAM_TOKEN = "your_no_experience_bot_token"
    NO_EXP_CHAT_ID = "your_no_experience_chat_id"
    DB_PATH = "your_database_path.db"
    ```

---

### Usage
	1.	Configure Scraper:
	•	Adjust settings in config/scraper_config.py to define categories, experience levels, and filters.
	2.	Run Scraper:
Example of running the scraper for Python jobs with 0-1 years of experience:
```python
from config.scraper_config import DouScraperConfig
from src.dou_job_scraper import DouJobScraper

config = DouScraperConfig(
    db_path="path_to_your_db",
    telegram_token="your_telegram_bot_token",
    chat_id="your_chat_id",
    category="Python",
    experience="0-1",
)
scraper = DouJobScraper(config)
scraper.check_and_add_jobs()
```

Run sript:
```bash
python run_scraper.py
```

### Database
- SQLite is used to store jobs to avoid duplication. 

**GitHub Actions**
- The project includes a GitHub Actions workflow that automatically runs the scraper every hour.

**Contributing**

Contributions are welcome! Please feel free to submit pull requests or open issues.

**License**
This project is licensed under the **MIT** License.
