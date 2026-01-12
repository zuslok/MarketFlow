from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    #DB
    db_url: str = Field(default="postgresql+psycopg2://marketflow:marketflow@localhost:55432/marketflow")
    db_url_test: str = Field(default="postgresql+psycopg2://marketflow:marketflow@localhost:55433/marketflow_test")
    
    #RabbitMQ
    rabbitmq_url: str = Field(default="amqp://marketflow:marketflow@localhost:5672//")
    rabbitmq_exchange: str = "market_data_exchange"
    
    # Redis / Celery
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Fetch Intervals
    crypto_fetch_interval: int = Field(default=60)      # 1 minute
    equity_fetch_interval: int = Field(default=300)     # 5 minutes
    commodity_fetch_interval: int = Field(default=900)  # 15 minutes
    bond_fetch_interval: int = Field(default=3600)      # 1 hour
    
    # App
    enviroment: str = "local"
    log_level: str = "INFO"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")
        
settings = Settings()