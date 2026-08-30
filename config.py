# ====================================
# TajDonat Mini App - Configuration
# ====================================

import os
from typing import Dict

# ============= TELEGRAM =============
# ⚠️ Впиши сюда СВОИ НОВЫЕ значения (старые из чата считаются скомпрометированными —
# перевыпусти токен через @BotFather -> /revoke, и API-ключ в личном кабинете Epinby)
TELEGRAM_BOT_TOKEN = "8742900596:AAEQvuOoPGrwppic1_JiagXl4z_VZmNzCr4"
TELEGRAM_WEBAPP_URL = "https://donatertaj.onrender.com"  # без слэша на конце, например https://tajdonat.example.com

# ============= EPINBY API =============
EPINBY_API_KEY = "kaRSM3jf7PASFhhWX8CmIabnzDq11OBZqQkyMD9d"
EPINBY_BASE_URL = "https://epinby.com/api/v1"
EPINBY_WEBHOOK_SECRET = "fvlXgqw199FxsFCR8tuhF9QrJj6H1RWT"

# ============= ADMIN SETTINGS =============
ADMIN_USERNAME = "dr_kurbonov04"
ADMIN_USER_ID = 5125234072
ADMIN_PASSWORD = "Amir142004"  # Смени в /admin после первого входа
ADMIN_PANEL_PATH = "/admin"

# ============= NOTIFICATION CHANNELS =============
ADMIN_GROUP_CHAT_ID = None  # Можно вписать ID группы сюда, либо задать позже прямо в /admin -> Настройки
SALES_CHANNEL_ID = None     # Аналогично — ID канала продаж


# ============= LANGUAGES =============
LANGUAGES = {
    "tg": {
        "name": "Тоҷикӣ",
        "flag": "🇹🇯",
        "code": "tg"
    },
    "ru": {
        "name": "Русский",
        "flag": "🇷🇺",
        "code": "ru"
    }
}

DEFAULT_LANGUAGE = "tg"

# ============= CURRENCIES =============
CURRENCIES = {
    "somoni": {
        "symbol": "сомони",
        "code": "TJS",
        "short": "с",
    },
    "ruble": {
        "symbol": "рубль",
        "code": "RUB",
        "short": "₽",
    }
}

DEFAULT_CURRENCY = "somoni"

# ============= DATABASE =============
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tajdonat.db")
# Для production используй PostgreSQL: postgresql://user:password@localhost/tajdonat

# ============= PATHS =============
# ВАЖНО: config.py лежит в корне проекта, поэтому BASE_DIR = сам корень проекта.
# (Раньше здесь было двойное dirname — из-за этого uploads/ и logs/ создавались
# на один уровень ВЫШЕ папки проекта. Исправлено.)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
CATEGORIES_IMAGES_DIR = os.path.join(UPLOADS_DIR, "categories")
PRODUCTS_IMAGES_DIR = os.path.join(UPLOADS_DIR, "products")
RECEIPTS_DIR = os.path.join(UPLOADS_DIR, "receipts")

# Создай директории если их нет
for directory in [UPLOADS_DIR, CATEGORIES_IMAGES_DIR, PRODUCTS_IMAGES_DIR, RECEIPTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ============= PAYMENT SETTINGS =============
MIN_BALANCE_TOPUP = 1  # Минимальная сумма пополнения
MAX_BALANCE_TOPUP = 100000  # Максимальная сумма пополнения

# ============= ORDER SETTINGS =============
ORDER_STATUS_PENDING = "PENDING"
ORDER_STATUS_PROCESSING = "PROCESSING"
ORDER_STATUS_COMPLETED = "COMPLETED"
ORDER_STATUS_FAILED = "FAILED"
ORDER_STATUS_PARTIAL = "PARTIAL"  # Частичное выполнение

ORDER_STATUSES = [
    ORDER_STATUS_PENDING,
    ORDER_STATUS_PROCESSING,
    ORDER_STATUS_COMPLETED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_PARTIAL,
]

# ============= STATISTICS =============
WEEKLY_STATS_DAYS = 7  # Статистика заказов за 7 дней

# ============= REFERRAL BONUS =============
REFERRAL_BONUS_PERCENT = 1.0  # Процент бонуса за реферала (1%)

# ============= TRANSLATIONS KEYS =============
TRANSLATIONS_KEYS = {
    # Menu
    "menu_catalog": {"tg": "Каталог", "ru": "Каталог"},
    "menu_history": {"tg": "Таърих", "ru": "История"},
    "menu_profile": {"tg": "Профил", "ru": "Профиль"},
    "menu_support": {"tg": "Дастгирӣ", "ru": "Поддержка"},
    
    # Common
    "back": {"tg": "Назад", "ru": "Назад"},
    "done": {"tg": "Маҳайё", "ru": "Готово"},
    "cancel": {"tg": "Бекор кунед", "ru": "Отмена"},
    "error": {"tg": "Хатоӣ", "ru": "Ошибка"},
}

# ============= LOGGING =============
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.path.join(BASE_DIR, "logs", "tajdonat.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# ============= DEBUG MODE =============
DEBUG = os.getenv("DEBUG", "False").lower() == "true"