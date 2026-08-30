# ====================================
# TajDonat - User Handlers
# ====================================

import logging
from typing import Optional
from sqlalchemy.orm import Session

from aiogram import types, F, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.models import User
from database.crud import (
    UserCRUD, CategoryCRUD, ProductCRUD, OrderCRUD, PaymentCRUD,
    PaymentMethodCRUD, ReviewCRUD, AdminLogCRUD
)
from translations.texts import get_text
from api.epinby import EpinbyAPI
from config import TELEGRAM_WEBAPP_URL, DEFAULT_CURRENCY

logger = logging.getLogger(__name__)
router = Router()

# ============= FSM STATES =============
class OrderStates(StatesGroup):
    choosing_category = State()
    choosing_product = State()
    entering_quantity = State()
    entering_player_id = State()
    choosing_server = State()
    confirming_order = State()


class TopupStates(StatesGroup):
    choosing_amount = State()
    entering_custom_amount = State()
    choosing_method = State()
    uploading_receipt = State()


# ============= CATALOG HANDLERS =============
@router.message(F.text.contains("📦"))
async def show_catalog(message: types.Message, user: User, db: Session, state: FSMContext):
    """Показать каталог категорий"""
    try:
        if user.is_blocked:
            await message.answer(get_text("error_user_blocked", user.language))
            return
        
        categories = CategoryCRUD.get_all(db)
        
        if not categories:
            await message.answer(get_text("catalog_title", user.language))
            await message.answer(get_text("error_not_found", user.language))
            return
        
        # Создать клавиатуру с категориями
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=category.name_tg if user.language == "tg" else category.name_ru,
                callback_data=f"category_{category.id}"
            )]
            for category in categories
        ])
        
        await message.answer(
            get_text("catalog_title", user.language),
            reply_markup=keyboard
        )
        
        await state.set_state(OrderStates.choosing_category)
    
    except Exception as e:
        logger.error(f"Error in show_catalog: {e}")
        await message.answer(get_text("error_something_wrong", user.language))


@router.callback_query(F.data.startswith("category_"))
async def show_products(callback: types.CallbackQuery, user: User, db: Session, state: FSMContext):
    """Показать товары категории"""
    try:
        category_id = int(callback.data.split("_")[1])
        category = CategoryCRUD.get_by_id(db, category_id)
        
        if not category:
            await callback.answer(get_text("error_not_found", user.language))
            return
        
        products = ProductCRUD.get_by_category(db, category_id)
        
        if not products:
            await callback.answer(get_text("error_not_found", user.language))
            return
        
        # Создать клавиатуру с товарами
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{product.name_tg if user.language == 'tg' else product.name_ru} - {product.price_somoni if user.preferred_currency == 'somoni' else product.price_ruble}{' с' if user.preferred_currency == 'somoni' else '₽'}",
                callback_data=f"product_{product.id}"
            )]
            for product in products
        ])
        
        await callback.message.edit_text(
            get_text("select_product", user.language),
            reply_markup=keyboard
        )
        
        await state.update_data(category_id=category_id)
        await state.set_state(OrderStates.choosing_product)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error in show_products: {e}")
        await callback.answer(get_text("error_something_wrong", user.language))


@router.callback_query(F.data.startswith("product_"))
async def show_product_details(callback: types.CallbackQuery, user: User, db: Session, state: FSMContext):
    """Показать детали товара"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = ProductCRUD.get_by_id(db, product_id)
        
        if not product:
            await callback.answer(get_text("error_not_found", user.language))
            return
        
        # Информация о товаре
        product_name = product.name_tg if user.language == "tg" else product.name_ru
        price = product.price_somoni if user.preferred_currency == "somoni" else product.price_ruble
        currency = "с" if user.preferred_currency == "somoni" else "₽"
        
        product_text = f"""
<b>{product_name}</b>

