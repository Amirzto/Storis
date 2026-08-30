# ====================================
# TajDonater - Mini App Backend Server
# (User Mini App API + Admin Panel API)
# ====================================

import os
import sys
import hmac
import hashlib
import json
import logging
import shutil
import secrets
from datetime import datetime, timedelta
from urllib.parse import parse_qsl
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from aiogram import Bot

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    TELEGRAM_BOT_TOKEN, DATABASE_URL, RECEIPTS_DIR, ADMIN_GROUP_CHAT_ID,
    SALES_CHANNEL_ID, REFERRAL_BONUS_PERCENT, MIN_BALANCE_TOPUP, MAX_BALANCE_TOPUP,
    ADMIN_USER_ID, ADMIN_PASSWORD, UPLOADS_DIR, CATEGORIES_IMAGES_DIR,
    PRODUCTS_IMAGES_DIR, WEEKLY_STATS_DAYS, TELEGRAM_WEBAPP_URL
)
from database.models import Base, User, Order, Payment
from database.crud import (
    UserCRUD, CategoryCRUD, ProductCRUD, OrderCRUD, PaymentCRUD,
    PaymentMethodCRUD, ReviewCRUD, SettingsCRUD, AdminLogCRUD
)
from api.epinby import EpinbyAPI, EpinbyWebhookHandler
from translations.texts import get_text, refresh_overrides as refresh_text_overrides

logger = logging.getLogger(__name__)

