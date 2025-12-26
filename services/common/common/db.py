from .config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_url = settings.db_url

engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()