{get_text("product_price", user.language)}: <b>{price} {currency}</b>
"""
        
        # Если товар требует input (player_id и т.д.)
        if product.epinby_product_type == "TOPUP":
            product_text += f"\n⚠️ {get_text("order_enter_player_id", user.language)}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("btn_confirm", user.language),
                callback_data=f"buy_{product_id}"
            )],
            [InlineKeyboardButton(
                text=get_text("btn_back", user.language),
                callback_data="back_to_products"
            )]
        ])
        
        await callback.message.edit_text(
            product_text,
            reply_markup=keyboard
        )
        
        await state.update_data(product_id=product_id, product=product)
        await state.set_state(OrderStates.choosing_quantity)
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error in show_product_details: {e}")
        await callback.answer(get_text("error_something_wrong", user.language))


@router.callback_query(F.data.startswith("buy_"))
async def buy_product(callback: types.CallbackQuery, user: User, db: Session, state: FSMContext):
    """Начать процесс покупки"""
    try:
        product_id = int(callback.data.split("_")[1])
        product = ProductCRUD.get_by_id(db, product_id)
        
        if not product:
            await callback.answer(get_text("error_not_found", user.language))
            return
        
        data = await state.get_data()
        data["product_id"] = product_id
        data["quantity"] = 1
        
        # Если topup - требуется player_id
        if product.epinby_product_type == "TOPUP":
            await callback.message.edit_text(
                get_text("order_enter_player_id", user.language)
            )
            await state.update_data(**data)
            await state.set_state(OrderStates.entering_player_id)
        else:
            # Voucher - сразу подтверждение
            await confirm_order(callback, user, db, state)
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error in buy_product: {e}")
        await callback.answer(get_text("error_something_wrong", user.language))


@router.message(OrderStates.entering_player_id)
async def process_player_id(message: types.Message, user: User, db: Session, state: FSMContext):
    """Обработать введенный player ID"""
    try:
        player_id = message.text.strip()
        
        if len(player_id) < 2:
            await message.answer(get_text("error_invalid_input", user.language))
            return
        
        data = await state.get_data()
        product = ProductCRUD.get_by_id(db, data["product_id"])
        
        # Валидировать игрока через Epinby
        epinby = EpinbyAPI()
        validation_result = epinby.validate_player(product.epinby_product_id, player_id)
        
        if not validation_result.get("success"):
            await message.answer(get_text("order_player_not_found", user.language))
            return
        
        player_info = validation_result.get("data", {})
        
        # Показать информацию об игроке
        confirm_text = f"""
✅ <b>{player_info.get('player_name', player_id)}</b>

{get_text("order_enter_player_id", user.language)}: {player_id}
{get_text("product_price", user.language)}: <b>{product.price_somoni if user.preferred_currency == 'somoni' else product.price_ruble} {'с' if user.preferred_currency == 'somoni' else '₽'}</b>
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("btn_confirm", user.language),
                callback_data="confirm_order"
            )],
            [InlineKeyboardButton(
                text=get_text("btn_cancel", user.language),
                callback_data="cancel_order"
            )]
        ])
        
        await message.answer(confirm_text, reply_markup=keyboard)
        
        await state.update_data(
            player_id=player_id,
            player_name=player_info.get('player_name'),
            region=player_info.get('region')
        )
        await state.set_state(OrderStates.confirming_order)
    
    except Exception as e:
        logger.error(f"Error in process_player_id: {e}")
        await message.answer(get_text("error_something_wrong", user.language))


