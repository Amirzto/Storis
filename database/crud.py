# ====================================
# TajDonat - Database CRUD Operations
# ====================================

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from typing import List, Optional

from database.models import (
    User, Category, Product, Order, Payment, PaymentMethod, Review, Settings, AdminLog
)


# ============= USER OPERATIONS =============
class UserCRUD:
    @staticmethod
    def get_or_create(db: Session, telegram_id: int, telegram_username: str = None) -> User:
        """Получить или создать пользователя"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                language="tg",
                preferred_currency="somoni"
            )
            db.add(user)
            db.commit()
        return user
    
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_telegram_id(db: Session, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        return db.query(User).filter(User.telegram_id == telegram_id).first()
    
    @staticmethod
    def update(db: Session, user_id: int, **kwargs) -> User:
        """Обновить данные пользователя"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.utcnow()
            db.commit()
        return user
    
    @staticmethod
    def add_balance(db: Session, user_id: int, amount_somoni: float = 0, amount_ruble: float = 0):
        """Добавить средства на баланс"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.balance_somoni += amount_somoni
            user.balance_ruble += amount_ruble
            db.commit()
        return user
    
    @staticmethod
    def subtract_balance(db: Session, user_id: int, amount_somoni: float = 0, amount_ruble: float = 0) -> bool:
        """Вычесть средства с баланса (возвращает True если хватило)"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        if amount_somoni > 0 and user.balance_somoni < amount_somoni:
            return False
        if amount_ruble > 0 and user.balance_ruble < amount_ruble:
            return False
        
        user.balance_somoni -= amount_somoni
        user.balance_ruble -= amount_ruble
        db.commit()
        return True
    
    @staticmethod
    def block_user(db: Session, user_id: int):
        """Заблокировать пользователя"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_blocked = True
            db.commit()
        return user
    
    @staticmethod
    def unblock_user(db: Session, user_id: int):
        """Разблокировать пользователя"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_blocked = False
            db.commit()
        return user
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить всех пользователей"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_total_count(db: Session) -> int:
        """Получить общее количество пользователей"""
        return db.query(User).count()
    
    @staticmethod
    def update_last_activity(db: Session, user_id: int):
        """Обновить время последней активности"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_activity = datetime.utcnow()
            db.commit()


# ============= CATEGORY OPERATIONS =============
class CategoryCRUD:
    @staticmethod
    def create(db: Session, name_tg: str, name_ru: str, image_path: str = None) -> Category:
        """Создать категорию"""
        category = Category(
            name_tg=name_tg,
            name_ru=name_ru,
            image_path=image_path,
            sort_order=CategoryCRUD.get_max_sort_order(db) + 1
        )
        db.add(category)
        db.commit()
        return category
    
    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        """Получить категорию по ID"""
        return db.query(Category).filter(Category.id == category_id).first()
    
    @staticmethod
    def get_all(db: Session) -> List[Category]:
        """Получить все активные категории (отсортированные)"""
        return db.query(Category).filter(Category.is_active == True).order_by(Category.sort_order).all()
    
    @staticmethod
    def update(db: Session, category_id: int, **kwargs) -> Category:
        """Обновить категорию"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            for key, value in kwargs.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            category.updated_at = datetime.utcnow()
            db.commit()
        return category
    
    @staticmethod
    def delete(db: Session, category_id: int) -> bool:
        """Удалить категорию"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if category:
            db.delete(category)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_max_sort_order(db: Session) -> int:
        """Получить максимальный порядок сортировки"""
        result = db.query(Category).order_by(desc(Category.sort_order)).first()
        return result.sort_order if result else 0


# ============= PRODUCT OPERATIONS =============
class ProductCRUD:
    @staticmethod
    def create(db: Session, category_id: int, name_tg: str, name_ru: str, 
               price_somoni: float, price_ruble: float, epinby_product_id: int, 
               epinby_product_type: str = "VOUCHER", image_url: str = None) -> Product:
        """Создать товар"""
        product = Product(
            category_id=category_id,
            name_tg=name_tg,
            name_ru=name_ru,
            price_somoni=price_somoni,
            price_ruble=price_ruble,
            epinby_product_id=epinby_product_id,
            epinby_product_type=epinby_product_type,
            image_url=image_url,
            sort_order=ProductCRUD.get_max_sort_order(db) + 1
        )
        db.add(product)
        db.commit()
        return product
    
    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Optional[Product]:
        """Получить товар по ID"""
        return db.query(Product).filter(Product.id == product_id).first()
    
    @staticmethod
    def get_by_category(db: Session, category_id: int) -> List[Product]:
        """Получить товары категории (отсортированные от дешевых к дорогим)"""
        return db.query(Product).filter(
            and_(Product.category_id == category_id, Product.is_active == True)
        ).order_by(Product.price_somoni).all()
    
    @staticmethod
    def get_by_epinby_id(db: Session, epinby_product_id: int) -> Optional[Product]:
        """Получить товар по ID Epinby"""
        return db.query(Product).filter(Product.epinby_product_id == epinby_product_id).first()
    
    @staticmethod
    def update(db: Session, product_id: int, **kwargs) -> Product:
        """Обновить товар"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            for key, value in kwargs.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            product.updated_at = datetime.utcnow()
            db.commit()
        return product
    
    @staticmethod
    def delete(db: Session, product_id: int) -> bool:
        """Удалить товар"""
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            db.delete(product)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_max_sort_order(db: Session) -> int:
        """Получить максимальный порядок сортировки"""
        result = db.query(Product).order_by(desc(Product.sort_order)).first()
        return result.sort_order if result else 0


