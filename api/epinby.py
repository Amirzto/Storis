# ====================================
# TajDonat - Epinby API Integration
# ====================================

import requests
import hashlib
import hmac
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from config import EPINBY_API_KEY, EPINBY_BASE_URL, EPINBY_WEBHOOK_SECRET

logger = logging.getLogger(__name__)


class EpinbyAPI:
    """Класс для работы с Epinby API"""
    
    def __init__(self):
        self.base_url = EPINBY_BASE_URL
        self.api_key = EPINBY_API_KEY
        self.webhook_secret = EPINBY_WEBHOOK_SECRET
        self.headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: dict = None, **kwargs) -> Dict[str, Any]:
        """
        Выполнить запрос к Epinby API
        
        Args:
            method: HTTP метод (GET, POST, etc)
            endpoint: endpoint API
            data: данные для POST
            **kwargs: дополнительные параметры для requests
        
        Returns:
            JSON ответ
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, **kwargs)
            else:
                response = requests.request(method, url, headers=self.headers, json=data, **kwargs)
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Epinby API error: {e}")
            return {"success": False, "error": str(e)}
    
    # ============= ACCOUNT =============
    def get_me(self) -> Dict[str, Any]:
        """Получить информацию о аккаунте и проверить API ключ"""
        return self._request("GET", "/getMe")
    
    # ============= GAMES =============
    def get_games(self) -> Dict[str, Any]:
        """Получить список доступных игр"""
        return self._request("GET", "/games")
    
    # ============= CATEGORIES =============
    def get_categories(self, game_id: int) -> Dict[str, Any]:
        """
        Получить категории товаров для игры
        
        Args:
            game_id: ID игры
        
        Returns:
            Список категорий
        """
        return self._request("GET", "/categories", params={"game_id": game_id})
    
    # ============= PRODUCTS =============
    def get_products(self, type: str = None, game_id: int = None, 
                    category_id: int = None, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """
        Получить товары с фильтрацией
        
        Args:
            type: voucher или topup
            game_id: ID игры
            category_id: ID категории
            page: номер страницы
            per_page: товаров на странице (макс 100)
        
        Returns:
            Список товаров
        """
        params = {}
        if type:
            params["type"] = type
        if game_id:
            params["game_id"] = game_id
        if category_id:
            params["category_id"] = category_id
        params["page"] = page
        params["per_page"] = min(per_page, 100)
        
        return self._request("GET", "/products", params=params)
    
    # ============= PLAYER VALIDATION =============
    def validate_player(self, product_id: int, player_id: str, 
                       server_id: str = None, **extra_fields) -> Dict[str, Any]:
        """
        Проверить игрока перед заказом
        
        Args:
            product_id: ID товара
            player_id: ID игрока
            server_id: ID сервера (если нужно)
            **extra_fields: дополнительные поля (input_2, input_3, и т.д.)
        
        Returns:
            Информация об игроке
        """
        data = {
            "product_id": product_id,
            "player_id": player_id
        }
        
        if server_id:
            data["server_id"] = server_id
        
        data.update(extra_fields)
        
        return self._request("POST", "/validate-player", data=data)
    
    # ============= ORDERS =============
    def create_order(self, product_id: int, qty: int = 1, player_id: str = None,
                    server_id: str = None, callback_url: str = None, 
                    callback_mode: str = "legacy", idempotency_key: str = None,
                    **extra_fields) -> Dict[str, Any]:
        """
        Создать заказ
        
        Args:
            product_id: ID товара
            qty: количество (для voucher), для topup всегда 1
            player_id: ID игрока (для topup)
            server_id: ID сервера
            callback_url: URL для вебхука
            callback_mode: legacy или events
            idempotency_key: уникальный ключ для безопасности
            **extra_fields: дополнительные поля
        
        Returns:
            Информация о заказе
        """
        data = {
            "product_id": product_id,
            "qty": qty
        }
        
        if player_id:
            data["player_id"] = player_id
        if server_id:
            data["server_id"] = server_id
        if callback_url:
            data["callback_url"] = callback_url
        if callback_mode:
            data["callback_mode"] = callback_mode
        
        data.update(extra_fields)
        
        headers = self.headers.copy()
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        return self._request("POST", "/order", data=data)
    
    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Получить статус заказа"""
        return self._request("GET", f"/order/{order_id}")
    
    def get_orders(self, limit: int = 50) -> Dict[str, Any]:
        """Получить список заказов"""
        return self._request("GET", "/orders", params={"limit": limit})
    
    # ============= REDEEM DATA =============
    def get_redeem_config(self) -> Dict[str, Any]:
        """Получить конфигурацию для Redeem Data API"""
        return self._request("GET", "/redeem-data/config")
    
    def check_redeem_code(self, code: str) -> Dict[str, Any]:
        """
        Проверить и получить информацию о коде
        
        Args:
            code: код для проверки
        
        Returns:
            Информация о коде
        """
        data = {"code": code}
        return self._request("POST", "/redeem-data/check", data=data)
    
    def get_redeem_history(self, limit: int = 20) -> Dict[str, Any]:
        """Получить историю проверок кодов"""
        return self._request("GET", "/redeem-data/history", params={"limit": limit})
    
    # ============= TELEGRAM STARS =============
    def get_stars_config(self) -> Dict[str, Any]:
        """Получить конфигурацию для Telegram Stars"""
        return self._request("GET", "/telegram-stars/config")
    
    def validate_telegram_recipient(self, telegram_username: str) -> Dict[str, Any]:
        """
        Проверить имя пользователя Telegram
        
        Args:
            telegram_username: имя пользователя (@username или username)
        
        Returns:
            Информация о пользователе
        """
        data = {"telegram_username": telegram_username}
        return self._request("POST", "/telegram-stars/recipient", data=data)
    
    def get_stars_quote(self, stars_amount: int) -> Dict[str, Any]:
        """
        Получить котировку для отправки звезд
        
        Args:
            stars_amount: количество звезд
        
        Returns:
            Цена в USD и информация о скидке
        """
        data = {"stars_amount": stars_amount}
        return self._request("POST", "/telegram-stars/quote", data=data)
    
    def send_telegram_stars(self, telegram_username: str, stars_amount: int, 
                           idempotency_key: str = None) -> Dict[str, Any]:
        """
        Отправить Telegram звезды
        
        Args:
            telegram_username: имя пользователя (@username или username)
            stars_amount: количество звезд
            idempotency_key: уникальный ключ для безопасности
        
        Returns:
            Информация о заказе
        """
        data = {
            "telegram_username": telegram_username,
            "stars_amount": stars_amount
        }
        
        headers = self.headers.copy()
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        return self._request("POST", "/telegram-stars/order", data=data)
    
    def get_stars_order(self, order_id: int) -> Dict[str, Any]:
        """Получить статус заказа звезд"""
        return self._request("GET", f"/telegram-stars/order/{order_id}")
    
    # ============= WEBHOOK VERIFICATION =============
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, secret: str = None) -> bool:
        """
        Проверить подпись вебхука
        
        Args:
            payload: тело запроса (raw)
            signature: значение заголовка X-GAMEX-Signature
            secret: webhook secret (если не указан, использует из конфига)
        
        Returns:
            True если подпись верна
        """
        if secret is None:
            secret = EPINBY_WEBHOOK_SECRET
        
        computed = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed, signature)
    
    @staticmethod
    def parse_webhook_payload(payload: str) -> Dict[str, Any]:
        """
        Парсить тело вебхука
        
        Args:
            payload: JSON строка
        
        Returns:
            Распарсенный словарь
        """
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse webhook payload: {payload}")
            return {}


