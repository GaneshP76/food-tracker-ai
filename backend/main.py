from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import SQLModel, Session, select
from sqlalchemy import text
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone

from src.database import engine, get_session
from src.models import FoodLog, FoodLogCreate, FoodLogRead

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    SQLModel.metadata.create_all(engine)
    yield
    # Shutdown: add any cleanup logic here if needed

# Initialize FastAPI with lifespan handler
app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Hello, Food Tracker!"}

@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    """
    A simple DB-test endpoint: runs SELECT 1 to verify connectivity.
    """
    try:
        session.exec(text("SELECT 1"))
        return {"status": "db ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post(
    "/foodlogs/",
    response_model=FoodLogRead,
    status_code=201
)
def create_foodlog(
    payload: FoodLogCreate,
    session: Session = Depends(get_session),
):
    """
    Create a new food log entry.
    """
    log = FoodLog.from_orm(payload)
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

@app.get(
    "/foodlogs/",
    response_model=List[FoodLogRead]
)
def read_foodlogs(
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    log_date: Optional[date] = Query(None, alias="date")
):
    """
    Retrieve food log entries, with optional pagination and date filter.
    - skip: number of records to skip
    - limit: max records to return (1-1000)
    - date: filter logs on a specific date (YYYY-MM-DD)
    """
    statement = select(FoodLog)
    # Apply date filter if provided
    if log_date:
        start = datetime.combine(log_date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        statement = statement.where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        )
    # Order and paginate
    statement = statement.order_by(FoodLog.timestamp).offset(skip).limit(limit)
    results = session.exec(statement).all()
    return results
