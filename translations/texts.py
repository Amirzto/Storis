# ====================================
# TajDonat - Translations
# ====================================

import json
import time
import logging

logger = logging.getLogger(__name__)

TRANSLATIONS = {
    # ========== MAIN MENU ==========
    "menu_catalog": {
        "tg": "📦 Каталог",
        "ru": "📦 Каталог"
    },
    "menu_history": {
        "tg": "⏰ Таърих",
        "ru": "⏰ История"
    },
    "menu_profile": {
        "tg": "👤 Профил",
        "ru": "👤 Профиль"
    },
    "menu_support": {
        "tg": "🆘 Дастгирӣ",
        "ru": "🆘 Поддержка"
    },

    # ========== PHONE REQUEST ==========
    "request_phone_title": {
        "tg": "📱 Барои беҳтар кардани хидматрасонӣ рақами телефони худро мубодила кунед:",
        "ru": "📱 Поделитесь номером телефона, чтобы мы могли лучше вас обслуживать:"
    },
    "btn_share_phone": {
        "tg": "📱 Рақами телефонро фиристед",
        "ru": "📱 Поделиться номером"
    },
    "btn_skip_phone": {
        "tg": "Гузарондан",
        "ru": "Пропустить"
    },
    "phone_saved_msg": {
        "tg": "✅ Раҳмат! Рақами телефон сабт шуд.",
        "ru": "✅ Спасибо! Номер телефона сохранён."
    },
    "phone_wrong_owner": {
        "tg": "⚠️ Лутфан рақами телефони худатонро фиристед.",
        "ru": "⚠️ Пожалуйста, отправьте свой собственный номер телефона."
    },
    
    # ========== CATALOG ==========
    "catalog_title": {
        "tg": "📦 Каталог товаров",
        "ru": "📦 Каталог товаров"
    },
    "select_category": {
        "tg": "Категорияро интихоб кунед:",
        "ru": "Выберите категорию:"
    },
    "select_product": {
        "tg": "Товорро интихоб кунед:",
        "ru": "Выберите товар:"
    },
    "product_quantity": {
        "tg": "Миқдор:",
        "ru": "Количество:"
    },
    "product_price": {
        "tg": "Қимат:",
        "ru": "Цена:"
    },
    "product_variants": {
        "tg": "Вариант:",
        "ru": "Вариант:"
    },
    "select_variant": {
        "tg": "Вариантро интихоб кунед:",
        "ru": "Выберите вариант:"
    },
    "no_variants": {
        "tg": "Вариант нист",
        "ru": "Вариантов нет"
    },
    
    # ========== PROFILE ==========
    "profile_title": {
        "tg": "👤 Профили ман",
        "ru": "👤 Мой профиль"
    },
    "profile_user_id": {
        "tg": "ID:",
        "ru": "ID:"
    },
    "profile_username": {
        "tg": "Номи истифодабарандагӣ:",
        "ru": "Имя пользователя:"
    },
    "profile_phone": {
        "tg": "Рақами телефон:",
        "ru": "Номер телефона:"
    },
    "profile_balance": {
        "tg": "Баланс:",
        "ru": "Баланс:"
    },
    "profile_language": {
        "tg": "Забон:",
        "ru": "Язык:"
    },
    "profile_currency": {
        "tg": "Валюта:",
        "ru": "Валюта:"
    },
    "profile_referral_link": {
        "tg": "Истиноди реферал:",
        "ru": "Реферальная ссылка:"
    },
    "profile_referral_bonus": {
        "tg": "Бонус реферал:",
        "ru": "Бонус рефералов:"
    },
    "profile_referral_count": {
        "tg": "Шумораи реферал:",
        "ru": "Количество рефералов:"
    },
    "button_topup": {
        "tg": "💰 Пур кардани баланс",
        "ru": "💰 Пополнить баланс"
    },
    "button_language": {
        "tg": "🌐 Забонро тағйир диҳед",
        "ru": "🌐 Изменить язык"
    },
    "button_currency": {
        "tg": "💵 Валютаро тағйир диҳед",
        "ru": "💵 Изменить валюту"
    },
    "button_edit_phone": {
        "tg": "📱 Рақами телефонро таҳрир кунед",
        "ru": "📱 Изменить номер телефона"
    },
    
    # ========== BALANCE TOPUP ==========
    "topup_title": {
        "tg": "💰 Пур кардани баланс",
        "ru": "💰 Пополнение баланса"
    },
    "topup_select_amount": {
        "tg": "Миқдорро интихоб кунед:",
        "ru": "Выберите сумму:"
    },
    "topup_custom_amount": {
        "tg": "Миқдори дилхоҳ",
        "ru": "Пользовательская сумма"
    },
    "topup_enter_amount": {
        "tg": "Миқдорро дохил кунед (мин: {min}, макс: {max}):",
        "ru": "Введите сумму (мин: {min}, макс: {max}):"
    },
    "topup_select_method": {
        "tg": "Усули пулакро интихоб кунед:",
        "ru": "Выберите способ оплаты:"
    },
    "topup_method_info": {
        "tg": "Маълумоти пулак:",
        "ru": "Информация о платеже:"
    },
    "topup_account": {
        "tg": "Ҳисоб:",
        "ru": "Счет:"
    },
    "topup_phone": {
        "tg": "Рақами телефон:",
        "ru": "Номер телефона:"
    },
    "topup_upload_receipt": {
        "tg": "Скрин-шотро юпуш кунед:",
        "ru": "Загрузите скриншот:"
    },
    "topup_waiting_confirmation": {
        "tg": "⏳ Интизори тасдиқи админ...",
        "ru": "⏳ Ожидание подтверждения админа..."
    },
    "topup_success": {
        "tg": "✅ Пулак қабул карда шуд!",
        "ru": "✅ Платеж принят!"
    },
    "topup_rejected": {
        "tg": "❌ Пулак рад карда шуд",
        "ru": "❌ Платеж отклонен"
    },
    "topup_invalid_amount": {
        "tg": "❌ Миқдори нодуруст",
        "ru": "❌ Неверная сумма"
    },
    
    # ========== ORDER/PURCHASE ==========
    "order_title": {
        "tg": "🛒 Суратҳисоб",
        "ru": "🛒 Заказ"
    },
    "order_total": {
        "tg": "Ҷами кӯл:",
        "ru": "Итого:"
    },
    "order_confirm": {
        "tg": "✅ Суратҳисобро тасдиқ кунед",
        "ru": "✅ Подтвердить заказ"
    },
    "order_enter_player_id": {
        "tg": "ID ҳуҷҷатҳорӣ дохил кунед:",
        "ru": "Введите ID игрока:"
    },
    "order_enter_server": {
        "tg": "Сервериро интихоб кунед:",
        "ru": "Выберите сервер:"
    },
    "order_player_validating": {
        "tg": "⏳ Тасдиқи ҳуҷҷатҳор...",
        "ru": "⏳ Проверка игрока..."
    },
    "order_player_not_found": {
        "tg": "❌ Ҳуҷҷатҳор пайдо нашуд",
        "ru": "❌ Игрок не найден"
    },
    "order_insufficient_balance": {
        "tg": "❌ Баланс кофӣ нест",
        "ru": "❌ Недостаточно средств"
    },
    "order_place_success": {
        "tg": "✅ Суратҳисоб созданӣ шуд!",
        "ru": "✅ Заказ создан!"
    },
    "order_status_pending": {
        "tg": "⏳ Интизор",
        "ru": "⏳ В ожидании"
    },
    "order_status_processing": {
        "tg": "⚙️ Иҷро",
        "ru": "⚙️ Обработка"
    },
    "order_status_completed": {
        "tg": "✅ Ба итмом расид",
        "ru": "✅ Завершен"
    },
    "order_status_failed": {
        "tg": "❌ Нокомӣ",
        "ru": "❌ Ошибка"
    },
    "order_status_partial": {
        "tg": "⚠️ Қисмӣ",
        "ru": "⚠️ Частично"
    },
    
    # ========== HISTORY/TRANSACTIONS ==========
    "history_title": {
        "tg": "⏰ Таърихи суратҳисоб",
        "ru": "⏰ История заказов"
    },
    "history_topups": {
        "tg": "💰 Пуладӣ",
        "ru": "💰 Пополнения"
    },
    "history_purchases": {
        "tg": "🛒 Харидҳо",
        "ru": "🛒 Покупки"
    },
    "history_empty": {
        "tg": "Таърих холӣ аст",
        "ru": "История пуста"
    },
    "history_date": {
        "tg": "Сана:",
        "ru": "Дата:"
    },
    "history_amount": {
        "tg": "Миқдор:",
        "ru": "Сумма:"
    },
    "history_status": {
        "tg": "Вазъият:",
        "ru": "Статус:"
    },
    
    # ========== SUPPORT ==========
    "support_title": {
        "tg": "🆘 Дастгирӣ",
        "ru": "🆘 Поддержка"
    },
    "support_text": {
        "tg": "Агар масъалаи касе дошта бошед, бо админ тамос гиред:",
        "ru": "Если у вас есть проблемы, свяжитесь с админом:"
    },
    "support_contact_admin": {
        "tg": "📞 Админро тамос кунед",
        "ru": "📞 Связаться с админом"
    },
    "support_faq": {
        "tg": "❓ ПарсишҲои Бесамовалан",
        "ru": "❓ Часто задаваемые вопросы"
    },
    
    # ========== COMMON BUTTONS ==========
    "btn_back": {
        "tg": "◀️ Назад",
        "ru": "◀️ Назад"
    },
    "btn_home": {
        "tg": "🏠 Асосӣ",
        "ru": "🏠 Главное меню"
    },
    "btn_confirm": {
        "tg": "✅ Тасдиқ",
        "ru": "✅ Подтвердить"
    },
    "btn_cancel": {
        "tg": "❌ Бекор",
        "ru": "❌ Отмена"
    },
    "btn_copy": {
        "tg": "📋 Нусха",
        "ru": "📋 Копировать"
    },
    "btn_share": {
        "tg": "🔗 Муштарак",
        "ru": "🔗 Поделиться"
    },
    "btn_edit": {
        "tg": "✏️ Таҳрир",
        "ru": "✏️ Редактировать"
    },
    "btn_delete": {
        "tg": "🗑️ Нест",
        "ru": "🗑️ Удалить"
    },
    "btn_next": {
        "tg": "▶️ Навбатӣ",
        "ru": "▶️ Дальше"
    },
    "btn_add": {
        "tg": "➕ Илова",
        "ru": "➕ Добавить"
    },
    "btn_search": {
        "tg": "🔍 Ҷустуҷӯ",
        "ru": "🔍 Поиск"
    },
    
    # ========== ERRORS ==========
    "error_title": {
        "tg": "❌ Хатоӣ",
        "ru": "❌ Ошибка"
    },
    "error_not_found": {
        "tg": "Маълумот пайдо нашуд",
        "ru": "Информация не найдена"
    },
    "error_access_denied": {
        "tg": "Дастрасӣ рад карда шуд",
        "ru": "Доступ запрещен"
    },
    "error_invalid_input": {
        "tg": "Воридоти нодуруст",
        "ru": "Неверные данные"
    },
    "error_something_wrong": {
        "tg": "Чизе нодуруст шуд. Бори дигар кӯшиш кунед.",
        "ru": "Что-то пошло не так. Попробуйте снова."
    },
    "error_try_again": {
        "tg": "🔄 Дубора кӯшиш кунед",
        "ru": "🔄 Попробуйте снова"
    },
    "error_user_blocked": {
        "tg": "👤 Шумо блокӣ карда шудед",
        "ru": "👤 Вы заблокированы"
    },
    
    # ========== ADMIN PANEL ==========
    "admin_title": {
        "tg": "⚙️ Админ Панел",
        "ru": "⚙️ Админ Панель"
    },
    "admin_dashboard": {
        "tg": "📊 Дашборд",
        "ru": "📊 Панель управления"
    },
    "admin_categories": {
        "tg": "📁 Категория",
        "ru": "📁 Категории"
    },
    "admin_products": {
        "tg": "📦 Товаров",
        "ru": "📦 Товары"
    },
    "admin_users": {
        "tg": "👥 Истифодабарандагон",
        "ru": "👥 Пользователи"
    },
    "admin_orders": {
        "tg": "🛒 Суратҳисобҳо",
        "ru": "🛒 Заказы"
    },
    "admin_payments": {
        "tg": "💳 Пулакҳо",
        "ru": "💳 Платежи"
    },
    "admin_reviews": {
        "tg": "⭐ Барқарорӣ",
        "ru": "⭐ Отзывы"
    },
    "admin_payment_methods": {
        "tg": "💰 Усули пулак",
        "ru": "💰 Способы оплаты"
    },
    "admin_settings": {
        "tg": "⚙️ Танзимот",
        "ru": "⚙️ Настройки"
    },
    "admin_add_category": {
        "tg": "➕ Категория ислоҳ",
        "ru": "➕ Добавить категорию"
    },
    "admin_add_product": {
        "tg": "➕ Товори ислоҳ",
        "ru": "➕ Добавить товар"
    },
    "admin_edit_category": {
        "tg": "✏️ Категория таҳрир",
        "ru": "✏️ Редактировать категорию"
    },
    "admin_edit_product": {
        "tg": "✏️ Товор таҳрир",
        "ru": "✏️ Редактировать товар"
    },
    "admin_delete_category": {
        "tg": "🗑️ Категория нест",
        "ru": "🗑️ Удалить категорию"
    },
    "admin_delete_product": {
        "tg": "🗑️ Товор нест",
        "ru": "🗑️ Удалить товар"
    },
    "admin_confirm_payment": {
        "tg": "✅ Пулак тасдиқ",
        "ru": "✅ Подтвердить платеж"
    },
    "admin_reject_payment": {
        "tg": "❌ Пулак рад",
        "ru": "❌ Отклонить платеж"
    },
    "admin_block_user": {
        "tg": "🚫 Истифодабаранда блокӣ",
        "ru": "🚫 Заблокировать пользователя"
    },
    "admin_unblock_user": {
        "tg": "✅ Истифодабаранда разблок",
        "ru": "✅ Разблокировать пользователя"
    },
    
    # ========== STATS ==========
    "stats_total_users": {
        "tg": "Ҷами истифодабарандагон:",
        "ru": "Всего пользователей:"
    },
    "stats_total_orders": {
        "tg": "Ҷами суратҳисобҳо:",
        "ru": "Всего заказов:"
    },
    "stats_total_revenue": {
        "tg": "Ҷами даромад:",
        "ru": "Общий доход:"
    },
    "stats_weekly_orders": {
        "tg": "Суратҳисобҳои ҳафтанӣ:",
        "ru": "Заказы за неделю:"
    },
    "stats_pending_payments": {
        "tg": "Пулакҳои интизор:",
        "ru": "Платежи в ожидании:"
    },
    
    # ========== CURRENCY SYMBOLS ==========
    "currency_somoni": {
        "tg": "с",
        "ru": "с"
    },
    "currency_ruble": {
        "tg": "₽",
        "ru": "₽"
    },
    
    # ========== WELCOME ==========
    "welcome_title": {
        "tg": "👋 Хуш омадед ба TajDonat!",
        "ru": "👋 Добро пожаловать в TajDonat!"
    },
    "welcome_description": {
        "tg": "Байҳатарин маҳали фрӯши товарҳои дигитал",
        "ru": "Лучшее место для покупки цифровых товаров"
    },
    "welcome_select_language": {
        "tg": "Забонро интихоб кунед:",
        "ru": "Выберите язык:"
    },
}


