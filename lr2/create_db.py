# create_db.py
from main import Base, engine

# Створюємо всі таблиці, визначені в Base.metadata
Base.metadata.create_all(bind=engine)
print("База даних та таблиці створені.")
