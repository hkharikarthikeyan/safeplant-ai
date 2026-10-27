import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    DATA_DIR = os.environ.get("DATA_DIR", "../data")
    GENERATION_SEED = int(os.environ.get("GENERATION_SEED", "20261022"))

    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

    ACK_DEADLINES = {"CRITICAL": 120, "HIGH": 300, "MEDIUM": 900, "LOW": 1800}
    ALARM_FLOOD_COUNT = 10
    ALARM_FLOOD_WINDOW_MINUTES = 5
    NUISANCE_ALARM_COUNT = 3
    NUISANCE_ALARM_WINDOW_HOURS = 1
    REPEATED_UNSAFE_THRESHOLD = 2
    REPEATED_UNSAFE_WINDOW_DAYS = 30
    RISK_WEIGHTS = {
        "critical_alarms": 10,
        "high_incidents": 8,
        "repeated_unsafe": 6,
        "delayed_acks": 4,
        "overdue_actions": 5,
        "interlock_violations": 7,
    }
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 500
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
