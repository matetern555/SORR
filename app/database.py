import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Obsługa zarówno PostgreSQL (produkcja) jak i SQLite (lokalnie)
# Render.com automatycznie ustawia DATABASE_URL dla PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL (produkcja na Render.com)
    # Render.com używa formatu: postgresql://user:pass@host:port/dbname
    # SQLAlchemy potrzebuje postgresql:// zamiast postgres://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
    connect_args = {}
else:
    # SQLite (lokalnie)
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sor.db"
    connect_args = {"check_same_thread": False}

# Tworzymy silnik bazy danych
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

# Tworzymy fabrykę sesji
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tworzymy bazową klasę dla modeli
Base = declarative_base()

# Dependency dla FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()