# ============= ORDER OPERATIONS =============
class OrderCRUD:
    @staticmethod
    def create(db: Session, user_id: int, product_id: int, quantity: int,
               total_price_somoni: float, total_price_ruble: float,
               player_id: str = None, server_id: str = None) -> Order:
        """Создать заказ"""
        order = Order(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            total_price_somoni=total_price_somoni,
            total_price_ruble=total_price_ruble,
            player_id=player_id,
            server_id=server_id,
            status="PENDING"
        )
        db.add(order)
        db.commit()
        return order
    
    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        """Получить заказ по ID"""
        return db.query(Order).filter(Order.id == order_id).first()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Получить заказы пользователя"""
        return db.query(Order).filter(Order.user_id == user_id).order_by(
            desc(Order.created_at)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_recent_orders(db: Session, days: int = 7) -> List[Order]:
        """Получить заказы за последние N дней"""
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(Order).filter(Order.created_at >= since).order_by(
            desc(Order.created_at)
        ).all()
    
    @staticmethod
    def get_by_epinby_id(db: Session, epinby_order_id: int) -> Optional[Order]:
        """Найти заказ по ID заказа в Epinby (используется как fallback в вебхуке)"""
        return db.query(Order).filter(Order.epinby_order_id == epinby_order_id).first()

    @staticmethod
    def get_by_client_order_id(db: Session, client_order_id: str) -> Optional[Order]:
        """Найти заказ по client_order_id, который мы сами передали в Epinby при создании"""
        return db.query(Order).filter(Order.epinby_client_order_id == client_order_id).first()

    @staticmethod
    def update_status(db: Session, order_id: int, status: str, message: str = None) -> Order:
        """Обновить статус заказа"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            if message:
                order.status_message = message
            if status == "COMPLETED":
                order.completed_at = datetime.utcnow()
            db.commit()
        return order
    
    @staticmethod
    def update(db: Session, order_id: int, **kwargs) -> Order:
        """Обновить заказ"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            for key, value in kwargs.items():
                if hasattr(order, key):
                    setattr(order, key, value)
            db.commit()
        return order
    
    @staticmethod
    def refund(db: Session, order_id: int, amount_somoni: float = 0, amount_ruble: float = 0) -> bool:
        """Вернуть средства за заказ"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order and not order.is_refunded:
            UserCRUD.add_balance(db, order.user_id, amount_somoni, amount_ruble)
            order.refund_amount_somoni = amount_somoni
            order.refund_amount_ruble = amount_ruble
            order.is_refunded = True
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_total_count(db: Session) -> int:
        """Получить общее количество заказов"""
        return db.query(Order).count()


