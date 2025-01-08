from html import unescape
import feedparser
from bs4 import BeautifulSoup


# URL RSS-каналу
rss_url = "https://djinni.co/jobs/rss/?q_company=&primary_keyword=Python&exp_level=no_exp&exp_level=1y&exp_level=2y&english_level=no_english&english_level=basic&english_level=pre&english_level=intermediate"

# Завантаження і розбір RSS
feed = feedparser.parse(rss_url)


num_job = 0
# Обробка вакансій
for entry in feed.entries[:10]:
    num_job += 1
    # Назва вакансії
    title = entry.title
    
    # Лінк на вакансію
    link = entry.link
    
    # Опис вакансії (з HTML декодуванням)
    raw_description = unescape(entry.summary)
    description = BeautifulSoup(raw_description, "html.parser").get_text()
    
    # Дата публікації
    pub_date = entry.published
    
    # Категорії (якщо є)
    categories = entry.get("tags", [])
    category_list = [tag.term for tag in categories]
    
    print(f"Дата публікації: {pub_date}")
    print(f"Вакансія: {title}")
    print(f"Посилання: {link}")
    print(f"Категорії: {', '.join(category_list) if category_list else 'Не вказано'}")
    print(f"Опис: {description}")
    print(num_job, "-" * 40)
