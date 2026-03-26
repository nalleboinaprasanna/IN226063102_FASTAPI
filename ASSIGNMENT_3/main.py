from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# Pydantic classes for input validation
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=100)
    delivery_address: str = Field(..., min_length=10)

class NewProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    in_stock: bool = True

# Data storage
products_db = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook', 'price': 99, 'category': 'Stationery', 'in_stock': True},
    {'id': 3, 'name': 'USB Hub', 'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set', 'price': 49, 'category': 'Stationery', 'in_stock': True},
]

orders_list = []
next_order_id = 1

# Functions
def get_product_by_id(pid: int):
    for item in products_db:
        if item['id'] == pid:
            return item
    return None

def get_cost(item: dict, qty: int) -> int:
    return item['price'] * qty

def do_filter(cat=None, min_p=None, max_p=None, in_stock_val=None):
    res = []
    for p in products_db:
        match = True
        if cat is not None and p['category'] != cat:
            match = False
        if min_p is not None and p['price'] < min_p:
            match = False
        if max_p is not None and p['price'] > max_p:
            match = False
        if in_stock_val is not None and p['in_stock'] != in_stock_val:
            match = False
        if match:
            res.append(p)
    return res

# Routes
@app.get('/')
def main_page():
    return {'message': 'Welcome to our E-commerce API'}

@app.get('/products')
def fetch_all_products():
    return {'products': products_db, 'total': len(products_db)}

@app.get('/products/filter')
def filter_items(
    category: str = Query(None, description='Electronics or Stationery'),
    min_price: int = Query(None, description='Minimum price'),
    max_price: int = Query(None, description='Maximum price'),
    in_stock: bool = Query(None, description='True = in stock only'),
):
    filtered = do_filter(category, min_price, max_price, in_stock)
    return {'filtered_products': filtered, 'count': len(filtered)}

@app.get('/products/compare')
def compare_two_products(
    product_id_1: int = Query(..., description='First product ID'),
    product_id_2: int = Query(..., description='Second product ID'),
):
    prod1 = get_product_by_id(product_id_1)
    prod2 = get_product_by_id(product_id_2)
    
    if prod1 is None:
        return {'error': f'Product {product_id_1} not found'}
    if prod2 is None:
        return {'error': f'Product {product_id_2} not found'}
        
    if prod1['price'] < prod2['price']:
        best_val = prod1
    else:
        best_val = prod2
        
    return {
        'product_1': prod1,
        'product_2': prod2,
        'better_value': best_val['name'],
        'price_diff': abs(prod1['price'] - prod2['price']),
    }

@app.post('/products')
def create_new_product(new_product: NewProduct, response: Response):
    # check exists
    for p in products_db:
        if p['name'].lower() == new_product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'error': 'Product with this name already exists'}

    new_id = 1
    if len(products_db) > 0:
        new_id = max(p['id'] for p in products_db) + 1

    prod = {
        'id': new_id,
        'name': new_product.name,
        'price': new_product.price,
        'category': new_product.category,
        'in_stock': new_product.in_stock,
    }
    products_db.append(prod)
    response.status_code = status.HTTP_201_CREATED
    return {'message': 'Product added', 'product': prod}

@app.delete('/products/{product_id}')
def remove_product(product_id: int, response: Response):
    prod = get_product_by_id(product_id)
    if prod is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
        
    products_db.remove(prod)
    return {'message': f"Product '{prod['name']}' deleted"}

@app.get("/products/audit")
def audit_products():
    in_stock_items = []
    out_stock_items = []
    for p in products_db:
        if p["in_stock"]:
            in_stock_items.append(p)
        else:
            out_stock_items.append(p)

    val = 0
    for p in in_stock_items:
        val += p["price"] * 10

    max_p = products_db[0]
    for p in products_db:
        if p["price"] > max_p["price"]:
            max_p = p

    out_names = []
    for p in out_stock_items:
        out_names.append(p["name"])

    return {
        "total_products": len(products_db),
        "in_stock_count": len(in_stock_items),
        "out_of_stock_names": out_names,
        "total_stock_value": val,
        "most_expensive": {
            "name": max_p["name"],
            "price": max_p["price"]
        }
    }

@app.put("/products/discount")
def apply_discount(category: str, discount_percent: int):
    updated_items = []
    for p in products_db:
        if p["category"] == category:
            p["price"] = int(p["price"] * (1 - discount_percent / 100))
            updated_items.append(p)

    if len(updated_items) == 0:
        return {"message": f"No products found in category {category}"}

    return {
        "message": f"{discount_percent}% discount applied",
        "updated_count": len(updated_items),
        "updated_products": updated_items
    }

@app.get('/products/{product_id}')
def fetch_product(product_id: int):
    prod = get_product_by_id(product_id)
    if prod is None:
        return {'error': 'Product not found'}
    return {'product': prod}

@app.post('/orders')
def create_order(order_data: OrderRequest):
    global next_order_id
    prod = get_product_by_id(order_data.product_id)
    
    if prod is None:
        return {'error': 'Product not found'}
    if not prod['in_stock']:
        return {'error': f"{prod['name']} is out of stock"}

    tot = get_cost(prod, order_data.quantity)

    new_order = {
        'order_id': next_order_id,
        'customer_name': order_data.customer_name,
        'product': prod['name'],
        'quantity': order_data.quantity,
        'delivery_address': order_data.delivery_address,
        'total_price': tot,
        'status': 'confirmed',
    }
    orders_list.append(new_order)
    next_order_id += 1
    return {'message': 'Order placed successfully', 'order': new_order}

@app.put('/products/{product_id}')
def edit_product(
    product_id: int,
    response: Response,
    in_stock: bool = Query(None, description='Update stock status'),
    price: int = Query(None, description='Update price'),
):
    prod = get_product_by_id(product_id)
    if not prod:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}

    if in_stock is not None:
        prod['in_stock'] = in_stock
    if price is not None:
        prod['price'] = price

    return {'message': 'Product updated', 'product': prod}

@app.get('/orders')
def fetch_all_orders():
    return {'orders': orders_list, 'total_orders': len(orders_list)}