async def confirm_order(event, user: User, db: Session, state: FSMContext):
    """Подтвердить заказ"""
    try:
        data = await state.get_data()
        product = ProductCRUD.get_by_id(db, data["product_id"])
        
        if not product:
            return
        
        # Выбрать цену в зависимости от валюты
        if user.preferred_currency == "somoni":
            price = product.price_somoni
        else:
            price = product.price_ruble
        
        # Проверить баланс
        balance = user.balance_somoni if user.preferred_currency == "somoni" else user.balance_ruble
        
        if balance < price:
            await event.message.edit_text(
                get_text("order_insufficient_balance", user.language),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=get_text("button_topup", user.language),
                        callback_data="topup"
                    )]
                ])
            )
            return
        
        # Создать заказ
        order = OrderCRUD.create(
            db,
            user_id=user.id,
            product_id=product.id,
            quantity=data.get("quantity", 1),
            total_price_somoni=price if user.preferred_currency == "somoni" else 0,
            total_price_ruble=price if user.preferred_currency == "ruble" else 0,
            player_id=data.get("player_id"),
            server_id=data.get("server_id")
        )
        
        # Вычесть средства
        if user.preferred_currency == "somoni":
            UserCRUD.subtract_balance(db, user.id, amount_somoni=price)
        else:
            UserCRUD.subtract_balance(db, user.id, amount_ruble=price)
        
        # client_order_id = наш внутренний Order.id - так вебхук от Epinby однозначно
        # сопоставляется с заказом в БД (см. /webhooks/epinbycom в server.py)
        client_order_id = str(order.id)
        OrderCRUD.update(db, order.id, epinby_client_order_id=client_order_id)

        # Отправить заказ в Epinby
        epinby = EpinbyAPI()
        epinby_order = epinby.create_order(
            product_id=product.epinby_product_id,
            qty=data.get("quantity", 1),
            player_id=data.get("player_id"),
            server_id=data.get("server_id"),
            callback_url=f"{TELEGRAM_WEBAPP_URL}/webhooks/epinbycom",
            callback_mode="events",
            idempotency_key=client_order_id,
        )
        
        if epinby_order.get("success"):
            order_id = epinby_order.get("data", {}).get("order_id")
            OrderCRUD.update(db, order.id, epinby_order_id=order_id)
            
            success_text = f"""
✅ <b>{get_text("order_place_success", user.language)}</b>

ID: {order.id}
{get_text("order_status", user.language)}: {get_text(f"order_status_{order.status.lower()}", user.language)}
"""
            await event.message.edit_text(success_text)
        else:
            # Вернуть деньги если ошибка
            if user.preferred_currency == "somoni":
                UserCRUD.add_balance(db, user.id, amount_somoni=price)
            else:
                UserCRUD.add_balance(db, user.id, amount_ruble=price)
            
            await event.message.edit_text(get_text("error_something_wrong", user.language))
        
        await state.clear()
    
    except Exception as e:
        logger.error(f"Error in confirm_order: {e}")


@router.callback_query(F.data == "confirm_order")
async def callback_confirm_order(callback: types.CallbackQuery, user: User, db: Session, state: FSMContext):
    """Callback для подтверждения заказа"""
    await confirm_order(callback, user, db, state)
    await callback.answer()


@router.callback_query(F.data == "cancel_order")
async def callback_cancel_order(callback: types.CallbackQuery, user: User, state: FSMContext):
    """Callback для отмены заказа"""
    await callback.message.delete()
    await state.clear()
    await callback.answer(get_text("btn_cancel", user.language))


