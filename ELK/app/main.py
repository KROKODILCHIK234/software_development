import logging
import random
import os
import csv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from typing import List, Dict, Optional

# Создаем директорию для логов, если она не существует
os.makedirs("logs", exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Цитат Джейсона Стэтема")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь к CSV файлу с цитатами
CSV_FILE_PATH = "data/statham.csv"


# Функция для загрузки цитат из CSV файла
def load_quotes() -> List[Dict[str, str]]:
    quotes = []
    try:
        # Проверяем существование файла
        if not os.path.exists(CSV_FILE_PATH):
            logger.error(f"Файл с цитатами не найден: {CSV_FILE_PATH}")
            return quotes

        # Читаем CSV файл
        with open(CSV_FILE_PATH, 'r', encoding='utf-8') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                quotes.append({
                    'quote': row.get('Цитата', ''),
                    'category': row.get('Категория', ''),
                    'source': row.get('Источник', ''),
                    'type': row.get('Тип', '')
                })

        logger.info(f"Загружено {len(quotes)} цитат из CSV файла")
    except Exception as e:
        logger.error(f"Ошибка при загрузке цитат: {str(e)}")

    return quotes


# Глобальная переменная для хранения цитат
quotes = []


@app.on_event("startup")
async def startup_event():
    """Загружаем цитаты при запуске приложения"""
    global quotes
    quotes = load_quotes()
    if not quotes:
        # Если цитаты не загрузились, добавляем запасную цитату
        quotes = [{
            'quote': 'Статистика - это как бикини. Она показывает многое, но скрывает самое главное.',
            'category': 'Юмор',
            'source': 'Неизвестно',
            'type': 'Цитата'
        }]


@app.get("/")
async def root():
    return {"message": "API цитат Джейсона Стэтема работает! Используйте /quote для получения случайной цитаты."}


@app.get("/quote")
async def get_quote(request: Request, category: Optional[str] = None):
    """
    Получить случайную цитату

    - **category**: Опциональный фильтр по категории
    """
    global quotes

    # Фильтрация по категории, если указана
    filtered_quotes = quotes
    if category:
        filtered_quotes = [q for q in quotes if q['category'].lower() == category.lower()]
        if not filtered_quotes:
            logger.warning(f"Не найдено цитат для категории: {category}")
            return {"error": f"Не найдено цитат для категории: {category}"}

    # Выбираем случайную цитату
    quote_data = random.choice(filtered_quotes)

    # Логирование
    client_host = request.client.host
    logger.info(f"Запрос на получение цитаты от {client_host}: {quote_data['quote'][:50]}...")

    return {
        "quote": quote_data['quote'],
        "category": quote_data['category'],
        "source": quote_data['source'],
        "type": quote_data['type']
    }


@app.get("/categories")
async def get_categories():
    """Получить список всех доступных категорий"""
    global quotes
    categories = set(quote['category'] for quote in quotes)
    return {"categories": sorted(list(categories))}


@app.get("/stats")
async def get_stats():
    """Получить статистику по цитатам"""
    global quotes

    # Считаем количество цитат в каждой категории
    category_counts = {}
    for quote in quotes:
        category = quote['category']
        category_counts[category] = category_counts.get(category, 0) + 1

    # Считаем количество цитат по типам
    type_counts = {}
    for quote in quotes:
        quote_type = quote['type']
        type_counts[quote_type] = type_counts.get(quote_type, 0) + 1

    return {
        "total_quotes": len(quotes),
        "categories": category_counts,
        "types": type_counts
    }


@app.get("/health")
async def health_check():
    logger.info("Проверка здоровья системы")
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "quotes_loaded": len(quotes)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)