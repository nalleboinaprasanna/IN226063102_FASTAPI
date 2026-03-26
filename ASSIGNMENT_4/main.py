from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

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

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

products_db = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook', 'price': 99, 'category': 'Stationery', 'in_stock': True},
    {'id': 3, 'name': 'USB Hub', 'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set', 'price': 49, 'category': 'Stationery', 'in_stock': True},
]

orders_list = []
global_order_id = 1
shopping_cart = []

def search_prod(pid: int):
    for x in products_db:
        if x['id'] == pid:
            return x
    return None

def calc_price(price: int, q: int) -> int:
    return price * q

def do_filter(cat=None, min_p=None, max_p=None, stock=None):
    res = []
    for p in products_db:
        if cat and p['category'] != cat:
            continue
        if min_p and p['price'] < min_p:
            continue
        if max_p and p['price'] > max_p:
            continue
        if stock is not None and p['in_stock'] != stock:
            continue
        res.append(p)
    return res

@app.get('/')
def root():
    return {'message': 'Welcome to our E-commerce API'}

@app.get('/products')
def retrieve_products():
    return {'products': products_db, 'total': len(products_db)}

@app.get('/products/filter')
def filtered_products(
    category: str = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    in_stock: bool = Query(None),
):
    f_list = do_filter(category, min_price, max_price, in_stock)
    return {'filtered_products': f_list, 'count': len(f_list)}

@app.get('/products/compare')
def comp_products(product_id_1: int = Query(...), product_id_2: int = Query(...)):
    item1 = search_prod(product_id_1)
    item2 = search_prod(product_id_2)
    
    if not item1: return {'error': f'Product {product_id_1} not found'}
    if not item2: return {'error': f'Product {product_id_2} not found'}
    
    if item1['price'] < item2['price']:
        cheaper = item1
    else:
        cheaper = item2
        
    return {
        'product_1': item1,
        'product_2': item2,
        'better_value': cheaper['name'],
        'price_diff': abs(item1['price'] - item2['price']),
    }

@app.post('/products')
def insert_product(new_product: NewProduct, response: Response):
    new_id = 1
    if products_db:
        new_id = max(x['id'] for x in products_db) + 1
        
    p = {
        'id': new_id,
        'name': new_product.name,
        'price': new_product.price,
        'category': new_product.category,
        'in_stock': new_product.in_stock,
    }
    products_db.append(p)
    response.status_code = status.HTTP_201_CREATED
    return {'message': 'Product added', 'product': p}

@app.put('/products/{product_id}')
def modify_product(product_id: int, response: Response, in_stock: bool = Query(None), price: int = Query(None)):
    p = search_prod(product_id)
    if not p:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
        
    if in_stock is not None:
        p['in_stock'] = in_stock
    if price is not None:
        p['price'] = price
        
    return {'message': 'Product updated', 'product': p}

@app.delete('/products/{product_id}')
def drop_product(product_id: int, response: Response):
    p = search_prod(product_id)
    if not p:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
        
    products_db.remove(p)
    return {'message': f"Product '{p['name']}' deleted"}

@app.get('/products/{product_id}')
def retrieve_single_product(product_id: int):
    p = search_prod(product_id)
    if not p:
        return {'error': 'Product not found'}
    return {'product': p}

@app.post('/orders')
def create_new_order(order_data: OrderRequest):
    global global_order_id
    p = search_prod(order_data.product_id)
    if not p:
        return {'error': 'Product not found'}
    if p['in_stock'] == False:
        return {'error': f"{p['name']} is out of stock"}
        
    price_total = calc_price(p['price'], order_data.quantity)
    
    created = {
        'order_id': global_order_id,
        'customer_name': order_data.customer_name,
        'product': p['name'],
        'quantity': order_data.quantity,
        'delivery_address': order_data.delivery_address,
        'total_price': price_total,
        'status': 'confirmed',
    }
    orders_list.append(created)
    global_order_id += 1
    return {'message': 'Order placed successfully', 'order': created}

@app.get('/orders')
def get_orders():
    return {'orders': orders_list, 'total_orders': len(orders_list)}

@app.post('/cart/add')
def append_to_cart(product_id: int = Query(...), quantity: int = Query(1)):
    p = search_prod(product_id)
    if not p:
        return {'error': 'Product not found'}
    if not p['in_stock']:
        return {'error': f"{p['name']} is out of stock"}
    if quantity < 1:
        return {'error': 'Quantity must be at least 1'}
        
    for item in shopping_cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item['subtotal'] = calc_price(p['price'], item['quantity'])
            return {'message': 'Cart updated', 'cart_item': item}
            
    c_item = {
        'product_id': product_id,
        'product_name': p['name'],
        'quantity': quantity,
        'unit_price': p['price'],
        'subtotal': calc_price(p['price'], quantity),
    }
    shopping_cart.append(c_item)
    return {'message': 'Added to cart', 'cart_item': c_item}

@app.get('/cart')
def show_cart():
    if len(shopping_cart) == 0:
        return {'message': 'Cart is empty', 'items': [], 'grand_total': 0}
        
    t = 0
    for x in shopping_cart:
        t += x['subtotal']
        
    return {
        'items': shopping_cart,
        'item_count': len(shopping_cart),
        'grand_total': t,
    }

@app.post('/cart/checkout')
def do_checkout(checkout_data: CheckoutRequest, response: Response):
    global global_order_id
    if len(shopping_cart) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {'error': 'Cart is empty — add items first'}
        
    placed = []
    t = 0
    for item in shopping_cart:
        new_order = {
            'order_id': global_order_id,
            'customer_name': checkout_data.customer_name,
            'product': item['product_name'],
            'quantity': item['quantity'],
            'delivery_address': checkout_data.delivery_address,
            'total_price': item['subtotal'],
            'status': 'confirmed',
        }
        orders_list.append(new_order)
        placed.append(new_order)
        t += item['subtotal']
        global_order_id += 1
        
    shopping_cart.clear()
    response.status_code = status.HTTP_201_CREATED
    return {
        'message': 'Checkout successful',
        'orders_placed': placed,
        'grand_total': t,
    }

@app.delete('/cart/{product_id}')
def delete_from_cart(product_id: int, response: Response):
    for i in range(len(shopping_cart)):
        if shopping_cart[i]['product_id'] == product_id:
            msg = f"{shopping_cart[i]['product_name']} removed from cart"
            shopping_cart.pop(i)
            return {'message': msg}
            
    response.status_code = status.HTTP_404_NOT_FOUND
    return {'error': 'Product not in cart'}