# ============= PROFILE HANDLERS =============
@router.message(F.text.contains("👤"))
async def show_profile(message: types.Message, user: User, db: Session):
    """Показать профиль пользователя"""
    try:
        balance = user.balance_somoni if user.preferred_currency == "somoni" else user.balance_ruble
        currency = "с" if user.preferred_currency == "somoni" else "₽"
        language_name = "Тоҷикӣ" if user.language == "tg" else "Русский"

        bot_username = (await message.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref_{user.telegram_id}"
        referrals_count = db.query(User).filter(User.referrer_id == user.id).count()

        profile_text = f"""
<b>👤 {get_text("profile_title", user.language)}</b>

{get_text("profile_user_id", user.language)} {user.telegram_id}
{get_text("profile_username", user.language)} @{user.telegram_username or 'N/A'}
{get_text("profile_phone", user.language)} {user.phone_number or 'N/A'}

{get_text("profile_balance", user.language)} <b>{balance} {currency}</b>
{get_text("profile_language", user.language)} {language_name}

{get_text("profile_referral_bonus", user.language)} {user.referral_bonus} с
{get_text("profile_referral_count", user.language)} {referrals_count}
{get_text("profile_referral_link", user.language)}
<code>{referral_link}</code>
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=get_text("button_topup", user.language),
                callback_data="topup"
            )],
            [InlineKeyboardButton(
                text=get_text("button_language", user.language),
                callback_data="change_language"
            )],
            [InlineKeyboardButton(
                text=get_text("button_currency", user.language),
                callback_data="change_currency"
            )]
        ])
        
        await message.answer(profile_text, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error in show_profile: {e}")
        await message.answer(get_text("error_something_wrong", user.language))


@router.callback_query(F.data == "change_language")
async def callback_change_language(callback: types.CallbackQuery, user: User, db: Session):
    """Callback для смены языка"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="set_lang_tg"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("welcome_select_language", user.language),
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_lang_"))
async def callback_set_language(callback: types.CallbackQuery, user: User, db: Session):
    """Callback для установки языка"""
    language = callback.data.split("_")[2]
    UserCRUD.update(db, user.id, language=language)
    
    await callback.answer(get_text("done", language))
    await callback.message.delete()


@router.callback_query(F.data == "change_currency")
async def callback_change_currency(callback: types.CallbackQuery, user: User, db: Session):
    """Callback для смены валюты"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Сомони (с)", callback_data="set_curr_somoni"),
            InlineKeyboardButton(text="💵 Рубли (₽)", callback_data="set_curr_ruble")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("profile_currency", user.language),
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_curr_"))
async def callback_set_currency(callback: types.CallbackQuery, user: User, db: Session):
    """Callback для установки валюты"""
    currency = callback.data.split("_")[2]
    UserCRUD.update(db, user.id, preferred_currency=currency)
    
    await callback.answer(get_text("done", user.language))
    await callback.message.delete()


# ============= HISTORY HANDLERS =============
PAYMENT_STATUS_KEY = {"PENDING": "topup_waiting_confirmation", "CONFIRMED": "topup_success", "REJECTED": "topup_rejected"}


@router.message(F.text.contains("⏰"))
async def show_history(message: types.Message, user: User, db: Session):
    """Показать историю: и заказы, и пополнения баланса (полная версия - в мини-аппе)"""
    try:
        orders = OrderCRUD.get_by_user(db, user.id, limit=10)
        payments = PaymentCRUD.get_by_user(db, user.id, limit=10)
        currency_symbol = "с" if user.preferred_currency == "somoni" else "₽"

        if not orders and not payments:
            await message.answer(get_text("history_empty", user.language))
            return

        history_text = f"<b>{get_text('history_title', user.language)}</b>\n\n"

        if orders:
            history_text += f"<b>{get_text('history_purchases', user.language)}</b>\n"
            for order in orders:
                status_text = get_text(f"order_status_{order.status.lower()}", user.language)
                product_name = order.product.name_tg if user.language == "tg" else order.product.name_ru
                amount = order.total_price_somoni if user.preferred_currency == "somoni" else order.total_price_ruble
                refund_note = f" (↩ {order.refund_amount_somoni} {currency_symbol})" if order.is_refunded else ""
                history_text += (
                    f"📦 <b>{product_name}</b> — {amount} {currency_symbol}{refund_note}\n"
                    f"{order.created_at.strftime('%d.%m.%Y %H:%M')} · {status_text}\n\n"
                )

        if payments:
            history_text += f"<b>{get_text('history_topups', user.language)}</b>\n"
            for payment in payments:
                status_text = get_text(PAYMENT_STATUS_KEY.get(payment.status, "topup_waiting_confirmation"), user.language)
                amount = payment.amount_somoni or payment.amount_ruble or 0
                history_text += (
                    f"💰 {amount} {currency_symbol}\n"
                    f"{payment.created_at.strftime('%d.%m.%Y %H:%M')} · {status_text}\n\n"
                )

        await message.answer(history_text)

    except Exception as e:
        logger.error(f"Error in show_history: {e}")
        await message.answer(get_text("error_something_wrong", user.language))


# ============= SUPPORT HANDLERS =============
@router.message(F.text.contains("🆘"))
async def show_support(message: types.Message, user: User):
    """Показать поддержку"""
    from config import ADMIN_USERNAME
    
    try:
        support_text = f"""
🆘 <b>{get_text("support_title", user.language)}</b>

{get_text("support_text", user.language)}

<a href="https://t.me/{ADMIN_USERNAME}">📞 @{ADMIN_USERNAME}</a>
"""
        
        await message.answer(support_text)
    
    except Exception as e:
        logger.error(f"Error in show_support: {e}")
        await message.answer(get_text("error_something_wrong", user.language))


# ============= BACK BUTTON =============
@router.message(F.text.contains("◀️"))
async def go_back(message: types.Message, user: User):
    """Обработчик кнопки назад"""
    from bot import get_main_menu_keyboard
    
    try:
        await message.answer(
            get_text("welcome_title", user.language),
            reply_markup=await get_main_menu_keyboard(user.language)
        )
    except Exception as e:
        logger.error(f"Error in go_back: {e}")