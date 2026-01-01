# -*- coding: utf-8 -*-
"""
API сервер для Mini App

Предоставляет эндпоинты для получения данных пользователя,
статуса рефералов и режима приложения.
"""

from aiohttp import web
from aiohttp.web import middleware
from datetime import datetime
import database
import messages
import logging
import json

# ═══════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═══════════════════════════════════════════════════════════════

@middleware
async def cors_middleware(request, handler):
    """Добавляет CORS заголовки для Mini App."""
    if request.method == "OPTIONS":
        response = web.Response()
    else:
        response = await handler(request)
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Telegram-Init-Data'
    return response


# ═══════════════════════════════════════════════════════════════
# ЭНДПОИНТЫ
# ═══════════════════════════════════════════════════════════════

async def get_user_data(request):
    """
    GET /api/user/{telegram_id}
    
    Возвращает данные пользователя для Mini App:
    - user_id, username, full_name
    - is_registered (зарегистрирован ли на вебинар)
    - referrals (количество приведённых друзей)
    - target_referrals (цель — 2)
    - in_raffle (участвует ли в розыгрыше)
    """
    try:
        telegram_id = int(request.match_info['telegram_id'])
        data = await database.get_user_referral_info(telegram_id)
        
        return web.json_response({
            "success": True,
            "data": data
        })
    except ValueError:
        return web.json_response({
            "success": False,
            "error": "Invalid telegram_id"
        }, status=400)
    except Exception as e:
        logging.error(f"Error getting user data: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def get_app_mode(request):
    """
    GET /api/mode
    
    Возвращает текущий режим приложения:
    - before_webinar: до начала эфира
    - live: эфир идёт (в течение 2 часов после старта)
    - after_webinar: после эфира (активируется sales page)
    - offer_expired: скидка закончилась
    """
    try:
        webinar_dt = datetime.strptime(messages.WEBINAR_DATE, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        # Параметры времени
        webinar_duration_hours = 2  # Длительность эфира
        offer_duration_hours = 12   # Время действия скидки
        
        from datetime import timedelta
        webinar_end = webinar_dt + timedelta(hours=webinar_duration_hours)
        offer_deadline = webinar_end + timedelta(hours=offer_duration_hours)
        
        if now < webinar_dt:
            mode = "before_webinar"
            seconds_until = (webinar_dt - now).total_seconds()
            deadline = webinar_dt.isoformat()
        elif now < webinar_end:
            mode = "live"
            seconds_until = 0
            deadline = None
        elif now < offer_deadline:
            mode = "after_webinar"
            seconds_until = (offer_deadline - now).total_seconds()
            deadline = offer_deadline.isoformat()
        else:
            mode = "offer_expired"
            seconds_until = 0
            deadline = None
        
        return web.json_response({
            "success": True,
            "data": {
                "mode": mode,
                "webinar_date": webinar_dt.isoformat(),
                "seconds_until": int(seconds_until),
                "deadline": deadline,
                "course_price": messages.COURSE_PRICE,
                "course_price_discount": messages.COURSE_PRICE_DISCOUNT
            }
        })
    except Exception as e:
        logging.error(f"Error getting app mode: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def register_user(request):
    """
    POST /api/register
    
    Регистрирует пользователя на вебинар.
    Body: { "telegram_id": 123, "name": "...", "phone": "...", "goal": "..." }
    """
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        
        if not telegram_id:
            return web.json_response({
                "success": False,
                "error": "telegram_id is required"
            }, status=400)
        
        # Регистрируем на вебинар
        await database.set_webinar_registration(telegram_id)
        
        # Получаем обновлённые данные
        user_data = await database.get_user_referral_info(telegram_id)
        
        return web.json_response({
            "success": True,
            "message": "Registered successfully",
            "data": user_data
        })
    except Exception as e:
        logging.error(f"Error registering user: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def get_referral_link(request):
    """
    GET /api/referral/{telegram_id}
    
    Возвращает реферальную ссылку для пользователя.
    """
    try:
        telegram_id = int(request.match_info['telegram_id'])
        bot_username = "GvozdiProstoBot"  # TODO: получать динамически
        
        referral_link = f"https://t.me/{bot_username}?start=ref_{telegram_id}"
        share_text = "Присоединяйся к эфиру про практику на гвоздях! 🔥"
        
        return web.json_response({
            "success": True,
            "data": {
                "referral_link": referral_link,
                "share_text": share_text,
                "share_url": f"https://t.me/share/url?url={referral_link}&text={share_text}"
            }
        })
    except ValueError:
        return web.json_response({
            "success": False,
            "error": "Invalid telegram_id"
        }, status=400)


async def health_check(request):
    """GET /api/health — проверка работоспособности."""
    return web.json_response({
        "success": True,
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    })


# ═══════════════════════════════════════════════════════════════
# ТРЕКЕР ПРАКТИКИ
# ═══════════════════════════════════════════════════════════════

async def get_practice(request):
    """
    GET /api/practice/{telegram_id}
    
    Возвращает прогресс трекера практики.
    """
    try:
        telegram_id = int(request.match_info['telegram_id'])
        
        completed_days = await database.get_completed_days(telegram_id)
        logs = await database.get_practice_logs(telegram_id)
        
        return web.json_response({
            "success": True,
            "data": {
                "completed_days": completed_days,
                "total_days": len(completed_days),
                "target_days": 21,
                "logs": logs
            }
        })
    except ValueError:
        return web.json_response({
            "success": False,
            "error": "Invalid telegram_id"
        }, status=400)
    except Exception as e:
        logging.error(f"Error getting practice: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def save_practice(request):
    """
    POST /api/practice
    
    Сохраняет запись о практике.
    Body: { "telegram_id": 123, "date": "2026-01-01", "duration": 300 }
    """
    try:
        data = await request.json()
        telegram_id = data.get('telegram_id')
        practice_date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        duration = data.get('duration', 0)
        
        if not telegram_id:
            return web.json_response({
                "success": False,
                "error": "telegram_id is required"
            }, status=400)
        
        await database.save_practice_log(telegram_id, practice_date, duration)
        
        # Возвращаем обновлённый прогресс
        completed_days = await database.get_completed_days(telegram_id)
        
        return web.json_response({
            "success": True,
            "message": "Practice saved",
            "data": {
                "completed_days": completed_days,
                "total_days": len(completed_days)
            }
        })
    except Exception as e:
        logging.error(f"Error saving practice: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


async def reset_practice(request):
    """
    DELETE /api/practice/{telegram_id}
    
    Сбрасывает трекер практики.
    """
    try:
        telegram_id = int(request.match_info['telegram_id'])
        
        await database.reset_practice_tracker(telegram_id)
        
        return web.json_response({
            "success": True,
            "message": "Practice tracker reset"
        })
    except ValueError:
        return web.json_response({
            "success": False,
            "error": "Invalid telegram_id"
        }, status=400)
    except Exception as e:
        logging.error(f"Error resetting practice: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        }, status=500)


# ═══════════════════════════════════════════════════════════════
# НАСТРОЙКА ПРИЛОЖЕНИЯ
# ═══════════════════════════════════════════════════════════════

def create_app():
    """Создаёт и настраивает aiohttp приложение."""
    app = web.Application(middlewares=[cors_middleware])
    
    # Роуты API
    app.router.add_get('/', health_check)  # Railway health check on root
    app.router.add_get('/api/health', health_check)
    app.router.add_get('/api/user/{telegram_id}', get_user_data)
    app.router.add_get('/api/mode', get_app_mode)
    app.router.add_get('/api/referral/{telegram_id}', get_referral_link)
    app.router.add_post('/api/register', register_user)
    
    # Трекер практики
    app.router.add_get('/api/practice/{telegram_id}', get_practice)
    app.router.add_post('/api/practice', save_practice)
    app.router.add_delete('/api/practice/{telegram_id}', reset_practice)
    
    # Статические файлы для Mini App (React build)
    # app.router.add_static('/app', 'mini-app/dist')
    
    return app


async def start_api_server(host='0.0.0.0', port=8080):
    """Запуск API сервера."""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info(f"API server started on http://{host}:{port}")
    return runner


if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        await database.init_db()
        await start_api_server()
        # Держим сервер запущенным
        while True:
            await asyncio.sleep(3600)
    
    asyncio.run(main())
