from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field

app = FastAPI()

# ----------------------------------------------------
# Pydantic Classes
# ----------------------------------------------------
class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)
    delivery_address: str = Field(..., min_length=10)
    delivery_slot: str = "Morning"
    bulk_order: bool = False

class NewItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    unit: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    in_stock: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)
    delivery_slot: str = "Morning"

# ----------------------------------------------------
# Global Variables and Data
# ----------------------------------------------------
grocery_items = [
    {'id': 1, 'name': 'Butter', 'price': 150, 'category': 'Dairy', 'unit': 'piece', 'in_stock': True},
    {'id': 2, 'name': 'Cheese', 'price': 100, 'category': 'Dairy', 'unit': 'piece', 'in_stock': True},
    {'id': 3, 'name': 'Milk', 'price': 30, 'category': 'Dairy', 'unit': 'litre', 'in_stock': False},
    {'id': 4, 'name': 'Curd', 'price': 40, 'category': 'Dairy', 'unit': 'litre', 'in_stock': False},
    {'id': 5, 'name': 'Paneer', 'price': 200, 'category': 'Dairy', 'unit': 'piece', 'in_stock': False},
    {'id': 6, 'name': 'Tomato', 'price': 49, 'category': 'Vegetable', 'unit': 'kg', 'in_stock': True},
]

all_orders = []
current_order_id = 1
shopping_cart = []

# ----------------------------------------------------
# Helper Functions
# ----------------------------------------------------
def search_for_item(search_id: int):
    # Loop over grocery_items to find item by id
    for item in grocery_items:
        if item['id'] == search_id:
            return item
    return None

def get_order_costs(item_price, qty, slot, bulk=False):
    t = item_price * qty
    orig_t = t

    # Apply discount
    if bulk == True and qty >= 10:
        t = t * 0.92

    # Delivery charges
    delivery_fee = 0
    if slot == "Morning":
        delivery_fee = 40
    elif slot == "Evening":
        delivery_fee = 60

    return {
        "original_total": orig_t,
        "discounted_total": t,
        "delivery_charge": delivery_fee,
        "final_total": t + delivery_fee
    }

def perform_filtering(cat=None, max_p=None, u=None, stock=None):
    res = []
    for g in grocery_items:
        add_it = True
        if cat is not None and g['category'] != cat:
            add_it = False
        if max_p is not None and g['price'] > max_p:
            add_it = False
        if u is not None and g['unit'] != u:
            add_it = False
        if stock is not None and g['in_stock'] != stock:
            add_it = False
            
        if add_it == True:
            res.append(g)
    return res

# ----------------------------------------------------
# Endpoints
# ----------------------------------------------------

@app.get('/')
def root():
    return {'message': 'Welcome to FreshMart Grocery'}

@app.get('/items')
def fetch_items():
    cnt = 0
    for x in grocery_items:
        if x['in_stock']:
            cnt += 1
            
    return {
        'items': grocery_items,
        'total': len(grocery_items),
        'in_stock_count': cnt
    }

@app.get('/items/summary')
def get_summary():
    tot = len(grocery_items)
    in_st = 0
    for x in grocery_items:
        if x['in_stock']:
            in_st += 1

    cat_dict = {}
    for x in grocery_items:
        c = x['category']
        if c in cat_dict:
            cat_dict[c] = cat_dict[c] + 1
        else:
            cat_dict[c] = 1

    out_st = tot - in_st
    return {
        "total_items": tot,
        "in_stock": in_st,
        "out_of_stock": out_st,
        "category_breakdown": cat_dict
    }

@app.get('/items/search')
def find_items_by_keyword(keyword: str):
    found = []
    for item in grocery_items:
        n = item['name'].lower()
        c = item['category'].lower()
        k = keyword.lower()
        if k in n or k in c:
            found.append(item)
            
    return {"results": found, "total": len(found)}

@app.get('/items/filter')
def filter_by_params(
    category: str = Query(None),
    max_price: int = Query(None),
    unit: str = Query(None),
    in_stock: bool = Query(None)
):
    filtered = perform_filtering(category, max_price, unit, in_stock)
    return {"items": filtered, "count": len(filtered)}

