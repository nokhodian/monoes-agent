import os

class Settings:
    APP_NAME = "Monoes Webapp"
    API_PREFIX = "/api"
    JWT_SECRET = os.environ.get("WEBAPP_JWT_SECRET", "dev-secret")
    JWT_ALGORITHM = "HS256"
    DB_URL = os.environ.get("WEBAPP_DB_URL", "sqlite:///./webapp.db")
    CORS_ORIGINS = os.environ.get("WEBAPP_CORS_ORIGINS", "*")

settings = Settings()