class EpinbyWebhookHandler:
    """Обработчик вебхуков от Epinby"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.api = EpinbyAPI()
    
    def handle_order_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Обработать вебхук заказа
        
        Args:
            payload: данные вебхука
        
        Returns:
            True если успешно обработан
        """
        from database.crud import OrderCRUD
        
        try:
            epinby_order_id = payload.get("order_id")
            client_order_id = payload.get("client_order_id")
            status = payload.get("status")
            
            if not status or (not epinby_order_id and not client_order_id):
                logger.warning(f"Invalid webhook payload: {payload}")
                return False

            # client_order_id - это наш внутренний Order.id (мы сами его передаём как
            # X-Idempotency-Key при создании заказа), поэтому он надёжнее чем epinby_order_id
            order = None
            if client_order_id:
                try:
                    order = OrderCRUD.get_by_id(self.db, int(client_order_id))
                except (TypeError, ValueError):
                    order = OrderCRUD.get_by_client_order_id(self.db, str(client_order_id))
            if not order and epinby_order_id:
                order = OrderCRUD.get_by_epinby_id(self.db, epinby_order_id)

            if not order:
                logger.warning(f"Order not found for webhook: {payload}")
                return False

            # Обновить статус заказа в БД
            order = OrderCRUD.update_status(
                self.db,
                order.id,
                status,
                payload.get("message")
            )
            
            # Если успешно, сохранить данные доставки
            if status == "COMPLETED":
                delivery_data = payload.get("delivery", [])
                if delivery_data:
                    OrderCRUD.update(self.db, order.id, delivery_data=delivery_data)
            
            # Если ошибка, вернуть деньги
            elif status in ["FAILED", "CANCELED"]:
                amount_somoni = order.total_price_somoni
                amount_ruble = order.total_price_ruble
                OrderCRUD.refund(self.db, order.id, amount_somoni, amount_ruble)
            
            # Частичное выполнение - вернуть часть денег
            # ПРИМЕЧАНИЕ: официальная документация Epinby (Status Lifecycle) перечисляет
            # только PENDING/PROCESSING/COMPLETED/CANCELED/FAILED — статуса PARTIAL и поля
            # completion_percent в их вебхуках сейчас нет. Ветка оставлена как защитный код
            # на случай появления такого статуса в будущем, но полагаться на неё для
            # реального частичного возврата пока нельзя — см. предупреждение в чате.
            elif status == "PARTIAL":
                # Процент выполнения из payload
                completion_percent = payload.get("completion_percent", 0)
                if completion_percent > 0:
                    refund_amount_somoni = order.total_price_somoni * (1 - completion_percent / 100)
                    refund_amount_ruble = order.total_price_ruble * (1 - completion_percent / 100)
                    OrderCRUD.refund(self.db, order.id, refund_amount_somoni, refund_amount_ruble)
            
            logger.info(f"Webhook processed for order {order.id}: {status}")
            return order

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return None
    
    def handle_stars_webhook(self, payload: Dict[str, Any]) -> bool:
        """Обработать вебхук Telegram Stars"""
        # Похоже на order webhook
        return self.handle_order_webhook(payload)