# ============= APP SETUP =============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(title="TajDonater Mini App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# ============= DATABASE =============
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============= TELEGRAM INIT DATA VALIDATION =============
def validate_telegram_init_data(init_data: str) -> Optional[dict]:
    """Проверить подпись initData от Telegram WebApp и вернуть данные пользователя"""
    if not init_data:
        return None
    try:
        parsed = dict(parse_qsl(init_data))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return None

        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            logger.warning("Invalid Telegram initData signature")
            return None

        user_json = parsed.get("user")
        if user_json:
            return json.loads(user_json)
        return None
    except Exception as e:
        logger.error(f"Error validating initData: {e}")
        return None


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Получить текущего пользователя из Telegram initData (dependency)"""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    tg_user = validate_telegram_init_data(init_data)

    # Fallback for local dev/testing without valid Telegram signature
    if not tg_user:
        if os.getenv("DEBUG_ALLOW_UNSIGNED", "false").lower() == "true":
            tg_user = {"id": ADMIN_USER_ID, "username": "dev_user"}
        else:
            raise HTTPException(status_code=401, detail="Invalid or missing Telegram init data")

    user = UserCRUD.get_or_create(db, tg_user["id"], tg_user.get("username"))

    # Владелец бота всегда админ, даже при первом заходе
    if user.telegram_id == ADMIN_USER_ID and not user.is_admin:
        user = UserCRUD.update(db, user.id, is_admin=True)

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")
    UserCRUD.update_last_activity(db, user.id)
    return user


# ============= ADMIN SESSION (in-memory tokens) =============
_admin_sessions: dict[str, dict] = {}
ADMIN_SESSION_TTL = timedelta(hours=12)


def _create_admin_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _admin_sessions[token] = {"user_id": user_id, "expires_at": datetime.utcnow() + ADMIN_SESSION_TTL}
    return token


async def get_current_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """Проверить X-Admin-Token и вернуть админа. Требует предварительного /api/admin/login"""
    token = request.headers.get("X-Admin-Token", "")
    session = _admin_sessions.get(token)
    if not session or session["expires_at"] < datetime.utcnow():
        _admin_sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Admin session expired, please login again")

    admin = UserCRUD.get_by_id(db, session["user_id"])
    if not admin or not admin.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return admin


def get_admin_password(db: Session) -> str:
    stored = SettingsCRUD.get(db, "admin_password")
    return stored if stored else ADMIN_PASSWORD


async def notify_admin_group(db: Session, text: str):
    chat_id = SettingsCRUD.get(db, "admin_group_chat_id") or ADMIN_GROUP_CHAT_ID
    if not chat_id:
        return
    try:
        await bot.send_message(chat_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify admin group: {e}")


def get_sales_channel_id(db: Session):
    return SettingsCRUD.get(db, "sales_channel_id") or SALES_CHANNEL_ID


ORDER_STATUS_EMOJI = {
    "PENDING": "⏳", "PROCESSING": "⚙️", "COMPLETED": "✅",
    "FAILED": "❌", "CANCELED": "❌", "PARTIAL": "⚠️",
}


def build_sales_channel_text(order: Order) -> str:
    emoji = ORDER_STATUS_EMOJI.get(order.status, "🛒")
    product_name = order.product.name_ru if order.product else "Товар"
    return (
        f"{emoji} <b>Заказ #{order.id}</b>\n"
        f"🎮 {product_name}\n"
        f"💵 Сумма: {order.total_price_somoni} сомони\n"
        f"📌 Статус: {order.status}"
    )


async def post_order_to_sales_channel(db: Session, order: Order):
    """Опубликовать/обновить пост о заказе в публичном канале продаж"""
    channel_id = get_sales_channel_id(db)
    if not channel_id:
        return
    try:
        if order.channel_message_id:
            await bot.edit_message_text(
                chat_id=channel_id, message_id=order.channel_message_id,
                text=build_sales_channel_text(order), parse_mode="HTML",
            )
        else:
            msg = await bot.send_message(channel_id, build_sales_channel_text(order), parse_mode="HTML")
            OrderCRUD.update(db, order.id, channel_message_id=msg.message_id)
    except Exception as e:
        logger.error(f"Failed to post/update sales channel message for order {order.id}: {e}")


async def notify_user_order_status(user: User, order: Order):
    """Уведомить пользователя в боте об изменении статуса его заказа"""
    lang = user.language or "tg"
    product_name = (order.product.name_ru if lang == "ru" else order.product.name_tg) if order.product else ""

    if order.status == "COMPLETED":
        codes = "\n".join(f"🔑 <code>{c}</code>" for c in (order.delivery_data or []))
        text = (
            f"✅ Заказ #{order.id} ({product_name}) выполнен!" + (f"\n\n{codes}" if codes else "")
            if lang == "ru" else
            f"✅ Суратҳисоб #{order.id} ({product_name}) иҷро шуд!" + (f"\n\n{codes}" if codes else "")
        )
    elif order.status in ("FAILED", "CANCELED"):
        text = (
            f"❌ Заказ #{order.id} ({product_name}) не выполнен. Средства ({order.refund_amount_somoni} сомони) возвращены на баланс."
            if lang == "ru" else
            f"❌ Суратҳисоб #{order.id} ({product_name}) иҷро нашуд. Маблағ ({order.refund_amount_somoni} сомонӣ) ба баланс баргардонида шуд."
        )
    elif order.status == "PARTIAL":
        text = (
            f"⚠️ Заказ #{order.id} ({product_name}) выполнен частично. Разница ({order.refund_amount_somoni} сомони) возвращена на баланс."
            if lang == "ru" else
            f"⚠️ Суратҳисоб #{order.id} ({product_name}) қисман иҷро шуд. Фарқ ({order.refund_amount_somoni} сомонӣ) ба баланс баргардонида шуд."
        )
    elif order.status == "PROCESSING":
        text = (f"⚙️ Заказ #{order.id} ({product_name}) в обработке..." if lang == "ru"
                else f"⚙️ Суратҳисоб #{order.id} ({product_name}) дар ҳоли иҷрост...")
    else:
        return

    try:
        await bot.send_message(user.telegram_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to notify user {user.telegram_id} about order {order.id}: {e}")


def save_upload(upload_file: UploadFile, directory: str, prefix: str) -> str:
    """Сохранить загруженное изображение, вернуть публичный /uploads/... путь"""
    ext = os.path.splitext(upload_file.filename or "")[1] or ".jpg"
    filename = f"{prefix}_{int(datetime.utcnow().timestamp() * 1000)}{ext}"
    filepath = os.path.join(directory, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    rel = os.path.relpath(filepath, UPLOADS_DIR).replace("\\", "/")
    return f"/uploads/{rel}"


# ============= SERIALIZERS =============
def serialize_user(u: User) -> dict:
    spent = sum(o.total_price_somoni for o in u.orders if o.status == "COMPLETED")
    return {
        "id": u.id,
        "telegram_id": u.telegram_id,
        "telegram_username": u.telegram_username,
        "phone_number": u.phone_number,
        "balance_somoni": u.balance_somoni,
        "balance_ruble": u.balance_ruble,
        "language": u.language,
        "preferred_currency": u.preferred_currency,
        "is_blocked": u.is_blocked,
        "is_admin": u.is_admin,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_activity": u.last_activity.isoformat() if u.last_activity else None,
        "total_spent": spent,
    }


def serialize_category(c, admin: bool = False) -> dict:
    data = {
        "id": c.id, "name_tg": c.name_tg, "name_ru": c.name_ru,
        "image_url": c.image_url, "sort_order": c.sort_order,
    }
    if admin:
        data["is_active"] = c.is_active
    return data


def serialize_product(p, admin: bool = False) -> dict:
    data = {
        "id": p.id, "category_id": p.category_id,
        "name_tg": p.name_tg, "name_ru": p.name_ru,
        "price_somoni": p.price_somoni, "price_ruble": p.price_ruble,
        "epinby_product_id": p.epinby_product_id, "epinby_product_type": p.epinby_product_type,
        "image_url": p.image_url, "variants": p.variants,
    }
    if admin:
        data["is_active"] = p.is_active
        data["sort_order"] = p.sort_order
    return data


def serialize_order(o) -> dict:
    return {
        "id": o.id, "status": o.status,
        "user_telegram_id": o.user.telegram_id if o.user else None,
        "user_username": o.user.telegram_username if o.user else None,
        "product_name_tg": o.product.name_tg if o.product else None,
        "product_name_ru": o.product.name_ru if o.product else None,
        "total_price_somoni": o.total_price_somoni, "total_price_ruble": o.total_price_ruble,
        "player_id": o.player_id, "player_name": o.player_name,
        "is_refunded": o.is_refunded,
        "created_at": o.created_at.isoformat(), "completed_at": o.completed_at.isoformat() if o.completed_at else None,
    }


def serialize_payment(p, admin: bool = False) -> dict:
    data = {
        "id": p.id, "status": p.status,
        "amount_somoni": p.amount_somoni, "amount_ruble": p.amount_ruble,
        "currency": p.currency, "payment_method": p.payment_method,
        "created_at": p.created_at.isoformat(),
    }
    if admin:
        data["user_telegram_id"] = p.user.telegram_id if p.user else None
        data["user_username"] = p.user.telegram_username if p.user else None
        data["receipt_url"] = f"/api/admin/payments/{p.id}/receipt" if p.receipt_image_path else None
        data["admin_note"] = p.admin_note
    return data


def serialize_payment_method(m) -> dict:
    return {
        "id": m.id, "name_tg": m.name_tg, "name_ru": m.name_ru,
        "account_number": m.account_number, "phone_number": m.phone_number,
        "full_name": m.full_name, "image_url": m.image_url,
        "is_active": getattr(m, "is_active", True),
    }


def serialize_review(r) -> dict:
    return {
        "id": r.id, "author_name": r.author_name, "rating": r.rating,
        "text_tg": r.text_tg, "text_ru": r.text_ru,
        "is_approved": r.is_approved,
        "created_at": r.created_at.isoformat(),
    }


# ============= ROUTES: FRONTEND =============
@app.get("/")
async def index():
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))


@app.get("/admin")
async def admin_index():
    return FileResponse(os.path.join(BASE_DIR, "templates", "admin.html"))


# ============= API: USER =============
@app.get("/api/user")
async def api_get_user(user: User = Depends(get_current_user)):
    return {"success": True, "data": serialize_user(user)}


@app.post("/api/user/language")
async def api_set_language(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    body = await request.json()
    language = body.get("language", "tg")
    UserCRUD.update(db, user.id, language=language)
    return {"success": True}


# ============= API: CATEGORIES =============
@app.get("/api/categories")
async def api_get_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    categories = CategoryCRUD.get_all(db)
    return {"success": True, "data": [serialize_category(c) for c in categories]}


# ============= API: PRODUCTS =============
@app.get("/api/products")
async def api_get_products(category_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    products = ProductCRUD.get_by_category(db, category_id)
    return {"success": True, "data": [serialize_product(p) for p in products]}


# ============= API: VALIDATE PLAYER =============
@app.post("/api/validate-player")
async def api_validate_player(request: Request, user: User = Depends(get_current_user)):
    body = await request.json()
    epinby = EpinbyAPI()
    result = epinby.validate_player(
        product_id=body.get("product_id"),
        player_id=body.get("player_id"),
        server_id=body.get("server_id"),
    )
    if not result.get("success"):
        error = result.get("error", {}) or {}
        status_code = error.get("status_code")
        if status_code is not None and 400 <= status_code < 500:
            # Epinby ответил клиентской ошибкой -> практически всегда значит,
            # что такого игрока/ID не существует, а не техническая проблема
            raise HTTPException(status_code=404, detail="PLAYER_NOT_FOUND")
        raise HTTPException(status_code=400, detail=error.get("message", "Validation failed"))
    return {"success": True, "data": result.get("data")}


# ============= API: ORDERS =============
@app.post("/api/orders")
async def api_create_order(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    body = await request.json()
    product = ProductCRUD.get_by_id(db, body.get("product_id"))
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Если у товара есть варианты по региону, использовать epinby_product_id этого варианта
    epinby_product_id = product.epinby_product_id
    # Фронтенд (app.js) отправляет ключ "variant"; принимаем и "region" для обратной совместимости
    region = body.get("variant") or body.get("region")
    if product.variants and region and region in product.variants:
        epinby_product_id = product.variants[region].get("epinby_product_id", epinby_product_id)

    if user.balance_somoni < product.price_somoni:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Списать средства
    ok = UserCRUD.subtract_balance(db, user.id, amount_somoni=product.price_somoni)
    if not ok:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    order = OrderCRUD.create(
        db, user_id=user.id, product_id=product.id, quantity=body.get("quantity", 1),
        total_price_somoni=product.price_somoni, total_price_ruble=product.price_ruble,
        player_id=body.get("player_id"), server_id=body.get("server_id"),
    )
    if region:
        OrderCRUD.update(db, order.id, selected_variant=region)

    # client_order_id = наш собственный Order.id: так вебхук от Epinby можно однозначно
    # сопоставить с заказом в нашей БД без гадания по epinby_order_id
    client_order_id = str(order.id)
    OrderCRUD.update(db, order.id, epinby_client_order_id=client_order_id)

    # Создать заказ в Epinby
    epinby = EpinbyAPI()
    result = epinby.create_order(
        product_id=epinby_product_id,
        qty=body.get("quantity", 1),
        player_id=body.get("player_id"),
        server_id=body.get("server_id"),
        callback_url=f"{TELEGRAM_WEBAPP_URL}/webhooks/epinbycom",
        callback_mode="events",
        idempotency_key=client_order_id,
    )

    if result.get("success"):
        data = result["data"]
        OrderCRUD.update(
            db, order.id,
            epinby_order_id=data.get("order_id"),
            status=data.get("status", "PENDING"),
            player_name=(data.get("player") or {}).get("player_name"),
            region=(data.get("player") or {}).get("region"),
        )
    else:
        # Ошибка создания заказа -> вернуть деньги
        UserCRUD.add_balance(db, user.id, amount_somoni=product.price_somoni)
        OrderCRUD.update_status(db, order.id, "FAILED", message=str(result.get("error")))
        error = result.get("error", {})
        raise HTTPException(status_code=400, detail=error.get("message", "Order creation failed"))

    db.refresh(order)
    await post_order_to_sales_channel(db, order)
    return {"success": True, "data": serialize_order(order)}


@app.get("/api/orders")
async def api_get_orders(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = OrderCRUD.get_by_user(db, user.id)
    return {"success": True, "data": [serialize_order(o) for o in orders]}


# ============= API: PAYMENT METHODS =============
@app.get("/api/payment-methods")
async def api_get_payment_methods(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    methods = PaymentMethodCRUD.get_all(db)
    return {"success": True, "data": [serialize_payment_method(m) for m in methods]}


# ============= API: PAYMENTS (TOPUP) =============
@app.get("/api/payments")
async def api_get_payments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payments = PaymentCRUD.get_by_user(db, user.id)
    return {"success": True, "data": [serialize_payment(p) for p in payments]}


@app.post("/api/payments")
async def api_create_payment(
    amount_somoni: float = Form(...),
    payment_method_id: int = Form(...),
    receipt: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if amount_somoni < MIN_BALANCE_TOPUP or amount_somoni > MAX_BALANCE_TOPUP:
        raise HTTPException(status_code=400, detail="Invalid amount")

    method = PaymentMethodCRUD.get_by_id(db, payment_method_id)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")

    filepath_url = save_upload(receipt, RECEIPTS_DIR, f"receipt_{user.id}")
    filepath_abs = os.path.join(UPLOADS_DIR, filepath_url.replace("/uploads/", ""))

    payment = PaymentCRUD.create(
        db, user_id=user.id, amount_somoni=amount_somoni, currency="somoni",
        payment_method=method.name_tg,
    )
    PaymentCRUD.update(db, payment.id, receipt_image_path=filepath_abs)

    # Уведомить группу админов о новом пополнении
    text = (
        "💰 <b>Новое пополнение баланса</b>\n\n"
        f"👤 Пользователь: @{user.telegram_username or 'N/A'} (ID: {user.telegram_id})\n"
        f"💵 Сумма: {amount_somoni} сомони\n"
        f"🆔 ID платежа: {payment.id}\n\n"
        f"Откройте админ-панель для подтверждения/отклонения."
    )
    await notify_admin_group(db, text)

    return {"success": True, "data": serialize_payment(payment)}


# ============= API: REVIEWS =============
@app.get("/api/reviews")
async def api_get_reviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reviews = ReviewCRUD.get_all(db)
    average = ReviewCRUD.get_average_rating(db)
    data = [{
        "id": r.id, "author_name": r.author_name, "rating": r.rating,
        "text_tg": r.text_tg, "text_ru": r.text_ru, "created_at": r.created_at.isoformat(),
    } for r in reviews]
    return {"success": True, "data": {"reviews": data, "average": round(average, 1), "total": len(data)}}


# ============= API: REFERRALS =============
@app.get("/api/referrals")
async def api_get_referrals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    referrals = db.query(User).filter(User.referrer_id == user.id).all()
    data = [{
        "telegram_id": r.telegram_id, "telegram_username": r.telegram_username,
        "created_at": r.created_at.isoformat(),
    } for r in referrals]
    return {"success": True, "data": {"referrals": data}}


# ============= HEALTH CHECK =============
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ============= EPINBY WEBHOOK =============
@app.post("/webhooks/epinbycom")
async def epinby_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Приём вебхуков от Epinby (callback_mode=events): PENDING/PROCESSING/COMPLETED/FAILED/PARTIAL.
    Подпись проверяется через X-GAMEX-Signature (HMAC SHA-256, секрет из /getMe = EPINBY_WEBHOOK_SECRET).
    """
    raw_body = await request.body()
    signature = request.headers.get("X-GAMEX-Signature", "")

    if not EpinbyAPI.verify_webhook_signature(raw_body, signature):
        logger.warning("Rejected Epinby webhook: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = EpinbyAPI.parse_webhook_payload(raw_body.decode("utf-8"))

    handler = EpinbyWebhookHandler(db)
    order = handler.handle_order_webhook(payload)

    if order:
        db.refresh(order)
        await post_order_to_sales_channel(db, order)
        user = UserCRUD.get_by_id(db, order.user_id)
        if user:
            await notify_user_order_status(user, order)

    # Epinby ожидает быстрый 2xx-ответ и допускает повторные доставки.
    # 204 No Content по HTTP-спецификации не должен иметь тела — JSONResponse(content=None)
    # сериализовал бы литерал "null" в тело ответа, что не по стандарту.
    return Response(status_code=204)


# ====================================================================
# ============================ ADMIN API ============================
# ====================================================================

@app.post("/api/admin/login")
async def api_admin_login(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Вход в админ-панель: пользователь уже опознан по Telegram initData, дополнительно нужен пароль"""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")

    body = await request.json()
    password = body.get("password", "")
    if password != get_admin_password(db):
        raise HTTPException(status_code=401, detail="Wrong password")

    token = _create_admin_session(user.id)
    return {"success": True, "data": {"token": token, "admin": serialize_user(user)}}


@app.get("/api/admin/me")
async def api_admin_me(admin: User = Depends(get_current_admin)):
    return {"success": True, "data": serialize_user(admin)}


@app.post("/api/admin/change-password")
async def api_admin_change_password(request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    body = await request.json()
    new_password = (body.get("new_password") or "").strip()
    if len(new_password) < 4:
        raise HTTPException(status_code=400, detail="Password too short (min 4 chars)")
    SettingsCRUD.set(db, "admin_password", new_password)
    AdminLogCRUD.create(db, admin_id=admin.id, action="change_admin_password")
    return {"success": True}


# ---------- STATISTICS ----------
@app.get("/api/admin/stats")
async def api_admin_stats(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    total_users = UserCRUD.get_total_count(db)
    total_orders = OrderCRUD.get_total_count(db)
    weekly_orders = OrderCRUD.get_recent_orders(db, days=WEEKLY_STATS_DAYS)
    total_topups = db.query(Payment).filter(Payment.status == "CONFIRMED").count()
    total_topup_amount = sum(p.amount_somoni or 0 for p in db.query(Payment).filter(Payment.status == "CONFIRMED").all())
    total_spent = sum(o.total_price_somoni for o in db.query(Order).filter(Order.status == "COMPLETED").all())
    pending_payments = len(PaymentCRUD.get_pending(db))
    blocked_users = db.query(User).filter(User.is_blocked == True).count()

    return {"success": True, "data": {
        "total_users": total_users,
        "blocked_users": blocked_users,
        "total_orders": total_orders,
        "weekly_orders_count": len(weekly_orders),
        "total_topups_confirmed": total_topups,
        "total_topup_amount_somoni": round(total_topup_amount, 2),
        "total_spent_somoni": round(total_spent, 2),
        "pending_payments": pending_payments,
    }}


# ---------- CATEGORIES ----------
@app.get("/api/admin/categories")
async def api_admin_get_categories(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """В отличие от публичного /api/categories, здесь видны и неактивные категории"""
    from database.models import Category
    categories = db.query(Category).order_by(Category.sort_order).all()
    return {"success": True, "data": [serialize_category(c, admin=True) for c in categories]}


@app.post("/api/admin/categories")
async def api_admin_create_category(
    name_tg: str = Form(...),
    name_ru: str = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    category = CategoryCRUD.create(db, name_tg=name_tg, name_ru=name_ru)
    if image is not None and image.filename:
        image_url = save_upload(image, CATEGORIES_IMAGES_DIR, f"category_{category.id}")
        category = CategoryCRUD.update(db, category.id, image_url=image_url, image_path=image_url)
    AdminLogCRUD.create(db, admin_id=admin.id, action="add_category", target_type="category", target_id=category.id)
    return {"success": True, "data": serialize_category(category, admin=True)}


@app.put("/api/admin/categories/{category_id}")
async def api_admin_update_category(
    category_id: int,
    name_tg: str = Form(None),
    name_ru: str = Form(None),
    is_active: bool = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    updates = {}
    if name_tg is not None:
        updates["name_tg"] = name_tg
    if name_ru is not None:
        updates["name_ru"] = name_ru
    if is_active is not None:
        updates["is_active"] = is_active
    if image is not None and image.filename:
        updates["image_url"] = save_upload(image, CATEGORIES_IMAGES_DIR, f"category_{category_id}")

    category = CategoryCRUD.update(db, category_id, **updates)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="edit_category", target_type="category", target_id=category_id, details=updates if "image_url" not in updates else {k: v for k, v in updates.items() if k != "image_url"})
    return {"success": True, "data": serialize_category(category, admin=True)}


@app.delete("/api/admin/categories/{category_id}")
async def api_admin_delete_category(category_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    ok = CategoryCRUD.delete(db, category_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Category not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="delete_category", target_type="category", target_id=category_id)
    return {"success": True}


# ---------- PRODUCTS ----------
@app.get("/api/admin/products")
async def api_admin_get_products(category_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    products = ProductCRUD.get_by_category(db, category_id)
    return {"success": True, "data": [serialize_product(p, admin=True) for p in products]}


@app.get("/api/admin/epinby-games")
async def api_admin_epinby_games(admin: User = Depends(get_current_admin)):
    """
    Список игр из каталога Epinby — нужен для фильтра в окне импорта товара
    (см. /api/admin/epinby-products). Раньше такого способа не было вообще:
    товар добавлялся только вручную, поле за полем, включая Epinby ID вслепую.
    """
    epinby = EpinbyAPI()
    result = epinby.get_games()
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=(result.get("error") or {}).get("message", "Epinby error"))
    games = result.get("data")
    if games is None:
        games = result.get("games", [])
    return {"success": True, "data": games}


@app.get("/api/admin/epinby-products")
async def api_admin_epinby_products(
    game_id: int = None,
    type: str = None,
    search: str = None,
    page: int = 1,
    admin: User = Depends(get_current_admin),
):
    """
    Каталог товаров поставщика (Epinby) для импорта в товар мини-аппа.
    Админ выбирает товар из списка на сайте поставщика — Epinby ID, картинка
    и тип (ваучер/пополнение) подставляются автоматически; вручную в модалке
    остаётся ввести только СВОЁ название (tg/ru) и цену для покупателя —
    так, как и просили изначально.

    ВАЖНО: точные названия полей в ответе Epinby (`/products`) нигде в проекте
    не задокументированы, поэтому ниже — защитный разбор с несколькими вариантами
    ключей (name/title, image/image_url/icon и т.д.). Если после первого реального
    запроса что-то не подтянется (например картинка), смотри в логи сервера —
    строка "Epinby products sample keys" покажет реальные ключи первого товара,
    и pick(...) ниже нужно будет дополнить нужным ключом.
    """
    epinby = EpinbyAPI()
    result = epinby.get_products(type=type, game_id=game_id, page=page, per_page=100)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=(result.get("error") or {}).get("message", "Epinby error"))

    raw_items = result.get("data")
    if raw_items is None:
        raw_items = result.get("products", [])
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("items") or raw_items.get("data") or []

    if raw_items and isinstance(raw_items[0], dict):
        logger.info(f"Epinby products sample keys: {list(raw_items[0].keys())}")

    def pick(item, *keys, default=None):
        for k in keys:
            v = item.get(k)
            if v not in (None, ""):
                return v
        return default

    normalized = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        name = pick(item, "name", "title", "product_name")
        if search and search.lower() not in str(name or "").lower():
            continue
        normalized.append({
            "epinby_product_id": pick(item, "id", "product_id"),
            "name": name,
            "image_url": pick(item, "image", "image_url", "icon", "logo"),
            "type": (pick(item, "type", "product_type", default="voucher") or "voucher").upper(),
            "game_id": pick(item, "game_id"),
            "game_name": pick(item, "game_name", "game"),
            "supplier_price": pick(item, "price", "cost"),
        })
    return {"success": True, "data": normalized}


@app.post("/api/admin/products")
async def api_admin_create_product(
    category_id: int = Form(...),
    name_tg: str = Form(...),
    name_ru: str = Form(...),
    price_somoni: float = Form(...),
    price_ruble: float = Form(0),
    epinby_product_id: int = Form(...),
    epinby_product_type: str = Form("VOUCHER"),
    variants: str = Form(None),
    image: UploadFile = File(None),
    image_url: str = Form(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    category = CategoryCRUD.get_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    product = ProductCRUD.create(
        db, category_id=category_id, name_tg=name_tg, name_ru=name_ru,
        price_somoni=price_somoni, price_ruble=price_ruble or price_somoni * 9.3,
        epinby_product_id=epinby_product_id, epinby_product_type=epinby_product_type,
    )

    parsed_variants = None
    if variants:
        try:
            parsed_variants = json.loads(variants)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="variants must be valid JSON")

    updates = {}
    if parsed_variants is not None:
        updates["variants"] = parsed_variants
    if image is not None and image.filename:
        updates["image_url"] = save_upload(image, PRODUCTS_IMAGES_DIR, f"product_{product.id}")
    elif image_url:
        # Ручной файл не загружали — берём ссылку на картинку с сайта поставщика,
        # подставленную при импорте товара из каталога Epinby (см. /api/admin/epinby-products).
        updates["image_url"] = image_url
    if updates:
        product = ProductCRUD.update(db, product.id, **updates)

    AdminLogCRUD.create(db, admin_id=admin.id, action="add_product", target_type="product", target_id=product.id)
    return {"success": True, "data": serialize_product(product, admin=True)}


@app.put("/api/admin/products/{product_id}")
async def api_admin_update_product(
    product_id: int,
    name_tg: str = Form(None),
    name_ru: str = Form(None),
    price_somoni: float = Form(None),
    price_ruble: float = Form(None),
    epinby_product_id: int = Form(None),
    is_active: bool = Form(None),
    variants: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    product = ProductCRUD.get_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_price = product.price_somoni
    updates = {}
    if name_tg is not None:
        updates["name_tg"] = name_tg
    if name_ru is not None:
        updates["name_ru"] = name_ru
    if price_somoni is not None:
        updates["price_somoni"] = price_somoni
    if price_ruble is not None:
        updates["price_ruble"] = price_ruble
    if epinby_product_id is not None:
        updates["epinby_product_id"] = epinby_product_id
    if is_active is not None:
        updates["is_active"] = is_active
    if variants is not None:
        try:
            updates["variants"] = json.loads(variants) if variants else None
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="variants must be valid JSON")
    if image is not None and image.filename:
        updates["image_url"] = save_upload(image, PRODUCTS_IMAGES_DIR, f"product_{product_id}")

    product = ProductCRUD.update(db, product_id, **updates)
    AdminLogCRUD.create(db, admin_id=admin.id, action="edit_product", target_type="product", target_id=product_id, details={k: v for k, v in updates.items() if k != "image_url"})

    # Уведомить группу админов об изменении цены
    if price_somoni is not None and price_somoni != old_price:
        await notify_admin_group(
            db,
            f"💲 <b>Изменена цена товара</b>\n\n"
            f"{product.name_ru}\n"
            f"Было: {old_price} сомони → Стало: {price_somoni} сомони"
        )

    return {"success": True, "data": serialize_product(product, admin=True)}


@app.delete("/api/admin/products/{product_id}")
async def api_admin_delete_product(product_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    ok = ProductCRUD.delete(db, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="delete_product", target_type="product", target_id=product_id)
    return {"success": True}


# ---------- USERS ----------
@app.get("/api/admin/users")
async def api_admin_get_users(
    search: str = None, skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin),
):
    query = db.query(User)
    if search:
        like = f"%{search}%"
        conditions = [User.telegram_username.ilike(like), User.phone_number.ilike(like)]
        if search.isdigit():
            conditions.append(User.telegram_id == int(search))
            conditions.append(User.id == int(search))
        from sqlalchemy import or_
        query = query.filter(or_(*conditions))
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return {"success": True, "data": {"users": [serialize_user(u) for u in users], "total": total}}


@app.post("/api/admin/users/{user_id}/block")
async def api_admin_block_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = UserCRUD.block_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="block_user", target_type="user", target_id=user_id)
    return {"success": True, "data": serialize_user(user)}


@app.post("/api/admin/users/{user_id}/unblock")
async def api_admin_unblock_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    user = UserCRUD.unblock_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="unblock_user", target_type="user", target_id=user_id)
    return {"success": True, "data": serialize_user(user)}


# ---------- ORDERS (last N days, view only) ----------
@app.get("/api/admin/orders")
async def api_admin_get_orders(search: str = None, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    orders = OrderCRUD.get_recent_orders(db, days=WEEKLY_STATS_DAYS)
    if search:
        like = search.lower()
        orders = [
            o for o in orders
            if like in str(o.id)
            or (o.user and like in str(o.user.telegram_id))
            or (o.user and o.user.telegram_username and like in o.user.telegram_username.lower())
        ]
    return {"success": True, "data": [serialize_order(o) for o in orders]}


# ---------- PAYMENTS (topups) ----------
@app.get("/api/admin/payments/pending")
async def api_admin_pending_payments(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    payments = PaymentCRUD.get_pending(db)
    return {"success": True, "data": [serialize_payment(p, admin=True) for p in payments]}


@app.get("/api/admin/payments/{payment_id}/receipt")
async def api_admin_get_receipt(payment_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    payment = PaymentCRUD.get_by_id(db, payment_id)
    if not payment or not payment.receipt_image_path or not os.path.exists(payment.receipt_image_path):
        raise HTTPException(status_code=404, detail="Receipt not found")
    return FileResponse(payment.receipt_image_path)


@app.post("/api/admin/payments/{payment_id}/confirm")
async def api_admin_confirm_payment(payment_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    payment = PaymentCRUD.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != "PENDING":
        raise HTTPException(status_code=400, detail="Payment already processed")

    payment = PaymentCRUD.confirm(db, payment_id)
    AdminLogCRUD.create(db, admin_id=admin.id, action="confirm_payment", target_type="payment", target_id=payment_id)

    user = UserCRUD.get_by_id(db, payment.user_id)
    if user:
        lang = user.language or "tg"
        msg = (f"✅ Ваше пополнение на {payment.amount_somoni} сомони подтверждено! Баланс пополнен."
               if lang == "ru" else
               f"✅ Пуркунии шумо ба маблағи {payment.amount_somoni} сомонӣ тасдиқ шуд! Баланс пур карда шуд.")
        try:
            await bot.send_message(user.telegram_id, msg)
        except Exception as e:
            logger.error(f"Failed to notify user about confirmed payment: {e}")

    return {"success": True, "data": serialize_payment(payment, admin=True)}


@app.post("/api/admin/payments/{payment_id}/reject")
async def api_admin_reject_payment(request: Request, payment_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    body = await request.json() if (await request.body()) else {}
    note = body.get("note")
    block_user_flag = bool(body.get("block_user", False))

    payment = PaymentCRUD.get_by_id(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != "PENDING":
        raise HTTPException(status_code=400, detail="Payment already processed")

    payment = PaymentCRUD.reject(db, payment_id, note=note)
    AdminLogCRUD.create(db, admin_id=admin.id, action="reject_payment", target_type="payment", target_id=payment_id, details={"note": note, "blocked": block_user_flag})

    user = UserCRUD.get_by_id(db, payment.user_id)
    if user:
        if block_user_flag:
            UserCRUD.block_user(db, user.id)
        lang = user.language or "tg"
        msg = (f"❌ Ваше пополнение на {payment.amount_somoni} сомони отклонено." + (f" Причина: {note}" if note else "")
               if lang == "ru" else
               f"❌ Пуркунии шумо ба маблағи {payment.amount_somoni} сомонӣ рад карда шуд." + (f" Сабаб: {note}" if note else ""))
        try:
            await bot.send_message(user.telegram_id, msg)
        except Exception as e:
            logger.error(f"Failed to notify user about rejected payment: {e}")

    return {"success": True, "data": serialize_payment(payment, admin=True)}


# ---------- REVIEWS ----------
@app.get("/api/admin/reviews")
async def api_admin_get_reviews(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    from database.models import Review
    reviews = db.query(Review).order_by(Review.created_at.desc()).all()
    return {"success": True, "data": [serialize_review(r) for r in reviews]}


@app.post("/api/admin/reviews")
async def api_admin_create_review(request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    body = await request.json()
    review = ReviewCRUD.create(
        db, author_name=body.get("author_name", "Anonymous"), rating=int(body.get("rating", 5)),
        text_tg=body.get("text_tg"), text_ru=body.get("text_ru"),
    )
    AdminLogCRUD.create(db, admin_id=admin.id, action="add_review", target_type="review", target_id=review.id)
    return {"success": True, "data": serialize_review(review)}


@app.put("/api/admin/reviews/{review_id}")
async def api_admin_update_review(review_id: int, request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    body = await request.json()
    allowed = {k: v for k, v in body.items() if k in ("author_name", "rating", "text_tg", "text_ru", "is_approved")}
    review = ReviewCRUD.update(db, review_id, **allowed)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="edit_review", target_type="review", target_id=review_id)
    return {"success": True, "data": serialize_review(review)}


@app.delete("/api/admin/reviews/{review_id}")
async def api_admin_delete_review(review_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    ok = ReviewCRUD.delete(db, review_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Review not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="delete_review", target_type="review", target_id=review_id)
    return {"success": True}


# ---------- PAYMENT METHODS (requisites) ----------
@app.get("/api/admin/payment-methods")
async def api_admin_get_payment_methods(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    from database.models import PaymentMethod
    methods = db.query(PaymentMethod).order_by(PaymentMethod.sort_order).all()
    return {"success": True, "data": [serialize_payment_method(m) for m in methods]}


@app.post("/api/admin/payment-methods")
async def api_admin_create_payment_method(
    name_tg: str = Form(...), name_ru: str = Form(...),
    account_number: str = Form(None), phone_number: str = Form(None), full_name: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin),
):
    method = PaymentMethodCRUD.create(db, name_tg=name_tg, name_ru=name_ru, account_number=account_number, phone_number=phone_number)
    updates = {}
    if full_name is not None:
        updates["full_name"] = full_name
    if image is not None and image.filename:
        updates["image_url"] = save_upload(image, UPLOADS_DIR, f"paymethod_{method.id}")
    if updates:
        method = PaymentMethodCRUD.update(db, method.id, **updates)
    AdminLogCRUD.create(db, admin_id=admin.id, action="add_payment_method", target_type="payment_method", target_id=method.id)
    return {"success": True, "data": serialize_payment_method(method)}


@app.put("/api/admin/payment-methods/{method_id}")
async def api_admin_update_payment_method(
    method_id: int,
    name_tg: str = Form(None), name_ru: str = Form(None),
    account_number: str = Form(None), phone_number: str = Form(None), full_name: str = Form(None),
    is_active: bool = Form(None), image: UploadFile = File(None),
    db: Session = Depends(get_db), admin: User = Depends(get_current_admin),
):
    updates = {k: v for k, v in {
        "name_tg": name_tg, "name_ru": name_ru, "account_number": account_number,
        "phone_number": phone_number, "full_name": full_name, "is_active": is_active,
    }.items() if v is not None}
    if image is not None and image.filename:
        updates["image_url"] = save_upload(image, UPLOADS_DIR, f"paymethod_{method_id}")

    method = PaymentMethodCRUD.update(db, method_id, **updates)
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="edit_payment_method", target_type="payment_method", target_id=method_id)
    return {"success": True, "data": serialize_payment_method(method)}


@app.delete("/api/admin/payment-methods/{method_id}")
async def api_admin_delete_payment_method(method_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    ok = PaymentMethodCRUD.delete(db, method_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Payment method not found")
    AdminLogCRUD.create(db, admin_id=admin.id, action="delete_payment_method", target_type="payment_method", target_id=method_id)
    return {"success": True}


# ---------- SITE TEXTS (inline editor overrides) ----------
@app.get("/api/admin/texts")
async def api_admin_get_texts(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    from translations.texts import TRANSLATIONS
    overrides_raw = SettingsCRUD.get(db, "text_overrides")
    overrides = json.loads(overrides_raw) if overrides_raw else {}
    return {"success": True, "data": {"base": TRANSLATIONS, "overrides": overrides}}


@app.put("/api/admin/texts")
async def api_admin_update_texts(request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """body: {"key": {"tg": "...", "ru": "..."}}  — частичное обновление, мёржится с текущими overrides"""
    body = await request.json()
    overrides_raw = SettingsCRUD.get(db, "text_overrides")
    overrides = json.loads(overrides_raw) if overrides_raw else {}
    overrides.update(body)
    SettingsCRUD.set(db, "text_overrides", json.dumps(overrides, ensure_ascii=False), value_type="json")
    refresh_text_overrides()  # применить изменения сразу, без ожидания TTL кэша
    AdminLogCRUD.create(db, admin_id=admin.id, action="edit_texts", details={"keys": list(body.keys())})
    return {"success": True, "data": {"overrides": overrides}}


# ---------- SETTINGS (group/channel ids) ----------
@app.get("/api/admin/settings")
async def api_admin_get_settings(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    admin_group = SettingsCRUD.get(db, "admin_group_chat_id") or ADMIN_GROUP_CHAT_ID
    sales_channel = SettingsCRUD.get(db, "sales_channel_id") or SALES_CHANNEL_ID
    return {"success": True, "data": {
        "admin_group_chat_id": admin_group,
        "sales_channel_id": sales_channel,
    }}


@app.put("/api/admin/settings")
async def api_admin_update_settings(request: Request, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    body = await request.json()
    if "admin_group_chat_id" in body:
        SettingsCRUD.set(db, "admin_group_chat_id", str(body["admin_group_chat_id"]))
    if "sales_channel_id" in body:
        SettingsCRUD.set(db, "sales_channel_id", str(body["sales_channel_id"]))
    AdminLogCRUD.create(db, admin_id=admin.id, action="edit_settings", details=body)
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)