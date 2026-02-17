from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import sys

# Load environment variables from .env
load_dotenv()

# Fetch Supabase PostgreSQL credentials
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Validate required environment variables
required_vars = {
    "user": USER,
    "password": PASSWORD,
    "host": HOST,
    "port": PORT,
    "dbname": DBNAME
}

missing_vars = [key for key, value in required_vars.items() if not value]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}", file=sys.stderr)
    print("Please set these environment variables in your Render dashboard or .env file", file=sys.stderr)
    sys.exit(1)

# Construct the SQLAlchemy connection string for PostgreSQL
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
