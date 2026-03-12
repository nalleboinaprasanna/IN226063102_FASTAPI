from fastapi import FastAPI
 
app = FastAPI()

products = [
     {'id': 1, 'name': 'Wireless Mouse', 'price': 499,  'category': 'Electronics', 'in_stock': True },
    {'id': 2, 'name': 'Notebook',       'price':  99,  'category': 'Stationery',  'in_stock': True },
    {'id': 3, 'name': 'USB Hub',         'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set',          'price':  49, 'category': 'Stationery',  'in_stock': True },
    {'id':5,  'name':'Laptop Stand',    'price':1299,  'category':'Electronics',  'in_stock':True},
    {'id':6,  'name':'Mechanical Keyboard','price':2499,'category':'Electronics', 'in_stock':True},
    {'id':7,  'name' :'Webcam',          'price':1899,'category':'Electronics',   'in_stock':False}
]
#added 3 products
#1. to display all products

@app.get('/products')
def get_all_products():
    return {'products': products, 'total': len(products)}

#2.filter by category
@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]

    if not result:
        return {"error": "No products found in this category"}

    return {
        "category": category_name,
        "products": result,
        "total": len(result)
    }

#3.show only instock products
@app.get("/products/in-stock")
def get_instock_products():
    result = [p for p in products if p['in_stock'] == True]

    return {
        "products": result,
        "total": len(result)
    }



#best deal
@app.get("/products/deals") 
def get_deals():
     cheapest = min(products, key=lambda p: p["price"]) 
     expensive = max(products, key=lambda p: p["price"]) 
     return { "best_deal": cheapest, 
             "premium_pick": expensive 
             }

#4.Build a Store Info Endpoint
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p

    return {"error": "Product not found"}

#5.search products by name
@app.get("/products/search/{name}")
def search_product(name: str):
    result = [p for p in products if name.lower() in p["name"].lower()]

    if not result:
        return {"error": "Product not found"}

    return {
        "results": result,
        "total": len(result)
    }