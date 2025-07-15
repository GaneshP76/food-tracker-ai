# src/models.py

from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional

class FoodLogBase(SQLModel):
    food_name: str
    quantity: float

class FoodLogCreate(FoodLogBase):
    pass

class FoodLogRead(FoodLogBase):
    id: int
    timestamp: datetime

class FoodLog(FoodLogBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Use a default_factory that returns a timezone-aware UTC datetime
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