class EpinbySync:
    """Синхронизация товаров из Epinby с локальной БД"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.api = EpinbyAPI()
    
    def sync_all_games(self) -> bool:
        """Синхронизировать все игры"""
        try:
            response = self.api.get_games()
            if not response.get("success"):
                logger.error(f"Failed to get games: {response}")
                return False
            
            games = response.get("data", [])
            logger.info(f"Found {len(games)} games")
            
            for game in games:
                logger.debug(f"Game: {game}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error syncing games: {e}")
            return False
    
    def sync_game_products(self, game_id: int) -> bool:
        """
        Синхронизировать товары для игры
        
        Args:
            game_id: ID игры в Epinby
        
        Returns:
            True если успешно
        """
        from database.crud import ProductCRUD, CategoryCRUD
        
        try:
            # Получить категории
            categories_response = self.api.get_categories(game_id)
            if not categories_response.get("success"):
                logger.error(f"Failed to get categories for game {game_id}")
                return False
            
            # Получить товары
            products_response = self.api.get_products(game_id=game_id, per_page=100)
            if not products_response.get("success"):
                logger.error(f"Failed to get products for game {game_id}")
                return False
            
            products = products_response.get("data", [])
            logger.info(f"Found {len(products)} products for game {game_id}")
            
            for product in products:
                # Проверить есть ли уже такой товар
                existing = ProductCRUD.get_by_epinby_id(self.db, product.get("id"))
                if not existing:
                    # Создать категорию если не существует
                    category_id = product.get("category_id")
                    category = CategoryCRUD.get_by_id(self.db, category_id)
                    if not category:
                        category_name = product.get("category", "Other")
                        category = CategoryCRUD.create(
                            self.db,
                            name_tg=category_name,
                            name_ru=category_name
                        )
                    
                    # Создать товар
                    ProductCRUD.create(
                        self.db,
                        category_id=category.id,
                        name_tg=product.get("name", "Product"),
                        name_ru=product.get("name", "Product"),
                        price_somoni=float(product.get("price", 0)) * 13,  # Примерный курс
                        price_ruble=float(product.get("price", 0)) * 100,
                        epinby_product_id=product.get("id"),
                        epinby_product_type=product.get("type", "VOUCHER")
                    )
            
            return True
        
        except Exception as e:
            logger.error(f"Error syncing products for game {game_id}: {e}")
            return False