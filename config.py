# Config.py

import os
from dotenv import load_dotenv

load_dotenv()


DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_HOST = os.getenv("POSTGRES_HOST", 'db')



class Config:
    DB_USER = DB_USER
    DB_PASSWORD = DB_PASSWORD
    DB_NAME = DB_NAME
    DB_HOST = DB_HOST
    
    DB_CONFIG = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

ADMIN_GROUP_ID = os.getenv("ADMIN_GROUP_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
BOT_TOKEN = os.getenv("TOKEN")
sentry_dsn = os.getenv("SENTRY_DSN")
# ADMIN_IDS = [123456789, 987654321]
