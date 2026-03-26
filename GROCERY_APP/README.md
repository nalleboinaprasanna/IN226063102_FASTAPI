# FreshMart Grocery Delivery API

A FastAPI-based backend application that simulates a grocery delivery system.  
It allows users to browse items, manage cart, place orders, and schedule deliveries.


## 🚀 Features

- 🛒 Item Management (CRUD)
- 🔍 Search, Filter, Sort, Pagination
- 🧾 Order Placement with Pricing Logic
- 🛍️ Cart System with Checkout
- 📦 Delivery Slot Handling
- 💰 Bulk Order Discounts


## 🛠️ Tech Stack

- **Backend:** FastAPI
- **Language:** Python
- **Validation:** Pydantic
- **Server:** Uvicorn


## 📁 Project Structure
main.py
requirements.txt
README.md
output_screenshots



## ▶️ How to Run

### 1. Install dependencies
pip install -r requirements.txt

## 2. Run server
uvicorn main:app --reload

## 3.Open API Docs
http://127.0.0.1:8000/docs

📌 API Modules
🥦 Items
Get all items
Get item by ID
Add / Update / Delete items
Search, Filter, Sort, Pagination


🛒 Cart
Add to cart
View cart
Remove item
Checkout


📦 Orders
Place order
View orders
Search / Sort / Pagination


💡 Special Features
Bulk order discount (8% for quantity ≥ 10)
Delivery charges:
Morning: ₹40
Evening: ₹60
Self pickup: ₹0
Stock validation before ordering