# ============= PAYMENT OPERATIONS =============
class PaymentCRUD:
    @staticmethod
    def create(db: Session, user_id: int, amount_somoni: float = 0, 
               amount_ruble: float = 0, currency: str = "somoni",
               payment_method: str = None) -> Payment:
        """Создать платеж"""
        payment = Payment(
            user_id=user_id,
            amount_somoni=amount_somoni,
            amount_ruble=amount_ruble,
            currency=currency,
            payment_method=payment_method,
            status="PENDING"
        )
        db.add(payment)
        db.commit()
        return payment
    
    @staticmethod
    def get_by_id(db: Session, payment_id: int) -> Optional[Payment]:
        """Получить платеж по ID"""
        return db.query(Payment).filter(Payment.id == payment_id).first()
    
    @staticmethod
    def get_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Payment]:
        """Получить платежи пользователя"""
        return db.query(Payment).filter(Payment.user_id == user_id).order_by(
            desc(Payment.created_at)
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_pending(db: Session) -> List[Payment]:
        """Получить неподтвержденные платежи"""
        return db.query(Payment).filter(Payment.status == "PENDING").order_by(
            Payment.created_at
        ).all()
    
    @staticmethod
    def confirm(db: Session, payment_id: int) -> Payment:
        """Подтвердить платеж"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            payment.status = "CONFIRMED"
            payment.confirmed_at = datetime.utcnow()
            
            # Добавить средства на баланс
            if payment.amount_somoni:
                UserCRUD.add_balance(db, payment.user_id, amount_somoni=payment.amount_somoni)
            if payment.amount_ruble:
                UserCRUD.add_balance(db, payment.user_id, amount_ruble=payment.amount_ruble)
            
            db.commit()
        return payment
    
    @staticmethod
    def reject(db: Session, payment_id: int, note: str = None) -> Payment:
        """Отклонить платеж"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            payment.status = "REJECTED"
            payment.rejected_at = datetime.utcnow()
            if note:
                payment.admin_note = note
            db.commit()
        return payment
    
    @staticmethod
    def update(db: Session, payment_id: int, **kwargs) -> Payment:
        """Обновить платеж"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            for key, value in kwargs.items():
                if hasattr(payment, key):
                    setattr(payment, key, value)
            db.commit()
        return payment


# ============= PAYMENT METHOD OPERATIONS =============
class PaymentMethodCRUD:
    @staticmethod
    def create(db: Session, name_tg: str, name_ru: str, 
               account_number: str = None, phone_number: str = None) -> PaymentMethod:
        """Создать способ оплаты"""
        method = PaymentMethod(
            name_tg=name_tg,
            name_ru=name_ru,
            account_number=account_number,
            phone_number=phone_number,
            sort_order=PaymentMethodCRUD.get_max_sort_order(db) + 1
        )
        db.add(method)
        db.commit()
        return method
    
    @staticmethod
    def get_by_id(db: Session, method_id: int) -> Optional[PaymentMethod]:
        """Получить способ оплаты по ID"""
        return db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
    
    @staticmethod
    def get_all(db: Session) -> List[PaymentMethod]:
        """Получить все активные способы оплаты"""
        return db.query(PaymentMethod).filter(
            PaymentMethod.is_active == True
        ).order_by(PaymentMethod.sort_order).all()
    
    @staticmethod
    def update(db: Session, method_id: int, **kwargs) -> PaymentMethod:
        """Обновить способ оплаты"""
        method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
        if method:
            for key, value in kwargs.items():
                if hasattr(method, key):
                    setattr(method, key, value)
            method.updated_at = datetime.utcnow()
            db.commit()
        return method
    
    @staticmethod
    def delete(db: Session, method_id: int) -> bool:
        """Удалить способ оплаты"""
        method = db.query(PaymentMethod).filter(PaymentMethod.id == method_id).first()
        if method:
            db.delete(method)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_max_sort_order(db: Session) -> int:
        """Получить максимальный порядок сортировки"""
        result = db.query(PaymentMethod).order_by(desc(PaymentMethod.sort_order)).first()
        return result.sort_order if result else 0


# ============= REVIEW OPERATIONS =============
class ReviewCRUD:
    @staticmethod
    def create(db: Session, author_name: str, rating: int = 5,
               text_tg: str = None, text_ru: str = None, user_id: int = None) -> Review:
        """Создать отзыв"""
        review = Review(
            user_id=user_id,
            author_name=author_name,
            rating=rating,
            text_tg=text_tg,
            text_ru=text_ru
        )
        db.add(review)
        db.commit()
        return review
    
    @staticmethod
    def get_all(db: Session) -> List[Review]:
        """Получить все одобренные отзывы"""
        return db.query(Review).filter(
            Review.is_approved == True
        ).order_by(desc(Review.sort_order)).all()
    
    @staticmethod
    def get_by_id(db: Session, review_id: int) -> Optional[Review]:
        """Получить отзыв по ID"""
        return db.query(Review).filter(Review.id == review_id).first()
    
    @staticmethod
    def update(db: Session, review_id: int, **kwargs) -> Review:
        """Обновить отзыв"""
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            for key, value in kwargs.items():
                if hasattr(review, key):
                    setattr(review, key, value)
            review.updated_at = datetime.utcnow()
            db.commit()
        return review
    
    @staticmethod
    def delete(db: Session, review_id: int) -> bool:
        """Удалить отзыв"""
        review = db.query(Review).filter(Review.id == review_id).first()
        if review:
            db.delete(review)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_average_rating(db: Session) -> float:
        """Получить среднюю оценку"""
        result = db.query(Review).filter(Review.is_approved == True).all()
        if not result:
            return 0.0
        total = sum(review.rating for review in result)
        return total / len(result)


# ============= SETTINGS OPERATIONS =============
class SettingsCRUD:
    @staticmethod
    def get(db: Session, key: str) -> Optional[str]:
        """Получить значение настройки"""
        setting = db.query(Settings).filter(Settings.key == key).first()
        return setting.value if setting else None
    
    @staticmethod
    def set(db: Session, key: str, value: str, value_type: str = "string"):
        """Установить значение настройки"""
        setting = db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = value
            setting.value_type = value_type
        else:
            setting = Settings(key=key, value=value, value_type=value_type)
            db.add(setting)
        db.commit()
        return setting
    
    @staticmethod
    def get_all(db: Session) -> dict:
        """Получить все настройки"""
        settings = db.query(Settings).all()
        return {s.key: s.value for s in settings}


# ============= ADMIN LOG OPERATIONS =============
class AdminLogCRUD:
    @staticmethod
    def create(db: Session, admin_id: int, action: str, target_type: str = None,
               target_id: int = None, details: dict = None) -> AdminLog:
        """Создать запись в логе админа"""
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        db.add(log)
        db.commit()
        return log
    
    @staticmethod
    def get_by_admin(db: Session, admin_id: int, skip: int = 0, limit: int = 100) -> List[AdminLog]:
        """Получить логи админа"""
        return db.query(AdminLog).filter(AdminLog.admin_id == admin_id).order_by(
            desc(AdminLog.created_at)
        ).offset(skip).limit(limit).all()