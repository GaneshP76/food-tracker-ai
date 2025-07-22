# scripts/test_nutrition.py

import os
import asyncio
import argparse
from dotenv import load_dotenv
import httpx

load_dotenv()
API_KEY = os.getenv("FDC_API_KEY")
BASE_URL = os.getenv("FDC_BASE_URL", "https://api.nal.usda.gov/fdc/v1")

# 1) Accept the food name on the command line:
parser = argparse.ArgumentParser(
    description="Fetch USDA nutrient data for a given food name"
)
parser.add_argument("food_name", help="Name of the food to search (e.g. apple, banana)")
args = parser.parse_args()
QUERY = args.food_name

async def main():
    async with httpx.AsyncClient() as client:
        # 2) Search for the supplied food name
        search_resp = await client.get(
            f"{BASE_URL}/foods/search",
            params={"api_key": API_KEY, "query": QUERY, "pageSize": 1}
        )
        search_resp.raise_for_status()
        foods = search_resp.json().get("foods", [])
        if not foods:
            print(f"No results for “{QUERY}”")
            return

        food = foods[0]
        fdc_id = food.get("fdcId") or food.get("fdcid")
        print(f"Found: {food.get('description')} (fdcId={fdc_id})\n")

        # 3) Fetch its nutrient details
        detail_resp = await client.get(
            f"{BASE_URL}/food/{fdc_id}",
            params={"api_key": API_KEY}
        )
        detail_resp.raise_for_status()
        nutrients = detail_resp.json().get("foodNutrients", [])

        if not nutrients:
            print("No nutrient data returned.")
            return

        # 4) Print them all (or slice if you want just the first few)
        for nut in nutrients:
            name = nut.get("nutrientName") or nut.get("nutrient", {}).get("name")
            value = nut.get("value") or nut.get("amount")
            unit = nut.get("unitName") or nut.get("nutrient", {}).get("unitName")
            print(f" • {name}: {value} {unit}")

if __name__ == "__main__":
    asyncio.run(main())