@app.get('/items/sort')
def order_items_sorted(sort_by: str = "price", order: str = "asc"):
    if sort_by != "price" and sort_by != "name" and sort_by != "category":
        return {"error": "Invalid sort field"}

    is_rev = False
    if order == "desc":
        is_rev = True

    def get_key(x):
        return x[sort_by]
        
    s_list = sorted(grocery_items, key=get_key, reverse=is_rev)

    return {
        "sort_by": sort_by,
        "order": order,
        "items": s_list
    }

@app.get('/items/page')
def get_paged_items(page: int = 1, limit: int = 2):
    idx1 = (page - 1) * limit
    idx2 = idx1 + limit
    
    t_pages = len(grocery_items) // limit
    if len(grocery_items) % limit != 0:
        t_pages += 1
        
    return {
        "items": grocery_items[idx1:idx2],
        "total_pages": t_pages
    }

@app.get('/orders')
def fetch_orders():
    return {'orders': all_orders, 'total': len(all_orders)}

@app.get('/orders/search')
def look_for_orders(name: str):
    res = []
    for o in all_orders:
        if name.lower() in o['customer_name'].lower():
            res.append(o)
    return res

@app.get('/orders/sort')
def sorted_orders_list(order: str = "asc"):
    is_rev = False
    if order == "desc":
        is_rev = True
        
    def get_order_key(x):
        return x['total_cost']
        
    return sorted(all_orders, key=get_order_key, reverse=is_rev)

@app.get('/orders/page')
def paged_orders_list(page: int = 1, limit: int = 2):
    idx1 = (page - 1) * limit
    idx2 = idx1 + limit
    
    t_pages = len(all_orders) // limit
    if len(all_orders) % limit != 0:
        t_pages += 1
        
    return {
        "page": page,
        "limit": limit,
        "total": len(all_orders),
        "total_pages": t_pages,
        "orders": all_orders[idx1:idx2]
    }

@app.post('/orders')
def make_order(order_data: OrderRequest):
    global current_order_id

    the_item = search_for_item(order_data.item_id)
    if the_item == None:
        return {'error': 'Item not found'}

    if the_item['in_stock'] == False:
        return {'error': 'Item out of stock'}

    calc = get_order_costs(
        the_item['price'],
        order_data.quantity,
        order_data.delivery_slot,
        order_data.bulk_order
    )

    new_ord = {
        'order_id': current_order_id,
        'customer_name': order_data.customer_name,
        'item_id': the_item['id'],
        'item_name': the_item['name'],
        'quantity': order_data.quantity,
        'unit': the_item['unit'],
        'delivery_slot': order_data.delivery_slot,
        'total_cost': calc["final_total"],
        'status': 'confirmed'
    }

    all_orders.append(new_ord)
    current_order_id += 1

    return new_ord

@app.post('/items')
def insert_item(new_item: NewItem, response: Response):
    for i in grocery_items:
        if i['name'].lower() == new_item.name.lower():
            response.status_code = 400
            return {'error': 'Item already exists'}

    nid = 1
    if len(grocery_items) > 0:
        m = grocery_items[0]['id']
        for g in grocery_items:
            if g['id'] > m:
                m = g['id']
        nid = m + 1

    it = {
        'id': nid,
        'name': new_item.name,
        'price': new_item.price,
        'unit': new_item.unit,
        'category': new_item.category,
        'in_stock': new_item.in_stock
    }

    grocery_items.append(it)
    response.status_code = 201
    return it

@app.put('/items/{item_id}')
def edit_item(item_id: int, price: int = Query(None), in_stock: bool = Query(None)):
    the_item = search_for_item(item_id)
    if the_item == None:
        return {'error': 'Item not found'}

    if price is not None:
        the_item['price'] = price

    if in_stock is not None:
        the_item['in_stock'] = in_stock

    return the_item

@app.delete('/items/{item_id}')
def remove_item(item_id: int):
    the_item = search_for_item(item_id)
    if the_item == None:
        return {'error': 'Item not found'}

    for o in all_orders:
        if o['item_id'] == item_id:
            return {'error': 'Item has active orders'}

    grocery_items.remove(the_item)
    return {'message': 'Deleted successfully'}

