from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
import cachetools

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Cache setup
cache = cachetools.TTLCache(maxsize=100, ttl=60)  # TTL 60 seconds

# Models
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

# Pydantic schemas
class ItemCreate(BaseModel):
    name: str
    description: str

class ItemRead(ItemCreate):
    id: int

app = FastAPI()

# CRUD endpoints
@app.post("/items/", response_model=ItemRead)
def create_item(item: ItemCreate):
    db = SessionLocal()
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    cache.clear()
    return db_item

@app.get("/items/{item_id}", response_model=ItemRead)
def read_item(item_id: int):
    if item_id in cache:
        return cache[item_id]
    db = SessionLocal()
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    cache[item_id] = db_item
    return db_item

@app.put("/items/{item_id}", response_model=ItemRead)
def update_item(item_id: int, item: ItemCreate):
    db = SessionLocal()
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db_item.name = item.name
    db_item.description = item.description
    db.commit()
    cache.pop(item_id, None)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    db = SessionLocal()
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    cache.pop(item_id, None)
    return {"ok": True}

# To auto-create tables (if not using Alembic upgrade):
# if __name__ == "__main__":
#     Base.metadata.create_all(bind=engine)
