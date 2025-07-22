# src/services/nutrition.py

import os
from dotenv import load_dotenv
import httpx

load_dotenv()
API_KEY  = os.getenv("FDC_API_KEY")
BASE_URL = os.getenv("FDC_BASE_URL", "https://api.nal.usda.gov/fdc/v1")

# Map USDA nutrient names → our Nutrition model fields
NUTRIENT_MAP = {
    # Macronutrients
    "Energy":                           "calories",     # kcal
    "Protein":                          "protein",      # g
    "Carbohydrate, by difference":      "carbs",        # g
    "Total lipid (fat)":                "fat",          # g
    "Sugars, total":                    "sugars",       # g

    # Cholesterol
    "Cholesterol":                      "cholesterol",  # mg

    # Detailed fatty acids
    "Fatty acids, total saturated":    "sat_fat",      # g
    "Fatty acids, total monounsaturated": "mono_fat",  # g
    "Fatty acids, total polyunsaturated":  "poly_fat", # g
    "Fatty acids, total trans":         "trans_fat",    # g

    # Vitamins
    "Vitamin A, RAE":                   "vitamin_a",    # µg
    "Beta-carotene":                    "beta_carotene",# µg
    "Thiamin":                          "vitamin_b1",   # mg
    "Riboflavin":                       "vitamin_b2",   # mg
    "Niacin":                           "vitamin_b3",   # mg
    "Pantothenic acid":                 "vitamin_b5",   # mg
    "Vitamin B-6":                      "vitamin_b6",   # mg
    "Folate, total":                    "vitamin_b9",   # µg
    "Vitamin B-12":                     "vitamin_b12",  # µg
    "Vitamin C, total ascorbic acid":   "vitamin_c",    # mg
    "Vitamin D (D2 + D3)":              "vitamin_d",    # µg
    "Vitamin E (alpha-tocopherol)":     "vitamin_e",    # mg
    "Vitamin K (phylloquinone)":        "vitamin_k",    # µg

    # Minerals
    "Calcium, Ca":                      "calcium",      # mg
    "Iron, Fe":                         "iron",         # mg
    "Magnesium, Mg":                    "magnesium",    # mg
    "Phosphorus, P":                    "phosphorus",   # mg
    "Potassium, K":                     "potassium",    # mg
    "Sodium, Na":                       "sodium",       # mg
    "Zinc, Zn":                         "zinc",         # mg
    "Copper, Cu":                       "copper",       # mg
    "Manganese, Mn":                    "manganese",    # mg
    "Selenium, Se":                     "selenium",     # µg
    "Chromium, Cr":                     "chromium",     # µg
    "Molybdenum, Mo":                   "molybdenum",   # µg
    "Fluoride, F":                      "fluoride",     # mg
}

# List all model fields to initialize defaults
ALL_FIELDS = [
    "calories", "protein", "carbs", "fat", "sugars",
    "cholesterol", "sat_fat", "mono_fat", "poly_fat", "trans_fat",
    "vitamin_a", "beta_carotene", "vitamin_b1", "vitamin_b2",
    "vitamin_b3", "vitamin_b5", "vitamin_b6", "vitamin_b9",
    "vitamin_b12", "vitamin_c", "vitamin_d", "vitamin_e",
    "vitamin_k", "calcium", "iron", "magnesium", "phosphorus",
    "potassium", "sodium", "zinc", "copper", "manganese",
    "selenium", "chromium", "molybdenum", "fluoride"
]

async def fetch_nutrition(food_name: str) -> dict:
    """
    Search FDC for food_name, fetch its fdcId, then pull full nutrient details.
    Returns a dict mapping our Nutrition field names → float values.
    """
    # Initialize all nutrients to 0.0
    result = { field: 0.0 for field in ALL_FIELDS }

    async with httpx.AsyncClient() as client:
        # 1) Search for the food
        search = await client.get(
            f"{BASE_URL}/foods/search",
            params={"api_key": API_KEY, "query": food_name, "pageSize": 1}
        )
        search.raise_for_status()
        foods = search.json().get("foods", [])
        if not foods:
            return result

        fdc_id = foods[0].get("fdcId")
        # 2) Fetch nutrient details
        detail = await client.get(
            f"{BASE_URL}/food/{fdc_id}",
            params={"api_key": API_KEY}
        )
        detail.raise_for_status()
        nutrients = detail.json().get("foodNutrients", [])

    # 3) Map USDA nutrient names → our fields
    for nut in nutrients:
        name = nut.get("nutrientName") or nut.get("nutrient", {}).get("name")
        value = nut.get("value") or nut.get("amount") or 0.0
        field = NUTRIENT_MAP.get(name)
        if field:
            result[field] = float(value)

    return result
