from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATABASE_DIR / "finance.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

DATABASE_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def initialize_database() -> None:
    """Create all database tables defined in our SQLAlchemy models."""

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    initialize_database()
    print("Database initialization successful.")
    print(f"Database: {DATABASE_PATH}")