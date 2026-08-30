# ====================================
# TajDonat - Database Models
# ====================================

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# ============= USER MODEL =============
class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Баланс
    balance_somoni = Column(Float, default=0.0)
    balance_ruble = Column(Float, default=0.0)
    
    # Язык и валюта
    language = Column(String(10), default="tg")  # tg или ru
    preferred_currency = Column(String(20), default="somoni")
    
    # Статус
    is_blocked = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    
    # Реферал
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    referral_bonus = Column(Float, default=0.0)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    referrals = relationship("User", remote_side=[referrer_id])
    
    def __repr__(self):
        return f"<User {self.telegram_id} ({self.telegram_username})>"


# ============= CATEGORY MODEL =============
class Category(Base):
    """Модель категории товаров"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name_tg = Column(String(255), nullable=False)  # Таджикское название
    name_ru = Column(String(255), nullable=False)  # Русское название
    
    image_url = Column(String(512), nullable=True)
    image_path = Column(String(512), nullable=True)  # Локальный путь
    
    description_tg = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    
    # Для сортировки и отображения
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Category {self.name_tg}>"


# ============= PRODUCT MODEL =============
class Product(Base):
    """Модель подкатегории/товара"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    
    # Базовая информация
    name_tg = Column(String(255), nullable=False)
    name_ru = Column(String(255), nullable=False)
    description_tg = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    
    # Цена
    price_somoni = Column(Float, nullable=False)
    price_ruble = Column(Float, nullable=False)
    
    # Товар с Epinby
    epinby_product_id = Column(Integer, nullable=False, index=True)  # ID товара на Epinby
    epinby_product_type = Column(String(50), default="VOUCHER")  # VOUCHER или TOPUP
    
    # Изображение
    image_url = Column(String(512), nullable=True)
    
    # Варианты/страны (для игр типа Free Fire)
    variants = Column(JSON, nullable=True)  # {"GLOBAL": {...}, "CIS": {...}, ...}
    
    # Сортировка
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    stock_count = Column(Integer, nullable=True)  # Если ограниченный товар
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    category = relationship("Category", back_populates="products")
    orders = relationship("Order", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product {self.name_tg} ({self.epinby_product_id})>"


# ============= ORDER MODEL =============
class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Информация заказа
    quantity = Column(Integer, default=1)
    total_price_somoni = Column(Float, nullable=False)
    total_price_ruble = Column(Float, nullable=False)
    
    # Статус
    status = Column(String(50), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED, PARTIAL
    status_message = Column(Text, nullable=True)
    
    # Для игр требующих ID
    player_id = Column(String(255), nullable=True)
    player_name = Column(String(255), nullable=True)
    server_id = Column(String(100), nullable=True)
    region = Column(String(50), nullable=True)
    
    # Выбранный вариант (для товаров с вариантами)
    selected_variant = Column(String(100), nullable=True)  # GLOBAL, CIS и т.д.
    
    # Deliveries/Коды
    delivery_data = Column(JSON, nullable=True)  # Массив кодов/данных для выдачи
    
    # Эпинби ID
    epinby_order_id = Column(Integer, nullable=True)
    epinby_client_order_id = Column(String(255), nullable=True)

    # ID сообщения в публичном канале продаж (для обновления статуса в посте)
    channel_message_id = Column(Integer, nullable=True)
    
    # Возврат средств при ошибке
    refund_amount_somoni = Column(Float, default=0.0)
    refund_amount_ruble = Column(Float, default=0.0)
    is_refunded = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")
    
    def __repr__(self):
        return f"<Order {self.id} - {self.status}>"


# ============= PAYMENT MODEL =============
class Payment(Base):
    """Модель пополнения баланса"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Сумма
    amount_somoni = Column(Float, nullable=True)
    amount_ruble = Column(Float, nullable=True)
    currency = Column(String(20))  # somoni или ruble
    
    # Метод
    payment_method = Column(String(50))  # DC_NEXT, ALIF, T_BANK, и т.д.
    payment_method_name = Column(String(255), nullable=True)
    
    # Статус
    status = Column(String(50), default="PENDING")  # PENDING, CONFIRMED, REJECTED
    admin_note = Column(Text, nullable=True)
    
    # Квитанция
    receipt_image_path = Column(String(512), nullable=True)
    receipt_url = Column(String(512), nullable=True)
    
    # Информация о платеже
    account_info = Column(String(255), nullable=True)  # Номер счета, ID и т.д.
    phone_number = Column(String(20), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    user = relationship("User", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment {self.id} - {self.status}>"


# ============= PAYMENT METHOD MODEL =============
class PaymentMethod(Base):
    """Модель способа оплаты (реквизиты)"""
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True)
    
    # Информация
    name_tg = Column(String(255), nullable=False)
    name_ru = Column(String(255), nullable=False)
    
    # Реквизиты
    account_number = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    full_name = Column(String(255), nullable=True)
    description_tg = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    
    # Изображение
    image_url = Column(String(512), nullable=True)
    image_path = Column(String(512), nullable=True)
    
    # Статус
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PaymentMethod {self.name_tg}>"


# ============= REVIEW MODEL =============
class Review(Base):
    """Модель отзыва"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Может быть NULL если админ добавил
    
    # Информация об отзыве
    rating = Column(Integer, default=5)  # 1-5 звёзд
    text_tg = Column(Text, nullable=True)
    text_ru = Column(Text, nullable=True)
    
    # Автор (может быть другой пользователь)
    author_name = Column(String(255), nullable=False)
    
    # Статус
    is_approved = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Review {self.id} - {self.rating}★>"


# ============= SETTINGS MODEL =============
class Settings(Base):
    """Модель для хранения глобальных настроек"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string")  # string, int, float, bool, json
    
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Settings {self.key}>"


# ============= ADMIN LOG MODEL =============
class AdminLog(Base):
    """Модель логов действий админа"""
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    action = Column(String(255), nullable=False)  # add_category, delete_user, edit_price и т.д.
    target_type = Column(String(100), nullable=True)  # user, order, product, category и т.д.
    target_id = Column(Integer, nullable=True)
    
    details = Column(JSON, nullable=True)  # Дополнительные детали изменения
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<AdminLog {self.action}>"