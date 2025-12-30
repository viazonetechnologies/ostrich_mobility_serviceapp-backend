class Settings:
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost/ostrich_service"
    SECRET_KEY: str = "service-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REDIS_URL: str = "redis://localhost:6379"
    
    class Config:
        env_file = ".env"

settings = Settings()
