# ====================================
# TajDonat - Telegram Bot Main
# ====================================

import logging
import asyncio
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import (
    TELEGRAM_BOT_TOKEN, DATABASE_URL, LOG_LEVEL, LOG_FILE,
    TELEGRAM_WEBAPP_URL, DEFAULT_LANGUAGE, ADMIN_USERNAME, ADMIN_USER_ID
)
from database.models import Base
from database.crud import UserCRUD, SettingsCRUD

# ============= LOGGING SETUP =============
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============= DATABASE SETUP =============
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создать таблицы если их нет
Base.metadata.create_all(bind=engine)
logger.info("Database tables created/checked")

# ============= AIOGRAM SETUP =============
bot = Bot(token=TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


# ============= DEPENDENCY INJECTION =============
def get_db() -> Session:
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Error getting DB session: {e}")
        db.close()
        raise


# ============= MIDDLEWARE =============
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Any, Awaitable

class DatabaseMiddleware(BaseMiddleware):
    """Middleware для добавления БД в контекст"""
    
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        db = SessionLocal()
        data["db"] = db
        try:
            result = await handler(event, data)
        finally:
            db.close()
        return result


class UserMiddleware(BaseMiddleware):
    """Middleware для автоматического создания/обновления пользователя"""
    
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        db = data.get("db")
        
        # Определить источник (Message или CallbackQuery)
        referrer_telegram_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username
            # Реферальная ссылка вида https://t.me/<bot>?start=ref_123456 приходит
            # ботy как текст "/start ref_123456" — раньше это нигде не парсилось,
            # поэтому referrer_id ни у кого никогда не сохранялся
            if event.text and event.text.startswith("/start"):
                parts = event.text.split(maxsplit=1)
                if len(parts) > 1 and parts[1].startswith("ref_"):
                    try:
                        referrer_telegram_id = int(parts[1][len("ref_"):])
                    except ValueError:
                        referrer_telegram_id = None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username
        else:
            return await handler(event, data)
        
        # Создать или получить пользователя
        if db:
            user = UserCRUD.get_or_create(db, user_id, username, referrer_telegram_id=referrer_telegram_id)
            data["user"] = user
            UserCRUD.update_last_activity(db, user.id)
        
        return await handler(event, data)


# Регистрировать middleware
dp.message.middleware(DatabaseMiddleware())
dp.callback_query.middleware(DatabaseMiddleware())
dp.message.middleware(UserMiddleware())
dp.callback_query.middleware(UserMiddleware())


# ============= COMMAND HANDLERS =============
@dp.message(Command("start"))
async def cmd_start(message: Message, db: Session, user: 'User'):
    """Обработчик команды /start"""
    from translations.texts import get_text
    
    try:
        if user.is_blocked:
            await message.answer(get_text("error_user_blocked", user.language))
            return
        
        # Приветствие
        welcome_text = get_text("welcome_title", user.language)
        description = get_text("welcome_description", user.language)
        
        await message.answer(
            f"{welcome_text}\n\n{description}",
            reply_markup=await get_main_menu_keyboard(user.language)
        )
        
        logger.info(f"User {user.telegram_id} started bot")
    
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")
        await message.answer(get_text("error_something_wrong", user.language))


@dp.message(Command("help"))
async def cmd_help(message: Message, user: 'User'):
    """Обработчик команды /help"""
    from translations.texts import get_text
    
    try:
        help_text = f"""
🆘 <b>{get_text("support_title", user.language)}</b>

{get_text("support_text", user.language)}

📞 @{ADMIN_USERNAME}
"""
        await message.answer(help_text, reply_markup=await get_back_button(user.language))
    
    except Exception as e:
        logger.error(f"Error in cmd_help: {e}")


@dp.message(Command("admin"))
async def cmd_admin(message: Message, user: 'User', db: Session):
    """Обработчик команды /admin (вход в админ-панель)"""
    from translations.texts import get_text
    
    try:
        # Проверить является ли админом
        if not user.is_admin:
            await message.answer(get_text("error_access_denied", user.language))
            return
        
        # Открыть админ-панель как веб-приложение
        # (маршрут на сервере — GET /admin, см. server.py; /admin/dashboard там не существует)
        admin_keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(
                    text="📊 " + get_text("admin_dashboard", user.language),
                    web_app=types.WebAppInfo(url=f"{TELEGRAM_WEBAPP_URL}/admin")
                )]
            ]
        )
        
        await message.answer(
            get_text("admin_title", user.language),
            reply_markup=admin_keyboard
        )
    
    except Exception as e:
        logger.error(f"Error in cmd_admin: {e}")