# ============= ADMIN TEXT OVERRIDES (редактор текстов в админ-панели) =============
# Оверрайды хранятся в таблице settings (ключ "text_overrides") и читаются сюда с
# небольшим TTL-кэшем, чтобы изменения из веб-админки подхватывались и процессом
# бота (bot.py), и веб-сервером (server.py) без необходимости прокидывать db в get_text().

_overrides_cache: dict = {}
_overrides_loaded_at: float = 0.0
_OVERRIDES_TTL_SECONDS = 30


def _load_overrides_from_db() -> dict:
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from config import DATABASE_URL
        from database.crud import SettingsCRUD

        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        try:
            raw = SettingsCRUD.get(db, "text_overrides")
            return json.loads(raw) if raw else {}
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"Could not load text overrides (this is normal on first run): {e}")
        return {}


def _ensure_overrides_loaded(force: bool = False) -> None:
    global _overrides_cache, _overrides_loaded_at
    now = time.time()
    if force or (now - _overrides_loaded_at) > _OVERRIDES_TTL_SECONDS:
        _overrides_cache = _load_overrides_from_db()
        _overrides_loaded_at = now


def refresh_overrides() -> None:
    """Принудительно сбросить кэш - вызывается сразу после сохранения текстов в админке."""
    _ensure_overrides_loaded(force=True)


