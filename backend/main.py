# backend/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import SQLModel, Session, select, func
from sqlalchemy import text
from sqlalchemy import desc
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone

from src.database import engine, get_session
from src.models import FoodLog, FoodLogCreate, FoodLogRead, Nutrition
from src.services.nutrition import fetch_nutrition

# Alias for clarity in summary queries
NutritionModel = Nutrition

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
    # 1) Insert base FoodLog
    log = FoodLog.from_orm(payload)
    session.add(log)
    session.commit()
    session.refresh(log)

    # 2) Fetch nutrition data
    nutrition_data = await fetch_nutrition(payload.food_name)
    if not nutrition_data:
        raise HTTPException(
            status_code=404,
            detail=f"No nutrition data found for '{payload.food_name}'"
        )

    # 3) Insert linked Nutrition record
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
        start = datetime.combine(log_date, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        stmt = stmt.where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        )
    stmt = stmt.order_by(FoodLog.timestamp).offset(skip).limit(limit)
    return session.exec(stmt).all()


# --- Phase 3.3: SUMMARY ENDPOINTS ---

@app.get("/summaries/daily")
def daily_summary(
    session: Session = Depends(get_session),
    summary_date: date = Query(..., alias="date")
):
    start = datetime.combine(summary_date, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    # Totals for the day
    agg = session.exec(
        select(
            func.sum(NutritionModel.calories).label("calories"),
            func.sum(NutritionModel.protein).label("protein"),
            func.sum(NutritionModel.carbs).label("carbs"),
            func.sum(NutritionModel.fat).label("fat")
        ).join(FoodLog).where(
            NutritionModel.foodlog_id == FoodLog.id,
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        )
    ).one()

    # Top 3 foods by calories
    top_foods = session.exec(
        select(
            FoodLog.food_name,
            func.sum(NutritionModel.calories).label("total_calories")
        ).join(NutritionModel).where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        ).group_by(FoodLog.food_name)
         .order_by(desc("total_calories"))
         .limit(3)
    ).all()

    return {
        "date": summary_date,
        "totals": {
            "calories": agg.calories or 0,
            "protein": agg.protein or 0,
            "carbs": agg.carbs or 0,
            "fat": agg.fat or 0
        },
        "top_foods": [
            {"food_name": name, "calories": total}
            for name, total in top_foods
        ]
    }


@app.get("/summaries/weekly")
def weekly_summary(
    session: Session = Depends(get_session),
    start_date: date = Query(..., alias="start_date")
):
    """
    Returns aggregated totals and top foods for the 7-day period
    starting on `start_date` (inclusive).
    """
    start = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end = start + timedelta(days=7)

    # Totals for the week
    agg = session.exec(
        select(
            func.sum(NutritionModel.calories),
            func.sum(NutritionModel.protein),
            func.sum(NutritionModel.carbs),
            func.sum(NutritionModel.fat)
        ).join(FoodLog).where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        )
    ).one()

    # Top 3 foods by calories over the week
    top_foods = session.exec(
        select(
            FoodLog.food_name,
            func.sum(NutritionModel.calories).label("total_calories")
        ).join(NutritionModel).where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        ).group_by(FoodLog.food_name)
         .order_by(desc("total_calories"))
         .limit(3)
    ).all()

    return {
        "week_start": start_date,
        "week_end": (start_date + timedelta(days=6)),
        "totals": {
            "calories": agg[0] or 0,
            "protein": agg[1] or 0,
            "carbs": agg[2] or 0,
            "fat": agg[3] or 0
        },
        "top_foods": [
            {"food_name": name, "calories": total}
            for name, total in top_foods
        ]
    }


@app.get("/summaries/monthly")
def monthly_summary(
    session: Session = Depends(get_session),
    year: int = Query(..., ge=1900, le=datetime.now().year),
    month: int = Query(..., ge=1, le=12)
):
    start = datetime(year, month, 1, tzinfo=timezone.utc)
    end = datetime(year + (month // 12), (month % 12) + 1, 1, tzinfo=timezone.utc)

    agg = session.exec(
        select(
            func.sum(NutritionModel.calories),
            func.sum(NutritionModel.protein),
            func.sum(NutritionModel.carbs),
            func.sum(NutritionModel.fat)
        ).join(FoodLog).where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        )
    ).one()

    return {
        "year": year,
        "month": month,
        "totals": {
            "calories": agg[0] or 0,
            "protein": agg[1] or 0,
            "carbs": agg[2] or 0,
            "fat": agg[3] or 0
        }
    }


@app.get("/summaries/yearly")
def yearly_summary(
    session: Session = Depends(get_session),
    year: int = Query(..., ge=1900, le=datetime.now().year)
):
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

    agg = session.exec(
        select(
            func.sum(NutritionModel.calories),
            func.sum(NutritionModel.protein),
            func.sum(NutritionModel.carbs),
            func.sum(NutritionModel.fat)
        ).join(FoodLog).where(
            FoodLog.timestamp >= start,
            FoodLog.timestamp < end
        )
    ).one()

    return {
        "year": year,
        "totals": {
            "calories": agg[0] or 0,
            "protein": agg[1] or 0,
            "carbs": agg[2] or 0,
            "fat": agg[3] or 0
        }
    }
