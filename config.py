import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ⚠️ Барлық мәндер .env файлында болуы КЕРЕК
    # ⚠️ All values MUST be set in .env file
    bot_token: str                          # BOT_TOKEN=...
    admin_ids: list[int] = []               # ADMIN_IDS=[123456789]
    kaspi_phone: str = ""                   # KASPI_PHONE=+77...
    kaspi_receiver: str = ""                # KASPI_RECEIVER=Аты Жөні
    database_url: str = "sqlite+aiosqlite:///database.db"

    # Optional links
    official_website: str = "https://example.com"
    download_link: str = "https://example.com/download"
    telegram_channel: str = "https://t.me/your_channel"
    contact_admin: str = "https://t.me/your_admin"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Settings()
