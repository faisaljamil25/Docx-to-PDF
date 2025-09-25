from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import get_settings
from sqlalchemy.engine.url import make_url

settings = get_settings()

db_url = settings.DATABASE_URL
url = make_url(db_url)
connect_args = {}
# Allow SQLite to be used across threads in tests
if url.get_backend_name().startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
