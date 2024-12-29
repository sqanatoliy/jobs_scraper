# Job Scraper
This project is designed to scrape job postings from popular job boards and send new listings to a Telegram channel.

### Features
- Scrapes job postings from websites like GlobalLogic and Dou.ua.
- Filters job postings based on criteria like keywords, experience level, and location.
- Sends new job postings to a Telegram channel.
- Uses GitHub Actions to automatically run the scraper every hour.
**Requirements**
- Python 3.11
- requests
- beautifulsoup4
- python-dotenv
### Usage
- Clone the repository.
- Create a .env file in the root directory and add your Telegram bot token and chat ID.
- Run the main.py script to start the scraper.
**GitHub Actions**
The project includes a GitHub Actions workflow that automatically runs the scraper every hour. The workflow also caches the CSV files to speed up the scraping process.

**Contributing**

Contributions are welcome! Please feel free to submit pull requests or open issues.

**License**
This project is licensed under the **MIT** License.
