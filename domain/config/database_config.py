from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables
load_dotenv()

# Get the environment variables
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

# Mount PostgreSQL connection URL
DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

# 1. Initializes the pure SQLAlchemy Engine
# echo=False prevents that all SQL queries from being printed in the terminal (change for True if you need to do debugging)
engine = create_engine(DATABASE_URI, echo=False)

# 2. Creates the Session Factory
# autocommit=False and autoflush=False are recommended standards for integrations with FastAPI
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Declarative base that replaces the old "db.Model" in the custom classes
Base = declarative_base()

# Utilitary function (Dependency) in order to FastAPI open and close connections automatically through requests
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
