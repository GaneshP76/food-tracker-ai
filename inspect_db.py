# inspect_db.py
from src.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
print("Tables in the database:", inspector.get_table_names())
