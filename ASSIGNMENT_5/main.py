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

store_products = [
    {'id': 1, 'name': 'Wireless Mouse', 'price': 499, 'category': 'Electronics', 'in_stock': True},
    {'id': 2, 'name': 'Notebook', 'price': 99, 'category': 'Stationery', 'in_stock': True},
    {'id': 3, 'name': 'USB Hub', 'price': 799, 'category': 'Electronics', 'in_stock': False},
    {'id': 4, 'name': 'Pen Set', 'price': 49, 'category': 'Stationery', 'in_stock': True},
]

store_orders = []
order_id_counter = 1
user_cart = []

def get_prod(pid: int):
    for prod in store_products:
        if prod['id'] == pid:
            return prod
    return None

def calc_subtotal(prod: dict, q: int) -> int:
    return prod['price'] * q

def filter_items(cat=None, min_p=None, max_p=None, stock=None):
    out = []
    for p in store_products:
        if cat and p['category'] != cat:
            continue
        if min_p and p['price'] < min_p:
            continue
        if max_p and p['price'] > max_p:
            continue
        if stock is not None and p['in_stock'] != stock:
            continue
        out.append(p)
    return out

@app.get('/')
def home_route():
    return {'message': 'Welcome to our E-commerce API'}

@app.get('/products')
def all_products_route():
    return {'products': store_products, 'total': len(store_products)}

@app.get('/products/filter')
def filtered_products_route(
    category: str = Query(None),
    min_price: int = Query(None),
    max_price: int = Query(None),
    in_stock: bool = Query(None),
):
    res = filter_items(category, min_price, max_price, in_stock)
    return {'filtered_products': res, 'count': len(res)}

@app.get('/products/compare')
def compare_route(
    product_id_1: int = Query(...),
    product_id_2: int = Query(...),
):
    p1 = get_prod(product_id_1)
    p2 = get_prod(product_id_2)
    
    if p1 is None: return {'error': f'Product {product_id_1} not found'}
    if p2 is None: return {'error': f'Product {product_id_2} not found'}
    
    best = p1 if p1['price'] < p2['price'] else p2
    
    return {
        'product_1': p1,
        'product_2': p2,
        'better_value': best['name'],
        'price_diff': abs(p1['price'] - p2['price']),
    }

@app.get('/products/search')
def search_keyword(keyword: str = Query(..., description='Word to search for')):
    found = []
    for p in store_products:
        if keyword.lower() in p['name'].lower():
            found.append(p)
            
    if len(found) == 0:
        return {'message': f'No products found for: {keyword}', 'results': []}
        
    return {
        'keyword': keyword,
        'total_found': len(found),
        'results': found,
    }

@app.get('/products/sort')
def sort_items(
    sort_by: str = Query('price', description='price or name'),
    order: str = Query('asc', description='asc or desc'),
):
    if sort_by != 'price' and sort_by != 'name':
        return {'error': "sort_by must be 'price' or 'name'"}
    if order != 'asc' and order != 'desc':
        return {'error': "order must be 'asc' or 'desc'"}
        
    def get_key(p):
        return p[sort_by]
        
    is_rev = False
    if order == 'desc':
        is_rev = True
        
    s_list = sorted(store_products, key=get_key, reverse=is_rev)
    
    return {
        'sort_by': sort_by,
        'order': order,
        'products': s_list,
    }

@app.get('/products/page')
def pagination(page: int = Query(1, ge=1), limit: int = Query(2, ge=1, le=20)):
    idx_start = (page - 1) * limit
    idx_end = idx_start + limit
    
    sliced = store_products[idx_start:idx_end]
    
    tot_pages = len(store_products) // limit
    if len(store_products) % limit != 0:
        tot_pages += 1
        
    return {
        'page': page,
        'limit': limit,
        'total': len(store_products),
        'total_pages': tot_pages,
        'products': sliced,
    }

@app.post('/products')
def add_new(new_product: NewProduct, response: Response):
    for p in store_products:
        if p['name'].lower() == new_product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {'error': 'Product with this name already exists'}
            
    nid = 1
    if len(store_products) > 0:
        nid = max(p['id'] for p in store_products) + 1
        
    p_dict = {
        'id': nid,
        'name': new_product.name,
        'price': new_product.price,
        'category': new_product.category,
        'in_stock': new_product.in_stock,
    }
    store_products.append(p_dict)
    response.status_code = status.HTTP_201_CREATED
    return {'message': 'Product added', 'product': p_dict}

@app.put('/products/{product_id}')
def update_existing(product_id: int, response: Response, in_stock: bool = Query(None), price: int = Query(None)):
    p = get_prod(product_id)
    if p is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
        
    if in_stock is not None:
        p['in_stock'] = in_stock
    if price is not None:
        p['price'] = price
        
    return {'message': 'Product updated', 'product': p}

@app.delete('/products/{product_id}')
def remove_existing(product_id: int, response: Response):
    p = get_prod(product_id)
    if not p:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {'error': 'Product not found'}
        
    store_products.remove(p)
    return {'message': f"Product '{p['name']}' deleted"}