def _resolve_entry(key: str) -> dict:
    _ensure_overrides_loaded()
    base = TRANSLATIONS.get(key, {})
    override = _overrides_cache.get(key, {})
    # Пустые строки в оверрайде игнорируем, чтобы случайно не затереть текст пустым полем
    merged = dict(base)
    merged.update({k: v for k, v in override.items() if v})
    return merged


def get_text(key: str, language: str = "tg", **kwargs) -> str:
    """
    Получить переведенный текст (с учётом правок из админ-панели)
    
    Args:
        key: ключ перевода
        language: язык (tg или ru)
        **kwargs: параметры для форматирования текста
    
    Returns:
        Переведенный текст
    """
    entry = _resolve_entry(key)
    if not entry:
        return f"[{key}]"

    text = entry.get(language, entry.get("tg", f"[{key}]"))
    
    # Форматирование с параметрами
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text


def get_text_dict(key: str, **kwargs) -> dict:
    """
    Получить словарь переводов (с учётом правок из админ-панели)
    
    Args:
        key: ключ перевода
        **kwargs: параметры для форматирования
    
    Returns:
        Словарь {язык: текст}
    """
    entry = _resolve_entry(key)
    if not entry:
        return {"tg": f"[{key}]", "ru": f"[{key}]"}
    
    result = {}
    for lang, text in entry.items():
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        result[lang] = text
    
    return result