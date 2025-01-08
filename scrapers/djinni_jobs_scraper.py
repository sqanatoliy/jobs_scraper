from html import unescape
import feedparser


# URL RSS-каналу
rss_url = "https://djinni.co/jobs/rss/?primary_keyword=Python"

# Завантаження і розбір RSS
feed = feedparser.parse(rss_url)

num_job = 1
# Обробка вакансій
for entry in feed.entries:
    num_job += 1
    # Назва вакансії
    title = entry.title
    
    # Лінк на вакансію
    link = entry.link
    
    # Опис вакансії (з HTML декодуванням)
    description = unescape(entry.description)
    
    # Дата публікації
    pub_date = entry.published
    
    # Категорії (якщо є)
    categories = entry.get("tags", [])
    category_list = [tag.term for tag in categories]
    
    print(f"Вакансія: {title}")
    print(f"Посилання: {link}")
    print(f"Дата публікації: {pub_date}")
    print(f"Категорії: {', '.join(category_list) if category_list else 'Не вказано'}")
    print("Опис:")
    print(description)
    print(num_job, "-" * 40)