@app.get("/orders/search")
def search_customer_orders(customer_name: str = Query(...)):
    res = []
    for o in store_orders:
        if customer_name.lower() in o["customer_name"].lower():
            res.append(o)

    if len(res) == 0:
        return {"message": f"No orders found for: {customer_name}"}

    return {
        "customer_name": customer_name,
        "total_found": len(res),
        "orders": res
    }

@app.get("/products/sort-by-category")
def sort_cat_price():
    def sort_key(p):
        return (p["category"], p["price"])
        
    res = sorted(store_products, key=sort_key)
    return {
        "products": res,
        "total": len(res)
    }

@app.get("/products/browse")
def browse_all(
    keyword: str = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1)
):
    tmp = []
    for p in store_products:
        tmp.append(p)
        
    if keyword:
        filtered = []
        for p in tmp:
            if keyword.lower() in p["name"].lower():
                filtered.append(p)
        tmp = filtered

    if sort_by == "price" or sort_by == "name":
        is_r = False
        if order == "desc":
            is_r = True
        tmp = sorted(tmp, key=lambda p: p[sort_by], reverse=is_r)

    tot = len(tmp)
    start_i = (page - 1) * limit
    sliced = tmp[start_i : start_i + limit]

    t_pages = tot // limit
    if tot % limit != 0:
        t_pages += 1

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": tot,
        "total_pages": t_pages,
        "products": sliced
    }

@app.get("/orders/page")
def paginate_orders(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    start_i = (page - 1) * limit
    
    t_pages = len(store_orders) // limit
    if len(store_orders) % limit != 0:
        t_pages += 1

    return {
        "page": page,
        "limit": limit,
        "total": len(store_orders),
        "total_pages": t_pages,
        "orders": store_orders[start_i : start_i + limit]
    }

@app.get('/products/{product_id}')
def get_one_product(product_id: int):
    p = get_prod(product_id)
    if p is None:
        return {'error': 'Product not found'}
    return {'product': p}

@app.post('/orders')
def create_order(order_data: OrderRequest):
    global order_id_counter
    p = get_prod(order_data.product_id)
    if p is None:
        return {'error': 'Product not found'}
    if p['in_stock'] == False:
        return {'error': f"{p['name']} is out of stock"}
        
    tot = calc_subtotal(p, order_data.quantity)
    o = {
        'order_id': order_id_counter,
        'customer_name': order_data.customer_name,
        'product': p['name'],
        'quantity': order_data.quantity,
        'delivery_address': order_data.delivery_address,
        'total_price': tot,
        'status': 'confirmed',
    }
    store_orders.append(o)
    order_id_counter += 1
    return {'message': 'Order placed successfully', 'order': o}

@app.get('/orders')
def list_orders():
    return {'orders': store_orders, 'total_orders': len(store_orders)}

@app.post('/cart/add')
def add_cart(product_id: int = Query(...), quantity: int = Query(1)):
    p = get_prod(product_id)
    if not p: return {'error': 'Product not found'}
    if not p['in_stock']: return {'error': f"{p['name']} is out of stock"}
    
    for item in user_cart:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item['subtotal'] = calc_subtotal(p, item['quantity'])
            return {'message': 'Cart updated', 'cart_item': item}
            
    new_c = {
        'product_id': product_id,
        'product_name': p['name'],
        'quantity': quantity,
        'unit_price': p['price'],
        'subtotal': calc_subtotal(p, quantity),
    }
    user_cart.append(new_c)
    return {'message': 'Added to cart', 'cart_item': new_c}

@app.get('/cart')
def get_cart():
    if len(user_cart) == 0:
        return {'message': 'Cart is empty', 'items': [], 'grand_total': 0}
        
    g_tot = 0
    for x in user_cart:
        g_tot += x['subtotal']
        
    return {
        'items': user_cart,
        'item_count': len(user_cart),
        'grand_total': g_tot,
    }

@app.post('/cart/checkout')
def checkout_cart(checkout_data: CheckoutRequest, response: Response):
    global order_id_counter
    if len(user_cart) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {'error': 'Cart is empty'}
        
    placed = []
    g_tot = 0
    for item in user_cart:
        o = {
            'order_id': order_id_counter,
            'customer_name': checkout_data.customer_name,
            'product': item['product_name'],
            'quantity': item['quantity'],
            'delivery_address': checkout_data.delivery_address,
            'total_price': item['subtotal'],
            'status': 'confirmed',
        }
        store_orders.append(o)
        placed.append(o)
        g_tot += item['subtotal']
        order_id_counter += 1
        
    user_cart.clear()
    
    response.status_code = status.HTTP_201_CREATED
    return {
        'message': 'Checkout successful',
        'orders_placed': placed,
        'grand_total': g_tot,
    }

@app.delete('/cart/{product_id}')
def delete_cart_item(product_id: int, response: Response):
    i = 0
    while i < len(user_cart):
        if user_cart[i]['product_id'] == product_id:
            n = user_cart[i]['product_name']
            user_cart.pop(i)
            return {'message': f"{n} removed from cart"}
        i += 1
        
    response.status_code = status.HTTP_404_NOT_FOUND
    return {'error': 'Product not in cart'}