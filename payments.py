"""
Интеграция с ЮKassa для курса «Гвозди Просто»

Документация: https://yookassa.ru/developers

⚠️ Для работы нужны SHOP_ID и SECRET_KEY из личного кабинета ЮKassa.
Добавьте их в .env:
    YOOKASSA_SHOP_ID=your_shop_id
    YOOKASSA_SECRET_KEY=your_secret_key
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Попытка импортировать yookassa (может не быть установлена)
try:
    from yookassa import Configuration, Payment
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False
    logging.warning("yookassa package not installed. Run: pip install yookassa")

# Конфигурация
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
RETURN_URL = os.getenv("RETURN_URL", "https://t.me/YourBotName")  # URL после оплаты

# Цены
COURSE_PRICE = 5990.00
COURSE_PRICE_DISCOUNT = 4790.00


def is_configured() -> bool:
    """Проверка, настроена ли ЮKassa."""
    return YOOKASSA_AVAILABLE and SHOP_ID and SECRET_KEY


def configure():
    """Настройка ЮKassa."""
    if not is_configured():
        logging.warning("YooKassa is not configured. Payments will not work.")
        return False
    
    Configuration.account_id = SHOP_ID
    Configuration.secret_key = SECRET_KEY
    return True


async def create_payment(
    user_id: int,
    amount: float = COURSE_PRICE_DISCOUNT,
    description: str = "Видеокурс «Гвозди Просто»"
) -> dict:
    """
    Создание платежа.
    
    Returns:
        dict: {
            'success': bool,
            'payment_id': str или None,
            'confirmation_url': str или None,
            'error': str или None
        }
    """
    if not configure():
        return {
            'success': False,
            'payment_id': None,
            'confirmation_url': None,
            'error': 'ЮKassa не настроена'
        }
    
    try:
        payment = Payment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": RETURN_URL
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id),
                "product": "gvozdi_prosto_course"
            }
        })
        
        return {
            'success': True,
            'payment_id': payment.id,
            'confirmation_url': payment.confirmation.confirmation_url,
            'error': None
        }
        
    except Exception as e:
        logging.error(f"Payment creation failed: {e}")
        return {
            'success': False,
            'payment_id': None,
            'confirmation_url': None,
            'error': str(e)
        }


async def check_payment_status(payment_id: str) -> dict:
    """
    Проверка статуса платежа.
    
    Returns:
        dict: {
            'status': 'pending' | 'waiting_for_capture' | 'succeeded' | 'canceled',
            'paid': bool,
            'user_id': str или None
        }
    """
    if not configure():
        return {'status': 'error', 'paid': False, 'user_id': None}
    
    try:
        payment = Payment.find_one(payment_id)
        
        return {
            'status': payment.status,
            'paid': payment.paid,
            'user_id': payment.metadata.get('user_id') if payment.metadata else None
        }
        
    except Exception as e:
        logging.error(f"Payment status check failed: {e}")
        return {'status': 'error', 'paid': False, 'user_id': None}


# ═══════════════════════════════════════════════════════════════
# WEBHOOK (для будущей реализации)
# ═══════════════════════════════════════════════════════════════

"""
Для автоматического подтверждения оплаты нужен webhook.
Настройте его в личном кабинете ЮKassa:
    URL: https://your-server.com/webhook/yookassa
    События: payment.succeeded, payment.canceled

Пример обработки (Flask/FastAPI):

@app.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    data = await request.json()
    
    if data.get('event') == 'payment.succeeded':
        payment = data['object']
        user_id = int(payment['metadata']['user_id'])
        payment_id = payment['id']
        
        # Отмечаем покупку
        await database.set_purchased(user_id, payment_id)
        
        # Отправляем подтверждение
        await bot.send_message(user_id, messages.PAYMENT_SUCCESS)
    
    return {"status": "ok"}
"""