@app.post('/cart/add')
def append_to_cart(
    item_id: int = Query(...),
    quantity: int = Query(1, gt=0)
):
    it = search_for_item(item_id)

    if it == None:
        return {'error': 'Item not found'}

    if it['in_stock'] == False:
        return {'error': f"{it['name']} is out of stock"}

    for c in shopping_cart:
        if c['item_id'] == item_id:
            c['quantity'] += quantity
            c['subtotal'] = c['quantity'] * it['price']
            return {'message': 'Item quantity updated in cart', 'cart_item': c}

    cart_obj = {
        'item_id': item_id,
        'item_name': it['name'],
        'quantity': quantity,
        'unit_price': it['price'],
        'subtotal': it['price'] * quantity
    }

    shopping_cart.append(cart_obj)

    return {'message': 'Item added to cart', 'cart_item': cart_obj}

@app.get('/cart')
def retrieve_cart():
    if len(shopping_cart) == 0:
        return {'message': 'Cart is empty', 'items': [], 'grand_total': 0}

    g_tot = 0
    for x in shopping_cart:
        g_tot += x['subtotal']

    return {
        'items': shopping_cart,
        'total_items': len(shopping_cart),
        'grand_total': g_tot
    }

@app.post('/cart/checkout')
def do_checkout(checkout_data: CheckoutRequest):
    global current_order_id

    if len(shopping_cart) == 0:
        return {'error': 'Cart is empty'}

    placed = []
    g_tot = 0

    for c in shopping_cart:
        costs = get_order_costs(
            c['unit_price'],
            c['quantity'],
            checkout_data.delivery_slot
        )

        new_ord = {
            'order_id': current_order_id,
            'customer_name': checkout_data.customer_name,
            'item_id': c['item_id'],
            'item_name': c['item_name'],
            'quantity': c['quantity'],
            'delivery_slot': checkout_data.delivery_slot,
            'total_cost': costs["final_total"],
            'status': 'confirmed'
        }

        all_orders.append(new_ord)
        placed.append(new_ord)
        g_tot += costs["final_total"]
        current_order_id += 1

    shopping_cart.clear()

    return {
        'message': 'Checkout successful',
        'orders': placed,
        'grand_total': g_tot
    }

@app.delete('/cart/{item_id}')
def delete_cart_item(item_id: int):
    i = 0
    while i < len(shopping_cart):
        if shopping_cart[i]['item_id'] == item_id:
            n = shopping_cart[i]['item_name']
            shopping_cart.pop(i)
            return {'message': f"{n} removed from cart"}
        i += 1
    return {'error': 'Item not in cart'}

@app.get('/items/browse')
def browse_items(
    keyword: str = None,
    category: str = None,
    in_stock: bool = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 2
):
    tmp_list = []
    for g in grocery_items:
        tmp_list.append(g)

    if keyword is not None:
        filtered = []
        for i in tmp_list:
            if keyword.lower() in i['name'].lower():
                filtered.append(i)
        tmp_list = filtered

    if category is not None:
        filtered = []
        for i in tmp_list:
            if i['category'] == category:
                filtered.append(i)
        tmp_list = filtered

    if in_stock is not None:
        filtered = []
        for i in tmp_list:
            if i['in_stock'] == in_stock:
                filtered.append(i)
        tmp_list = filtered

    if sort_by != "price" and sort_by != "name" and sort_by != "category":
        return {"error": "Invalid sort field"}

    is_rev = False
    if order == "desc":
        is_rev = True
        
    def get_sort_key(x):
        return x[sort_by]
        
    tmp_list = sorted(tmp_list, key=get_sort_key, reverse=is_rev)

    tot = len(tmp_list)
    idx1 = (page - 1) * limit
    idx2 = idx1 + limit
    
    t_pages = tot // limit
    if tot % limit != 0:
        t_pages += 1

    return {
        "total_found": tot,
        "page": page,
        "limit": limit,
        "total_pages": t_pages,
        "items": tmp_list[idx1:idx2]
    }

@app.get('/items/{item_id}')
def fetch_item_by_id(item_id: int):
    it = search_for_item(item_id)
    if it == None:
        return {'error': 'Item not found'}
    return it