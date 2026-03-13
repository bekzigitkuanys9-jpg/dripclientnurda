import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from database.engine import create_db

from middlewares.rate_limit import RateLimitMiddleware
from middlewares.auth import AuthMiddleware

from handlers import common, user, payment
from handlers.admin import panel, moderation, keys, users, products

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize Database
    await create_db()
    
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    
    # Register Middlewares
    dp.message.middleware(RateLimitMiddleware(limit=1))
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Register common user routers
    dp.include_router(common.router)
    dp.include_router(user.router)
    dp.include_router(payment.router)
    
    # Register admin routers
    dp.include_router(panel.router)
    dp.include_router(moderation.router)
    dp.include_router(keys.router)
    dp.include_router(users.router)
    dp.include_router(products.router)
    
    logging.info("Starting bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
