

import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

# 1. Load .env
load_dotenv()

# 2. Read the connection string (fallback to SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./foodtracker.db")

# 3. Create the SQLModel/SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# 4. Session dependency for FastAPI
def get_session():
    with Session(engine) as session:
        yield session
