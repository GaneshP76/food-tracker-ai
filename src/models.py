from sqlmodel import SQLModel, Field, Relationship
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # One-to-one link to Nutrition
    nutrition: Optional["Nutrition"] = Relationship(back_populates="food_log")


class Nutrition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    foodlog_id: int = Field(foreign_key="foodlog.id")

    # Macronutrients
    calories: float = Field(default=0.0, ge=0, description="Calories (kcal)")
    protein: float = Field(default=0.0, ge=0, description="Protein (g)")
    carbs: float = Field(default=0.0, ge=0, description="Carbohydrates (g)")
    fat: float = Field(default=0.0, ge=0, description="Fat (g)")

    # Micronutrients – Vitamins
    vitamin_a: Optional[float] = Field(default=0.0, ge=0, description="Vitamin A (µg)")
    beta_carotene: Optional[float] = Field(default=0.0, ge=0, description="Beta-carotene (µg)")
    vitamin_b1: Optional[float] = Field(default=0.0, ge=0, description="Vitamin B1 (mg)")
    vitamin_b2: Optional[float] = Field(default=0.0, ge=0, description="Vitamin B2 (mg)")
    vitamin_b3: Optional[float] = Field(default=0.0, ge=0, description="Vitamin B3 (mg)")
    vitamin_b5: Optional[float] = Field(default=0.0, ge=0, description="Vitamin B5 (mg)")
    vitamin_b6: Optional[float] = Field(default=0.0, ge=0, description="Vitamin B6 (mg)")
    vitamin_b9: Optional[float] = Field(default=0.0, ge=0, description="Folate (Vitamin B9) (µg)")
    vitamin_b12: Optional[float] = Field(default=0.0, ge=0, description="Vitamin B12 (µg)")
    vitamin_c: Optional[float] = Field(default=0.0, ge=0, description="Vitamin C (mg)")
    vitamin_d: Optional[float] = Field(default=0.0, ge=0, description="Vitamin D (µg)")
    vitamin_e: Optional[float] = Field(default=0.0, ge=0, description="Vitamin E (mg)")
    vitamin_k: Optional[float] = Field(default=0.0, ge=0, description="Vitamin K (µg)")

    # Micronutrients – Minerals
    calcium: Optional[float] = Field(default=0.0, ge=0, description="Calcium (mg)")
    iron: Optional[float] = Field(default=0.0, ge=0, description="Iron (mg)")
    magnesium: Optional[float] = Field(default=0.0, ge=0, description="Magnesium (mg)")
    phosphorus: Optional[float] = Field(default=0.0, ge=0, description="Phosphorus (mg)")
    potassium: Optional[float] = Field(default=0.0, ge=0, description="Potassium (mg)")
    sodium: Optional[float] = Field(default=0.0, ge=0, description="Sodium (mg)")
    zinc: Optional[float] = Field(default=0.0, ge=0, description="Zinc (mg)")
    copper: Optional[float] = Field(default=0.0, ge=0, description="Copper (mg)")
    manganese: Optional[float] = Field(default=0.0, ge=0, description="Manganese (mg)")
    selenium: Optional[float] = Field(default=0.0, ge=0, description="Selenium (µg)")
    chromium: Optional[float] = Field(default=0.0, ge=0, description="Chromium (µg)")
    molybdenum: Optional[float] = Field(default=0.0, ge=0, description="Molybdenum (µg)")
    fluoride: Optional[float] = Field(default=0.0, ge=0, description="Fluoride (mg)")

    # Back-reference to FoodLog
    food_log: "FoodLog" = Relationship(back_populates="nutrition")
