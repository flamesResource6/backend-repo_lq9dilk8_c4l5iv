import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents, db
from schemas import Product, Order, OrderItem

app = FastAPI(title="Chips Commerce API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductCreate(Product):
    pass

class OrderCreate(Order):
    pass

@app.get("/")
def read_root():
    return {"message": "Chips Commerce Backend Running"}

@app.get("/schema")
def get_schema():
    # Allows the database viewer to inspect schemas
    return {
        "user": "User",
        "product": "Product",
        "order": "Order"
    }

@app.get("/api/products", response_model=List[Product])
async def list_products(category: Optional[str] = None):
    filter_q = {"category": category} if category else {}
    docs = await get_documents("product", filter_q, limit=100)
    return docs

@app.post("/api/products", response_model=dict)
async def create_product(product: ProductCreate):
    doc = await create_document("product", product.dict())
    return doc

@app.get("/api/seed")
async def seed_products():
    # Insert some delicious chips products if collection is empty
    existing = await get_documents("product", {}, limit=1)
    if existing:
        return {"inserted": 0, "message": "Products already seeded"}

    chips = [
        {
            "title": "Classic Salted Potato Chips",
            "description": "Crispy, thin-cut potatoes with a perfect salty crunch.",
            "price": 2.99,
            "category": "potato",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?w=800",
            "rating": 4.6,
            "brand": "CrunchCraft",
            "weight_grams": 150
        },
        {
            "title": "Spicy Tortilla Chips",
            "description": "Stone-ground corn chips dusted with fiery chili and lime.",
            "price": 3.49,
            "category": "tortilla",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1604908176997-4316c288032e?w=800",
            "rating": 4.7,
            "brand": "FuegoBite",
            "weight_grams": 170
        },
        {
            "title": "Cheddar Ridges",
            "description": "Ridged chips blasted with bold cheddar cheese flavor.",
            "price": 3.19,
            "category": "potato",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1613478223719-3c84c68ffd4a?w=800",
            "rating": 4.4,
            "brand": "RidgeRush",
            "weight_grams": 160
        },
        {
            "title": "Sea Salt Kettle Chips",
            "description": "Thick-cut kettle chips cooked in small batches for extra crunch.",
            "price": 3.99,
            "category": "kettle",
            "in_stock": True,
            "image_url": "https://images.unsplash.com/photo-1585238342028-4bbc3e2f5b42?w=800",
            "rating": 4.8,
            "brand": "KettleCo",
            "weight_grams": 200
        }
    ]

    inserted = 0
    for c in chips:
        await create_document("product", c)
        inserted += 1

    return {"inserted": inserted}

@app.post("/api/orders", response_model=dict)
async def create_order(order: OrderCreate):
    # Basic validation for stock and price
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    # Recalculate subtotal to prevent manipulation
    subtotal = 0.0
    for item in order.items:
        subtotal += item.price * item.quantity
    order.subtotal = round(subtotal, 2)

    doc = await create_document("order", order.dict())
    return doc

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
