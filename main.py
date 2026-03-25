import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import config
from database.engine import create_db
from database.github_sync import load_database

from middlewares.rate_limit import RateLimitMiddleware
from middlewares.auth import AuthMiddleware

from handlers import common, user, payment
from handlers import vip
from handlers.admin import panel, moderation, keys, users, products, vip_admin, broadcast

async def on_startup(bot: Bot):
    if config.use_webhook and config.webhook_url:
        await bot.set_webhook(f"{config.webhook_url}{config.webhook_path}", drop_pending_updates=True)
        logging.info(f"Webhook set to {config.webhook_url}{config.webhook_path}")

async def on_shutdown(bot: Bot):
    logging.info("Shutting down...")
    await bot.delete_webhook(drop_pending_updates=True)

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Database
    await create_db()

    # Restore data from GitHub (if configured)
    await load_database()
    
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Register Middlewares
    dp.message.middleware(RateLimitMiddleware(limit=1))
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Register common user routers
    dp.include_router(vip.router)      # VIP code interceptor — must be before common
    dp.include_router(common.router)
    dp.include_router(user.router)
    dp.include_router(payment.router)
    
    # Register admin routers
    dp.include_router(panel.router)
    dp.include_router(moderation.router)
    dp.include_router(keys.router)
    dp.include_router(users.router)
    dp.include_router(products.router)
    dp.include_router(vip_admin.router)
    dp.include_router(broadcast.router)
    
    if config.use_webhook:
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=config.webhook_path)
        setup_application(app, dp, bot=bot)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host=config.webapp_host, port=config.webapp_port)
        logging.info(f"Starting webhook server on {config.webapp_host}:{config.webapp_port}")
        await site.start()
        
        # Keep the event loop running
        await asyncio.Event().wait()
    else:
        logging.info("Starting bot in polling mode...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