@dp.message(Command("stats"))
async def cmd_stats(message: Message, user: 'User', db: Session):
    """Обработчик команды /stats (статистика для админа)"""
    from translations.texts import get_text
    from database.crud import UserCRUD, OrderCRUD
    
    try:
        if not user.is_admin:
            await message.answer(get_text("error_access_denied", user.language))
            return
        
        # Собрать статистику
        total_users = UserCRUD.get_total_count(db)
        total_orders = OrderCRUD.get_total_count(db)
        recent_orders = OrderCRUD.get_recent_orders(db, days=7)
        
        stats_text = f"""
📊 <b>{get_text("admin_dashboard", user.language)}</b>

👥 {get_text("stats_total_users", user.language)} {total_users}
🛒 {get_text("stats_total_orders", user.language)} {total_orders}
📅 {get_text("stats_weekly_orders", user.language)} {len(recent_orders)}
"""
        
        await message.answer(stats_text)
    
    except Exception as e:
        logger.error(f"Error in cmd_stats: {e}")
        await message.answer(get_text("error_something_wrong", user.language))


@dp.message(Command("language"))
async def cmd_language(message: Message, user: 'User'):
    """Обработчик команды /language (смена языка)"""
    from translations.texts import get_text
    
    try:
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tg"),
                    types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
                ]
            ]
        )
        
        await message.answer(
            get_text("welcome_select_language", user.language),
            reply_markup=keyboard
        )
    
    except Exception as e:
        logger.error(f"Error in cmd_language: {e}")


# ============= CALLBACK HANDLERS =============
@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def callback_change_language(callback: types.CallbackQuery, user: 'User', db: Session):
    """Обработчик переключения языка"""
    from translations.texts import get_text
    
    try:
        language = callback.data.split("_")[1]
        
        # Обновить язык пользователя
        UserCRUD.update(db, user.id, language=language)
        user.language = language
        
        await callback.answer(get_text("done", language))
        await callback.message.edit_text(
            get_text("welcome_title", language),
            reply_markup=await get_main_menu_keyboard(language)
        )
    
    except Exception as e:
        logger.error(f"Error in callback_change_language: {e}")
        await callback.answer("❌ " + get_text("error_something_wrong", user.language))


# ============= KEYBOARD FUNCTIONS =============
async def get_main_menu_keyboard(language: str = DEFAULT_LANGUAGE):
    """Получить главное меню"""
    from translations.texts import get_text
    
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=get_text("menu_catalog", language))],
            [types.KeyboardButton(text=get_text("menu_history", language))],
            [
                types.KeyboardButton(text=get_text("menu_profile", language)),
                types.KeyboardButton(text=get_text("menu_support", language))
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )


async def get_back_button(language: str = DEFAULT_LANGUAGE):
    """Получить кнопку назад"""
    from translations.texts import get_text
    
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=get_text("btn_back", language))]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


# ============= BOT SETUP =============
async def set_default_commands(bot: Bot):
    """Установить список команд бота"""
    commands = [
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Get help"),
        BotCommand(command="language", description="Change language"),
        BotCommand(command="admin", description="Admin panel (admin only)"),
        BotCommand(command="stats", description="Statistics (admin only)"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
    logger.info("Bot commands set")


async def set_menu_button(bot: Bot):
    """
    Установить постоянную кнопку "Меню" (слева от поля ввода) как кнопку открытия
    Mini App. Без этого обычный пользователь физически не может открыть index.html —
    все текстовые кнопки главного меню (Каталог/Профил и т.д.) работают только как
    обычные чат-хендлеры внутри user_handlers.py, а не открывают веб-интерфейс.
    """
    await bot.set_chat_menu_button(
        menu_button=types.MenuButtonWebApp(
            text="🛍 Каталог",
            web_app=types.WebAppInfo(url=TELEGRAM_WEBAPP_URL)
        )
    )
    logger.info("Menu button (Mini App launcher) set")


async def on_startup(bot: Bot):
    """Обработчик запуска бота"""
    try:
        await set_default_commands(bot)
        await set_menu_button(bot)
        logger.info("Bot started successfully")
        
        # Проверить Epinby API
        from api.epinby import EpinbyAPI
        epinby = EpinbyAPI()
        response = epinby.get_me()
        if response.get("success"):
            logger.info("Epinby API connected successfully")
        else:
            logger.warning(f"Epinby API error: {response}")
    
    except Exception as e:
        logger.error(f"Error during startup: {e}")


async def on_shutdown(bot: Bot):
    """Обработчик остановки бота"""
    logger.info("Bot shutdown")
    await bot.session.close()


# ============= MAIN FUNCTION =============
async def main():
    """Главная функция для запуска бота"""
    try:
        logger.info("Starting TajDonat bot...")
        
        # Регистрировать команды, кнопку меню (Mini App) и проверить Epinby API
        # (раньше on_startup() был определён, но нигде не вызывался — команды
        # регистрировались, а кнопка меню и проверка Epinby — нет)
        await on_startup(bot)
        
        # Запустить polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated")