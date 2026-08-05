import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "threading")
    CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "30"))
    LIVE_UPDATE_INTERVAL_SECONDS = float(os.getenv("LIVE_UPDATE_INTERVAL_SECONDS", "2"))
    MODEL_DIR = os.getenv("MODEL_DIR", "models")
    MODEL_PATH = os.path.join(MODEL_DIR, "xgb_direction_model.joblib")
    TOP_STOCKS = os.getenv("TOP_STOCKS", "AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA").split(",")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///instance/sharemarket_pro_predictor.db")
    
    # Session configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Contact email (SMTP)
    CONTACT_TO_EMAIL = os.getenv("CONTACT_TO_EMAIL", "nityagohel0109@gmail.com")
    CONTACT_FROM_EMAIL = os.getenv("CONTACT_FROM_EMAIL", os.getenv("SMTP_USERNAME", ""))
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true")