# scripts/check_foodlog.py

import sys
# Explicitly add your project root so Python can find src/
sys.path.append(r"C:\Users\owner\Documents\GitHub\food-tracker-ai")

from pathlib import Path
from sqlmodel import Session, select
from src.database import engine
from src.models import FoodLog, Nutrition

with Session(engine) as session:
    logs = session.exec(select(FoodLog)).all()
    for log in logs:
        nut = session.exec(
            select(Nutrition).where(Nutrition.foodlog_id == log.id)
        ).one_or_none()
        print(f"FoodLog #{log.id} ({log.food_name}):")
        if nut:
            print(" ", nut)
        else:
            print("   no nutrition data found")
