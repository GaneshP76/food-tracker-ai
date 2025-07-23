from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import SQLModel, Session, select, func
from sqlalchemy import text
from sqlalchemy import desc
from typing import List, Optional
from datetime import date, datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo

from src.database import engine, get_session
from src.models import FoodLog, FoodLogCreate, FoodLogRead, Nutrition
from src.services.nutrition import fetch_nutrition
from src.services.feedback import generate_feedback

# Constant for UTC timezone using built-in timezone
UTC = timezone.utc

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create or update tables on startup
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"message": "Hello, Food Tracker!"}

@app.get("/health")
def health_check(session: Session = Depends(get_session)):
    try:
        session.exec(text("SELECT 1"))
        return {"status": "db ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/foodlogs/", response_model=FoodLogRead, status_code=201)
async def create_foodlog(
    payload: FoodLogCreate,
    session: Session = Depends(get_session),
):
    # Insert base FoodLog
    log = FoodLog.from_orm(payload)
    session.add(log)
    session.commit()
    session.refresh(log)

    # Fetch nutrition data
    nutrition_data = await fetch_nutrition(payload.food_name)
    if not nutrition_data:
        raise HTTPException(
            status_code=404,
            detail=f"No nutrition data found for '{payload.food_name}'"
        )

    # Insert linked Nutrition record
    nut = Nutrition(foodlog_id=log.id, **nutrition_data)
    session.add(nut)
    session.commit()

    return log

@app.get("/foodlogs/", response_model=List[FoodLogRead])
def read_foodlogs(
    session: Session = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    log_date: Optional[date] = Query(None, alias="date")
):
    stmt = select(FoodLog)
    if log_date:
        start = datetime.combine(log_date, time.min).replace(tzinfo=UTC)
        end = start + timedelta(days=1)
        stmt = stmt.where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        )
    stmt = stmt.order_by(FoodLog.timestamp).offset(skip).limit(limit)
    return session.exec(stmt).all()

# --- Helper functions for summaries ---

def get_daily_summary(session: Session, summary_date: date, tz: str):
    local_zone = ZoneInfo(tz)
    start_local = datetime.combine(summary_date, time.min).replace(tzinfo=local_zone)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(UTC)
    end_utc = end_local.astimezone(UTC)

    agg = session.exec(
        select(
            func.sum(Nutrition.calories).label("calories"),
            func.sum(Nutrition.protein).label("protein"),
            func.sum(Nutrition.carbs).label("carbs"),
            func.sum(Nutrition.fat).label("fat")
        )
        .join(FoodLog)
        .where(
            FoodLog.timestamp >= start_utc,
            FoodLog.timestamp < end_utc
        )
    ).one()

    top_foods = session.exec(
        select(
            FoodLog.food_name,
            func.sum(Nutrition.calories).label("total_calories")
        )
        .join(Nutrition)
        .where(
            FoodLog.timestamp >= start_utc,
            FoodLog.timestamp < end_utc
        )
        .group_by(FoodLog.food_name)
        .order_by(desc("total_calories"))
        .limit(3)
    ).all()

    return {
        "date": summary_date,
        "timezone": tz,
        "totals": {
            "calories": agg.calories or 0,
            "protein": agg.protein or 0,
            "carbs": agg.carbs or 0,
            "fat": agg.fat or 0
        },
        "top_foods": [
            {"food_name": n, "calories": c} for n, c in top_foods
        ]
    }

@app.get("/summaries/daily")
def daily_summary(
    session: Session = Depends(get_session),
    summary_date: date = Query(..., alias="date"),
    tz: str = Query("UTC", description="IANA timezone name, e.g. 'America/Chicago'")
):
    return get_daily_summary(session, summary_date, tz)

@app.get("/summaries/weekly")
def weekly_summary(
    session: Session = Depends(get_session),
    start_date: date = Query(..., alias="start_date"),
    tz: str = Query("UTC", description="IANA timezone name, e.g. 'Europe/London'")
):
    local_zone = ZoneInfo(tz)
    start_local = datetime.combine(start_date, time.min).replace(tzinfo=local_zone)
    end_local = start_local + timedelta(days=7)
    start_utc = start_local.astimezone(UTC)
    end_utc = end_local.astimezone(UTC)

    agg = session.exec(
        select(
            func.sum(Nutrition.calories).label("calories"),
            func.sum(Nutrition.protein).label("protein"),
            func.sum(Nutrition.carbs).label("carbs"),
            func.sum(Nutrition.fat).label("fat")
        )
        .join(FoodLog)
        .where(
            FoodLog.timestamp >= start_utc,
            FoodLog.timestamp < end_utc
        )
    ).one()

    top_foods = session.exec(
        select(
            FoodLog.food_name,
            func.sum(Nutrition.calories).label("total_calories")
        )
        .join(Nutrition)
        .where(
            FoodLog.timestamp >= start_utc,
            FoodLog.timestamp < end_utc
        )
        .group_by(FoodLog.food_name)
        .order_by(desc("total_calories"))
        .limit(3)
    ).all()

    return {
        "week_start": start_date,
        "week_end": start_date + timedelta(days=6),
        "timezone": tz,
        "totals": {
            "calories": agg.calories or 0,
            "protein": agg.protein or 0,
            "carbs": agg.carbs or 0,
            "fat": agg.fat or 0
        },
        "top_foods": [{"food_name": n, "calories": c} for n, c in top_foods]
    }

from src.services.feedback import test_ollama_connection

@app.get("/health/ollama")
async def ollama_health_check():
    """Check Ollama service health"""
    return await test_ollama_connection()

@app.get("/feedback/daily")
async def daily_feedback(
    session: Session = Depends(get_session),
    summary_date: date = Query(..., alias="date"),
    tz: str = Query("UTC", description="IANA timezone (e.g. America/Chicago)")
):
    # Generate feedback based on daily summary
    summary = get_daily_summary(session, summary_date, tz)
    tip_prompt = (
        f"You’re a friendly, supportive nutrition coach. On {summary_date} ({tz}), "
        f"the user consumed {summary['totals']['calories']} kcal, {summary['totals']['protein']} g protein, "
        f"{summary['totals']['carbs']} g carbs, and {summary['totals']['fat']} g fat. "
        "1) Provide a brief health summary comparing intake to goals.\n"
        "2) Suggest two balanced meal ideas (with rough macro breakdowns) to meet remaining targets.\n"
        "3) Offer one concise, actionable tip to close the top nutrient gap."
    )
    tip = await generate_feedback(tip_prompt)
    return {"date": summary_date, "timezone": tz, "tip": tip}
