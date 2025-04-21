# from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
# from pymongo import MongoClient
# from bson import ObjectId
# import datetime
# import logging
# import schedule
# import time
# import threading
# import re

# app = Flask(__name__)
# app.secret_key = 'your_secret_key'

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # MongoDB setup
# client = MongoClient('mongodb://localhost:27017/')
# db = client['login_db']
# users_collection = db['users']
# products_collection = db['products']
# carts_collection = db['carts']
# orders_collection = db['orders']
# sell_back_requests_collection = db['sell_back_requests']
# sell_back_history_collection = db['sell_back_history']
# scheduled_orders_collection = db['scheduled_orders']
# profiles_collection = db['profiles']

# # Scheduler setup
# scheduler_running = False
# scheduler_thread = None
# scheduler_lock = threading.Lock()

# def run_scheduler():
#     """Run the schedule loop in a separate thread."""
#     global scheduler_running
#     logger.debug("run_scheduler: Starting scheduler loop")
#     while scheduler_running:
#         schedule.run_pending()
#         time.sleep(1)  # Sleep to avoid high CPU usage
#     logger.debug("run_scheduler: Exiting scheduler loop")

# def process_scheduled_orders():
#     """Process all scheduled orders that need to run"""
#     try:
#         now = datetime.datetime.now()
#         logger.info(f"Checking scheduled orders at {now}")
#         scheduled_orders = list(scheduled_orders_collection.find({
#             'schedule_interval': {'$gt': 0},
#             'next_run': {'$lte': now}
#         }))
        
#         if scheduled_orders:
#             logger.info(f"Processing {len(scheduled_orders)} orders: {[str(order['_id']) for order in scheduled_orders]}")
#         else:
#             logger.info("No scheduled orders to process")
            
#         for scheduled_order in scheduled_orders:
#             logger.info(f"Processing order {scheduled_order['_id']} with interval {scheduled_order['schedule_interval']} minutes")
#             orders_collection.insert_one({
#                 'username': scheduled_order['username'],
#                 'items': list(scheduled_order['items']),
#                 'total': scheduled_order['total'],
#                 'status': 'Scheduled',
#                 'scheduled_from': scheduled_order['_id'],
#                 'created_at': now
#             })
            
#             scheduled_orders_collection.update_one(
#                 {'_id': scheduled_order['_id']},
#                 {'$set': {
#                     'last_run': now,
#                     'next_run': now + datetime.timedelta(minutes=scheduled_order['schedule_interval'])
#                 }}
#             )
#             logger.info(f"Updated last_run and next_run for order {scheduled_order['_id']}")
#     except Exception as e:
#         logger.error(f"Error in scheduler job: {e}")

# @app.route('/scheduler/start')
# def start_scheduler_route():
#     global scheduler_running, scheduler_thread
#     if 'username' not in session:
#         flash("Please login first", "error")
#         return redirect(url_for('home'))
    
#     with scheduler_lock:
#         if not scheduler_running:
#             schedule.clear()
#             schedule.every(5).seconds.do(process_scheduled_orders)
#             scheduler_running = True
#             scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
#             scheduler_thread.start()
#             logger.info("Scheduler started")
#             flash("Auto-order scheduler has been started", "success")
#         else:
#             logger.debug("Scheduler start attempted but already running")
#             flash("Scheduler is already running", "info")
    
#     return redirect(url_for('view_orders'))

# @app.route('/scheduler/stop')
# def stop_scheduler_route():
#     global scheduler_running, scheduler_thread
#     if 'username' not in session:
#         flash("Please login first", "error")
#         return redirect(url_for('home'))
    
#     with scheduler_lock:
#         if scheduler_running:
#             scheduler_running = False
#             schedule.clear()
#             if scheduler_thread:
#                 scheduler_thread = None
#             logger.info("Scheduler stopped")
#             flash("Scheduler successfully stopped", "success")
#         else:
#             logger.debug("Scheduler stop attempted but not running")
#             flash("Scheduler is not running", "info")
    
#     return redirect(url_for('view_orders'))

# @app.route('/scheduler/status')
# def scheduler_status():
#     global scheduler_running
#     with scheduler_lock:
#         pending_jobs = schedule.get_jobs()
#         status = {
#             'running': scheduler_running,
#             'jobs': [
#                 {
#                     'id': 'process_scheduled_orders',
#                     'next_run_time': str(job.next_run) if job else 'Pending'
#                 }
#                 for job in pending_jobs
#             ]
#         }
#     logger.debug(f"Scheduler status: {status}")
#     return jsonify(status)

# @app.route('/cancel_scheduled_order/<schedule_id>')
# def cancel_scheduled_order(schedule_id):
#     if 'username' not in session:
#         flash("Please log in to cancel a scheduled order.", "error")
#         return redirect(url_for('home'))
    
#     try:
#         scheduled_order = scheduled_orders_collection.find_one({
#             '_id': ObjectId(schedule_id),
#             'username': session['username']
#         })
        
#         if scheduled_order:
#             scheduled_orders_collection.delete_one({'_id': ObjectId(schedule_id)})
#             flash("Scheduled order has been cancelled.", "success")
#         else:
#             flash("Scheduled order not found or you don't have permission to cancel it.", "error")
#     except Exception as e:
#         logger.error(f"Error cancelling scheduled order: {e}")
#         flash("An error occurred while cancelling the scheduled order.", "error")
    
#     return redirect(url_for('view_orders'))

# @app.teardown_appcontext
# def shutdown_scheduler(exception=None):
#     global scheduler_running, scheduler_thread
#     logger.debug("teardown_appcontext called")

# @app.route('/')
# def home():
#     return render_template('login.html')

# @app.route('/login', methods=['POST'])
# def login():
#     username = request.form['username']
#     password = request.form['password']

#     if username == 'admin' and password == 'admin123':
#         session['admin'] = username
#         flash('Admin login successful!', 'success')
#         return redirect(url_for('admin_dashboard'))

#     user = users_collection.find_one({'username': username, 'password': password})
#     if user:
#         session['username'] = username
#         flash('User login successful!', 'success')
#         return redirect(url_for('dashboard'))
#     else:
#         flash('Invalid credentials.', 'error')
#         return redirect(url_for('home'))

# @app.route('/logout')
# def logout():
#     session.clear()
#     flash('You have been logged out.', 'info')
#     return redirect(url_for('home'))

# @app.route('/register')
# def register():
#     return render_template('register.html')

# @app.route('/register_user', methods=['POST'])
# def register_user():
#     username = request.form['username']
#     password = request.form['password']
#     if users_collection.find_one({'username': username}):
#         flash('Username already exists. Choose a different one.', 'error')
#         return redirect(url_for('register'))
#     users_collection.insert_one({'username': username, 'password': password})
#     flash('Registered successfully! Please login.', 'success')
#     return redirect(url_for('home'))

# @app.route('/dashboard')
# def dashboard():
#     if 'username' in session:
#         products = list(products_collection.find())
#         return render_template('index.html', username=session['username'], products=products)
#     else:
#         flash("Please log in to access the dashboard.", "error")
#         return redirect(url_for('home'))

# @app.route('/add_to_cart', methods=['POST'])
# def add_to_cart():
#     if 'username' not in session:
#         flash("Please log in to add items to your cart.", "error")
#         return redirect(url_for('home'))

#     product_id = request.form.get('product_id')
#     if product_id:
#         username = session['username']
#         product = products_collection.find_one({'_id': ObjectId(product_id)})
#         if product:
#             cart = carts_collection.find_one({'username': username})
#             if cart:
#                 item_exists = False
#                 for item in cart.get('items', []):
#                     if item.get('product_id') == product_id:
#                         item['quantity'] = item.get('quantity', 0) + 1
#                         item_exists = True
#                         break
#                 if not item_exists:
#                     cart['items'] = cart.get('items', []) + [{'product_id': product_id, 'quantity': 1}]
#                 carts_collection.update_one({'username': username}, {'$set': {'items': cart['items']}}, upsert=True)
#             else:
#                 carts_collection.insert_one({'username': username, 'items': [{'product_id': product_id, 'quantity': 1}]})
#             flash(f"{product['name']} added to cart!", 'success')
#         else:
#             flash("Product not found.", 'error')
#     return redirect(url_for('dashboard'))

# @app.route('/order')
# def order():
#     if 'username' not in session:
#         flash("Please log in to view your cart.", "error")
#         return redirect(url_for('home'))

#     cart = carts_collection.find_one({'username': session['username']})
#     items = []
#     grand_total = 0

#     if cart and 'items' in cart:
#         for item_data in cart['items']:
#             product = products_collection.find_one({'_id': ObjectId(item_data['product_id'])})
#             if product:
#                 quantity = item_data.get('quantity', 0)
#                 total = product['price'] * quantity
#                 print(grand_total, total)
#                 grand_total += total
#                 items.append({
#                     'product_id': str(product['_id']),
#                     'name': product['name'],
#                     'price': product['price'],
#                     'image': product['image'],
#                     'quantity': quantity,
#                     'total': total
#                 })

#     return render_template('order.html', items=items, total=grand_total)

# @app.route('/schedule_order', methods=['POST'])
# def schedule_order():
#     if 'username' not in session:
#         flash("Please log in to schedule an order.", "error")
#         return redirect(url_for('home'))

#     try:
#         interval = int(request.form.get('schedule_interval', 0))
#         cart = carts_collection.find_one({'username': session['username']})

#         if not cart or not cart.get('items'):
#             flash('Your cart is empty. Add items to schedule an order.', 'warning')
#             return redirect(url_for('order'))

#         order_items = []
#         order_total = 0
        
#         for item_data in cart['items']:
#             product = products_collection.find_one({'_id': ObjectId(item_data['product_id'])})
#             if product:
#                 quantity = item_data.get('quantity', 1)
#                 item_total = product['price'] * quantity
#                 order_total += item_total
#                 order_items.append({
#                     'product_id': str(product['_id']),
#                     'name': product['name'],
#                     'price': product['price'],
#                     'quantity': quantity,
#                     'total': item_total
#                 })

#         if interval == 0:
#             flash('Please select a valid schedule interval.', 'warning')
#             return redirect(url_for('order'))

#         scheduled_orders_collection.insert_one({
#             'username': session['username'],
#             'items': order_items,
#             'total': order_total,
#             'schedule_interval': interval,
#             'scheduled_at': datetime.datetime.now(),
#             'last_run': None,
#             'next_run': datetime.datetime.now() + datetime.timedelta(minutes=interval)
#         })

#         interval_display = {
#             1: "1 minute",
#             21600: "15 days",
#             43200: "30 days",
#             64800: "45 days"
#         }.get(interval, f"{interval} minutes")

#         carts_collection.delete_one({'username': session['username']})
#         flash(f'Order scheduled successfully! It will repeat every {interval_display}.', 'success')
#         return redirect(url_for('view_orders'))
    
#     except Exception as e:
#         logger.error(f"Error scheduling order: {e}")
#         flash('An error occurred while scheduling your order. Please try again.', 'error')
#         return redirect(url_for('order'))

# @app.route('/place_order', methods=['POST'])
# def place_order():
#     if 'username' not in session:
#         flash("Please log in to place an order.", "error")
#         return redirect(url_for('home'))

#     cart = carts_collection.find_one({'username': session['username']})
#     if not cart or not cart.get('items'):
#         flash('Your cart is empty. Add items to place an order.', 'warning')
#         return redirect(url_for('order'))

#     try:
#         order_items = []
#         order_total = 0
        
#         for item_data in cart['items']:
#             product = products_collection.find_one({'_id': ObjectId(item_data['product_id'])})
#             if product:
#                 quantity = item_data.get('quantity', 1)
#                 item_total = product['price'] * quantity
#                 order_total += item_total
#                 order_items.append({
#                     'product_id': str(product['_id']),
#                     'name': product['name'],
#                     'price': product['price'],
#                     'quantity': quantity,
#                     'total': item_total
#                 })

#         orders_collection.insert_one({
#             'username': session['username'],
#             'items': order_items,
#             'total': order_total,
#             'status': 'Placed',
#             'created_at': datetime.datetime.now()
#         })

#         carts_collection.delete_one({'username': session['username']})
#         flash('Order placed successfully!', 'success')
#         return redirect(url_for('order_success'))
    
#     except Exception as e:
#         logger.error(f"Error placing order: {e}")
#         flash('An error occurred while placing your order. Please try again.', 'error')
#         return redirect(url_for('order'))

# @app.route('/profile')
# def profile():
#     if 'username' not in session:
#         flash("Please log in to access your profile.", "error")
#         return redirect(url_for('home'))
    
#     username = session['username']
#     profile = profiles_collection.find_one({'username': username})
#     return render_template('profile.html', username=username, profile=profile)

# @app.route('/profile/submit', methods=['POST'])
# def profile_submit():
#     if 'username' not in session:
#         flash("Please log in to update your profile.", "error")
#         return redirect(url_for('home'))
    
#     username = session['username']
#     address = request.form.get('address', '').strip()
#     phone_no = request.form.get('phone_no', '').strip()
    
#     # Validation
#     if not address:
#         flash("Address is required.", "error")
#         return redirect(url_for('profile'))
    
#     phone_pattern = re.compile(r'^\d{10}$')  # Assuming 10-digit phone number
#     if not phone_no or not phone_pattern.match(phone_no):
#         flash("Please enter a valid 10-digit phone number.", "error")
#         return redirect(url_for('profile'))
    
#     try:
#         # Upsert profile (create if doesn't exist, update if it does)
#         profiles_collection.update_one(
#             {'username': username},
#             {'$set': {
#                 'address': address,
#                 'phone_no': phone_no,
#                 'updated_at': datetime.datetime.now()
#             }},
#             upsert=True
#         )
#         flash("Profile updated successfully!", "success")
#     except Exception as e:
#         logger.error(f"Error updating profile for {username}: {e}")
#         flash("An error occurred while updating your profile.", "error")
    
#     return redirect(url_for('profile'))

# @app.route('/admin/user_profile', methods=['GET', 'POST'])
# def admin_user_profile():
#     if 'admin' not in session:
#         flash("Admin login required.", "error")
#         return redirect(url_for('home'))
    
#     profile = None
#     if request.method == 'POST':
#         username = request.form.get('username', '').strip()
#         if not username:
#             flash("Username is required.", "error")
#         else:
#             # Verify user exists
#             user = users_collection.find_one({'username': username})
#             if not user:
#                 flash("User not found.", "error")
#             else:
#                 profile = profiles_collection.find_one({'username': username})
#                 if not profile:
#                     flash("No profile found for this user", "warning")
    
#     return render_template('admin_user_profile.html', profile=profile)

# @app.route('/order_success')
# def order_success():
#     if 'username' in session:
#         try:
#             last_order = orders_collection.find({'username': session['username']}).sort('_id', -1).limit(1).next()
#             return render_template('order_success.html', items=last_order.get('items', []), total=last_order.get('total', 0))
#         except StopIteration:
#             flash("No orders found.", "error")
#             return redirect(url_for('dashboard'))
#     else:
#         return redirect(url_for('home'))

# @app.route('/orders')
# def view_orders():
#     global scheduler_running
#     if 'username' not in session:
#         flash("Please log in to view your orders.", "error")
#         return redirect(url_for('home'))

#     username = session['username']
#     orders = list(orders_collection.find({'username': username}))
#     scheduled_orders = list(scheduled_orders_collection.find({'username': username}))
    
#     for order in orders:
#         if 'created_at' not in order:
#             default_date = datetime.datetime.now()
#             orders_collection.update_one(
#                 {'_id': order['_id']},
#                 {'$set': {'created_at': default_date}}
#             )
#             order['created_at'] = default_date
        
#         if 'items' not in order:
#             order['items'] = []
#         elif not isinstance(order['items'], list):
#             order['items'] = list(order['items'])
    
#     with scheduler_lock:
#         pending_jobs = schedule.get_jobs()
#         scheduler_running = scheduler_running and len(pending_jobs) > 0
#         logger.debug(f"view_orders: scheduler_running = {scheduler_running}, pending_jobs = {len(pending_jobs)}")
    
#     return render_template('order_history.html', 
#                           orders=orders,
#                           scheduled_orders=scheduled_orders,
#                           scheduler_running=scheduler_running)

# @app.route('/about')
# def about():
#     return render_template('About.html')

# @app.route('/contact')
# def contact():
#     return render_template('Contact.html')

# @app.route('/admin_dashboard')
# def admin_dashboard():
#     if 'admin' in session:
#         orders = list(orders_collection.find())
#         return render_template('admin_dashboard.html', admin=session['admin'], orders=orders)
#     else:
#         flash("Admin login required.", "error")
#         return redirect(url_for('home'))

# @app.route('/admin/add_product')
# def admin_add_product():
#     if 'admin' in session:
#         return render_template('add_product.html')
#     else:
#         flash("Admin login required to add products.", "error")
#         return redirect(url_for('home'))

# @app.route('/admin/add_product/submit', methods=['POST'])
# def add_product_submit():
#     if 'admin' in session:
#         name = request.form['name']
#         category = request.form['category']
#         description = request.form['description']
#         price = float(request.form['price'])
#         image = request.form.get('image') or "https://via.placeholder.com/300"
#         has_sell_back = request.form.get('has_sell_back') == 'True'

#         products_collection.insert_one({
#             'name': name,
#             'category': category,
#             'description': description,
#             'price': price,
#             'image': image,
#             'has_sell_back': has_sell_back
#         })
#         flash(f"Product '{name}' added successfully!", 'success')
#         return redirect(url_for('admin_add_product'))
#     else:
#         flash("Admin login required to add products.", "error")
#         return redirect(url_for('home'))

# @app.route('/admin/sell_back')
# def admin_sell_back():
#     if 'admin' in session:
#         requests = list(sell_back_requests_collection.find({'status': 'Pending'}))
#         return render_template('admin_sell_back.html', requests=requests)
#     else:
#         flash("Admin login required.", "error")
#         return redirect(url_for('home'))

# @app.route('/admin/sell_back/process', methods=['POST'])
# def admin_process_sell_back():
#     if 'admin' in session:
#         request_id = request.form.get('request_id')
#         sell_back_price = request.form.get('sell_back_price')

#         if not request_id or not sell_back_price:
#             flash("Request ID and sell back price are required.", "error")
#             return redirect(url_for('admin_sell_back'))

#         try:
#             request_data = sell_back_requests_collection.find_one({'_id': ObjectId(request_id)})
#             if request_data:
#                 sell_back_history_collection.insert_one({
#                     'user_id': request_data['user_id'],
#                     'product_name': request_data['product_name'],
#                     'quantity': request_data['quantity'],
#                     'sell_back_price': float(sell_back_price),
#                     'sell_back_date': datetime.datetime.now()
#                 })
#                 sell_back_requests_collection.delete_one({'_id': ObjectId(request_id)})
#                 flash(f"Sell back processed for {request_data['product_name']} from {request_data['user_id']} at ₹{sell_back_price}.", "success")
#             else:
#                 flash("Sell back request not found.", "error")
#         except Exception as e:
#             logger.error(f"Error processing sell back: {e}")
#             flash("An error occurred while processing the sell back request.", "error")

#         return redirect(url_for('admin_sell_back'))
#     else:
#         flash("Admin login required.", "error")
#         return redirect(url_for('home'))

# @app.route('/sell_back')
# def sell_back_request_form():
#     if 'username' not in session:
#         flash("Login required to sell back medicine.", "error")
#         return redirect(url_for('home'))
#     sellable_products = list(products_collection.find({'has_sell_back': True}))
#     return render_template('sell_back_request.html', sellable_products=sellable_products)

# @app.route('/sell_back/submit', methods=['POST'])
# def submit_sell_back_request():
#     if 'username' not in session:
#         flash("Login required to sell back medicine.", "error")
#         return redirect(url_for('home'))

#     product_id = request.form.get('product_id')
#     quantity = int(request.form.get('quantity', 1))
    
#     try:
#         product = products_collection.find_one({'_id': ObjectId(product_id), 'has_sell_back': True})
#         if not product:
#             flash("Invalid product for sell back.", "error")
#             return redirect(url_for('sell_back_request_form'))

#         sell_back_requests_collection.insert_one({
#             'user_id': session['username'],
#             'product_id': str(product['_id']),
#             'product_name': product['name'],
#             'quantity': quantity,
#             'request_date': datetime.datetime.now(),
#             'status': 'Pending'
#         })
#         flash("Your sell back request has been submitted. The admin will review it.", "success")
#         return redirect(url_for('dashboard'))
#     except Exception as e:
#         logger.error(f"Error submitting sell back request: {e}")
#         flash("An error occurred while submitting your sell back request.", "error")
#         return redirect(url_for('sell_back_request_form'))

# @app.route('/sell_back/history')
# def sell_back_history():
#     if 'username' not in session:
#         flash("Login required to view sell back history.", "error")
#         return redirect(url_for('home'))
#     history = list(sell_back_history_collection.find({'user_id': session['username']}).sort('sell_back_date', -1))
#     return render_template('sell_back_history.html', history=history)

# if __name__ == '__main__':
#     try:
#         app.run(debug=True, use_reloader=False)
#     finally:
#         with scheduler_lock:
#             if scheduler_running:
#                 scheduler_running = False
#                 schedule.clear()
#                 scheduler_thread = None
#                 logger.info("Scheduler shut down")
#         client.close()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo import MongoClient
from bson import ObjectId
import datetime
import logging
import schedule
import time
import threading
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['login_db']
users_collection = db['users']
products_collection = db['products']
carts_collection = db['carts']
orders_collection = db['orders']
sell_back_requests_collection = db['sell_back_requests']
sell_back_history_collection = db['sell_back_history']
scheduled_orders_collection = db['scheduled_orders']
profiles_collection = db['profiles']

# Scheduler setup
scheduler_running = False
scheduler_thread = None
scheduler_lock = threading.Lock()

def run_scheduler():
    """Run the schedule loop in a separate thread."""
    global scheduler_running
    logger.debug("run_scheduler: Starting scheduler loop")
    while scheduler_running:
        schedule.run_pending()
        time.sleep(1)  # Sleep to avoid high CPU usage
    logger.debug("run_scheduler: Exiting scheduler loop")

def process_scheduled_orders():
    """Process all scheduled orders that need to run"""
    try:
        now = datetime.datetime.now()
        logger.info(f"Checking scheduled orders at {now}")
        scheduled_orders = list(scheduled_orders_collection.find({
            'schedule_interval': {'$gt': 0},
            'next_run': {'$lte': now}
        }))
        
        if scheduled_orders:
            logger.info(f"Processing {len(scheduled_orders)} orders: {[str(order['_id']) for order in scheduled_orders]}")
        else:
            logger.info("No scheduled orders to process")
            
        for scheduled_order in scheduled_orders:
            logger.info(f"Processing order {scheduled_order['_id']} with interval {scheduled_order['schedule_interval']} minutes")
            orders_collection.insert_one({
                'username': scheduled_order['username'],
                'items': list(scheduled_order['items']),
                'total': scheduled_order['total'],
                'status': 'Scheduled',
                'scheduled_from': scheduled_order['_id'],
                'created_at': now
            })
            
            scheduled_orders_collection.update_one(
                {'_id': scheduled_order['_id']},
                {'$set': {
                    'last_run': now,
                    'next_run': now + datetime.timedelta(minutes=scheduled_order['schedule_interval'])
                }}
            )
            logger.info(f"Updated last_run and next_run for order {scheduled_order['_id']}")
    except Exception as e:
        logger.error(f"Error in scheduler job: {e}")

@app.route('/scheduler/start')
def start_scheduler_route():
    global scheduler_running, scheduler_thread
    if 'username' not in session:
        flash("Please login first", "error")
        return redirect(url_for('home'))
    
    with scheduler_lock:
        if not scheduler_running:
            schedule.clear()
            schedule.every(5).seconds.do(process_scheduled_orders)
            scheduler_running = True
            scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            scheduler_thread.start()
            logger.info("Scheduler started")
            flash("Auto-order scheduler has been started", "success")
        else:
            logger.debug("Scheduler start attempted but already running")
            flash("Scheduler is already running", "info")
    
    return redirect(url_for('view_orders'))

@app.route('/scheduler/stop')
def stop_scheduler_route():
    global scheduler_running, scheduler_thread
    if 'username' not in session:
        flash("Please login first", "error")
        return redirect(url_for('home'))
    
    with scheduler_lock:
        if scheduler_running:
            scheduler_running = False
            schedule.clear()
            if scheduler_thread:
                scheduler_thread = None
            logger.info("Scheduler stopped")
            flash("Scheduler successfully stopped", "success")
        else:
            logger.debug("Scheduler stop attempted but not running")
            flash("Scheduler is not running", "info")
    
    return redirect(url_for('view_orders'))

@app.route('/scheduler/status')
def scheduler_status():
    global scheduler_running
    with scheduler_lock:
        pending_jobs = schedule.get_jobs()
        status = {
            'running': scheduler_running,
            'jobs': [
                {
                    'id': 'process_scheduled_orders',
                    'next_run_time': str(job.next_run) if job else 'Pending'
                }
                for job in pending_jobs
            ]
        }
    logger.debug(f"Scheduler status: {status}")
    return jsonify(status)

@app.route('/cancel_scheduled_order/<schedule_id>')
def cancel_scheduled_order(schedule_id):
    if 'username' not in session:
        flash("Please log in to cancel a scheduled order.", "error")
        return redirect(url_for('home'))
    
    try:
        scheduled_order = scheduled_orders_collection.find_one({
            '_id': ObjectId(schedule_id),
            'username': session['username']
        })
        
        if scheduled_order:
            scheduled_orders_collection.delete_one({'_id': ObjectId(schedule_id)})
            flash("Scheduled order has been cancelled.", "success")
        else:
            flash("Scheduled order not found or you don't have permission to cancel it.", "error")
    except Exception as e:
        logger.error(f"Error cancelling scheduled order: {e}")
        flash("An error occurred while cancelling the scheduled order.", "error")
    
    return redirect(url_for('view_orders'))

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    global scheduler_running, scheduler_thread
    logger.debug("teardown_appcontext called")

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if username == 'admin' and password == 'admin123':
        session['admin'] = username
        flash('Admin login successful!', 'success')
        return redirect(url_for('admin_dashboard'))

    user = users_collection.find_one({'username': username, 'password': password})
    if user:
        session['username'] = username
        flash('User login successful!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials.', 'error')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register_user', methods=['POST'])
def register_user():
    username = request.form['username']
    password = request.form['password']
    if users_collection.find_one({'username': username}):
        flash('Username already exists. Choose a different one.', 'error')
        return redirect(url_for('register'))
    users_collection.insert_one({'username': username, 'password': password})
    flash('Registered successfully! Please login.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        products = list(products_collection.find())
        return render_template('index.html', username=session['username'], products=products)
    else:
        flash("Please log in to access the dashboard.", "error")
        return redirect(url_for('home'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        flash("Please log in to add items to your cart.", "error")
        return redirect(url_for('home'))

    product_id = request.form.get('product_id')
    if product_id:
        username = session['username']
        product = products_collection.find_one({'_id': ObjectId(product_id)})
        if product:
            cart = carts_collection.find_one({'username': username})
            if cart:
                item_exists = False
                for item in cart.get('items', []):
                    if item.get('product_id') == product_id:
                        item['quantity'] = item.get('quantity', 0) + 1
                        item_exists = True
                        break
                if not item_exists:
                    cart['items'] = cart.get('items', []) + [{'product_id': product_id, 'quantity': 1}]
                carts_collection.update_one({'username': username}, {'$set': {'items': cart['items']}}, upsert=True)
            else:
                carts_collection.insert_one({'username': username, 'items': [{'product_id': product_id, 'quantity': 1}]})
            flash(f"{product['name']} added to cart!", 'success')
        else:
            flash("Product not found.", 'error')
    return redirect(url_for('dashboard'))

@app.route('/order')
def order():
    if 'username' not in session:
        flash("Please log in to view your cart.", "error")
        return redirect(url_for('home'))

    cart = carts_collection.find_one({'username': session['username']})
    items = []
    grand_total = 0

    if cart and 'items' in cart:
        for item_data in cart['items']:
            product = products_collection.find_one({'_id': ObjectId(item_data['product_id'])})
            if product:
                quantity = item_data.get('quantity', 0)
                total = product['price'] * quantity
                print(grand_total, total)
                grand_total += total
                items.append({
                    'product_id': str(product['_id']),
                    'name': product['name'],
                    'price': product['price'],
                    'image': product['image'],
                    'quantity': quantity,
                    'total': total
                })

    return render_template('order.html', items=items, total=grand_total)

@app.route('/schedule_order', methods=['POST'])
def schedule_order():
    if 'username' not in session:
        flash("Please log in to schedule an order.", "error")
        return redirect(url_for('home'))

    try:
        interval = int(request.form.get('schedule_interval', 0))
        cart = carts_collection.find_one({'username': session['username']})

        if not cart or not cart.get('items'):
            flash('Your cart is empty. Add items to schedule an order.', 'warning')
            return redirect(url_for('order'))

        order_items = []
        order_total = 0
        
        for item_data in cart['items']:
            product = products_collection.find_one({'_id': ObjectId(item_data['product_id'])})
            if product:
                quantity = item_data.get('quantity', 1)
                item_total = product['price'] * quantity
                order_total += item_total
                order_items.append({
                    'product_id': str(product['_id']),
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': quantity,
                    'total': item_total
                })

        if interval == 0:
            flash('Please select a valid schedule interval.', 'warning')
            return redirect(url_for('order'))

        scheduled_orders_collection.insert_one({
            'username': session['username'],
            'items': order_items,
            'total': order_total,
            'schedule_interval': interval,
            'scheduled_at': datetime.datetime.now(),
            'last_run': None,
            'next_run': datetime.datetime.now() + datetime.timedelta(minutes=interval)
        })

        interval_display = {
            1: "1 minute",
            21600: "15 days",
            43200: "30 days",
            64800: "45 days"
        }.get(interval, f"{interval} minutes")

        carts_collection.delete_one({'username': session['username']})
        flash(f'Order scheduled successfully! It will repeat every {interval_display}.', 'success')
        return redirect(url_for('view_orders'))
    
    except Exception as e:
        logger.error(f"Error scheduling order: {e}")
        flash('An error occurred while scheduling your order. Please try again.', 'error')
        return redirect(url_for('order'))

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'username' not in session:
        flash("Please log in to place an order.", "error")
        return redirect(url_for('home'))

    cart = carts_collection.find_one({'username': session['username']})
    if not cart or not cart.get('items'):
        flash('Your cart is empty. Add items to place an order.', 'warning')
        return redirect(url_for('order'))

    try:
        order_items = []
        order_total = 0
        
        for item_data in cart['items']:
            product = products_collection.find_one({'_id': ObjectId(item_data['product_id'])})
            if product:
                quantity = item_data.get('quantity', 1)
                item_total = product['price'] * quantity
                order_total += item_total
                order_items.append({
                    'product_id': str(product['_id']),
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': quantity,
                    'total': item_total
                })

        orders_collection.insert_one({
            'username': session['username'],
            'items': order_items,
            'total': order_total,
            'status': 'Placed',
            'created_at': datetime.datetime.now()
        })

        carts_collection.delete_one({'username': session['username']})
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_success'))
    
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        flash('An error occurred while placing your order. Please try again.', 'error')
        return redirect(url_for('order'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        flash("Please log in to access your profile.", "error")
        return redirect(url_for('home'))
    
    username = session['username']
    profile = profiles_collection.find_one({'username': username})
    return render_template('profile.html', username=username, profile=profile)

@app.route('/profile/submit', methods=['POST'])
def profile_submit():
    if 'username' not in session:
        flash("Please log in to update your profile.", "error")
        return redirect(url_for('home'))
    
    username = session['username']
    address = request.form.get('address', '').strip()
    phone_no = request.form.get('phone_no', '').strip()
    
    # Validation
    if not address:
        flash("Address is required.", "error")
        return redirect(url_for('profile'))
    
    phone_pattern = re.compile(r'^\d{10}$')  # Assuming 10-digit phone number
    if not phone_no or not phone_pattern.match(phone_no):
        flash("Please enter a valid 10-digit phone number.", "error")
        return redirect(url_for('profile'))
    
    try:
        # Upsert profile (create if doesn't exist, update if it does)
        profiles_collection.update_one(
            {'username': username},
            {'$set': {
                'address': address,
                'phone_no': phone_no,
                'updated_at': datetime.datetime.now()
            }},
            upsert=True
        )
        flash("Profile updated successfully!", "success")
    except Exception as e:
        logger.error(f"Error updating profile for {username}: {e}")
        flash("An error occurred while updating your profile.", "error")
    
    return redirect(url_for('profile'))

@app.route('/admin/user_profile', methods=['GET', 'POST'])
def admin_user_profile():
    if 'admin' not in session:
        flash("Admin login required.", "error")
        return redirect(url_for('home'))
    
    profile = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        if not username:
            flash("Username is required.", "error")
        else:
            # Verify user exists
            user = users_collection.find_one({'username': username})
            if not user:
                flash("User not found.", "error")
            else:
                profile = profiles_collection.find_one({'username': username})
                if not profile:
                    flash("No profile found for this user.", "warning")
    
    return render_template('admin_user_profile.html', profile=profile)

@app.route('/admin/sell_back_history')
def admin_sell_back_history():
    if 'admin' not in session:
        flash("Admin login required.", "error")
        return redirect(url_for('home'))
    
    try:
        history = list(sell_back_history_collection.find().sort('sell_back_date', -1))
        return render_template('admin_sell_back_history.html', history=history)
    except Exception as e:
        logger.error(f"Error fetching sell back history: {e}")
        flash("An error occurred while fetching sell back history.", "error")
        return redirect(url_for('admin_dashboard'))

@app.route('/order_success')
def order_success():
    if 'username' in session:
        try:
            last_order = orders_collection.find({'username': session['username']}).sort('_id', -1).limit(1).next()
            return render_template('order_success.html', items=last_order.get('items', []), total=last_order.get('total', 0))
        except StopIteration:
            flash("No orders found.", "error")
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('home'))

@app.route('/orders')
def view_orders():
    global scheduler_running
    if 'username' not in session:
        flash("Please log in to view your orders.", "error")
        return redirect(url_for('home'))

    username = session['username']
    orders = list(orders_collection.find({'username': username}))
    scheduled_orders = list(scheduled_orders_collection.find({'username': username}))
    
    for order in orders:
        if 'created_at' not in order:
            default_date = datetime.datetime.now()
            orders_collection.update_one(
                {'_id': order['_id']},
                {'$set': {'created_at': default_date}}
            )
            order['created_at'] = default_date
        
        if 'items' not in order:
            order['items'] = []
        elif not isinstance(order['items'], list):
            order['items'] = list(order['items'])
    
    with scheduler_lock:
        pending_jobs = schedule.get_jobs()
        scheduler_running = scheduler_running and len(pending_jobs) > 0
        logger.debug(f"view_orders: scheduler_running = {scheduler_running}, pending_jobs = {len(pending_jobs)}")
    
    return render_template('order_history.html', 
                          orders=orders,
                          scheduled_orders=scheduled_orders,
                          scheduler_running=scheduler_running)

@app.route('/about')
def about():
    return render_template('About.html')

@app.route('/contact')
def contact():
    return render_template('Contact.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin' in session:
        orders = list(orders_collection.find())
        return render_template('admin_dashboard.html', admin=session['admin'], orders=orders)
    else:
        flash("Admin login required.", "error")
        return redirect(url_for('home'))

@app.route('/admin/add_product')
def admin_add_product():
    if 'admin' in session:
        return render_template('add_product.html')
    else:
        flash("Admin login required to add products.", "error")
        return redirect(url_for('home'))

@app.route('/admin/add_product/submit', methods=['POST'])
def add_product_submit():
    if 'admin' in session:
        name = request.form['name']
        category = request.form['category']
        description = request.form['description']
        price = float(request.form['price'])
        image = request.form.get('image') or "https://via.placeholder.com/300"
        has_sell_back = request.form.get('has_sell_back') == 'True'

        products_collection.insert_one({
            'name': name,
            'category': category,
            'description': description,
            'price': price,
            'image': image,
            'has_sell_back': has_sell_back
        })
        flash(f"Product '{name}' added successfully!", 'success')
        return redirect(url_for('admin_add_product'))
    else:
        flash("Admin login required to add products.", "error")
        return redirect(url_for('home'))

@app.route('/admin/sell_back')
def admin_sell_back():
    if 'admin' in session:
        requests = list(sell_back_requests_collection.find({'status': 'Pending'}))
        return render_template('admin_sell_back.html', requests=requests)
    else:
        flash("Admin login required.", "error")
        return redirect(url_for('home'))

@app.route('/admin/sell_back/process', methods=['POST'])
def admin_process_sell_back():
    if 'admin' in session:
        request_id = request.form.get('request_id')
        sell_back_price = request.form.get('sell_back_price')

        if not request_id or not sell_back_price:
            flash("Request ID and sell back price are required.", "error")
            return redirect(url_for('admin_sell_back'))

        try:
            request_data = sell_back_requests_collection.find_one({'_id': ObjectId(request_id)})
            if request_data:
                sell_back_history_collection.insert_one({
                    'user_id': request_data['user_id'],
                    'product_name': request_data['product_name'],
                    'quantity': request_data['quantity'],
                    'sell_back_price': float(sell_back_price),
                    'sell_back_date': datetime.datetime.now()
                })
                sell_back_requests_collection.delete_one({'_id': ObjectId(request_id)})
                flash(f"Sell back processed for {request_data['product_name']} from {request_data['user_id']} at ₹{sell_back_price}.", "success")
            else:
                flash("Sell back request not found.", "error")
        except Exception as e:
            logger.error(f"Error processing sell back: {e}")
            flash("An error occurred while processing the sell back request.", "error")

        return redirect(url_for('admin_sell_back'))
    else:
        flash("Admin login required.", "error")
        return redirect(url_for('home'))

@app.route('/sell_back')
def sell_back_request_form():
    if 'username' not in session:
        flash("Login required to sell back medicine.", "error")
        return redirect(url_for('home'))
    sellable_products = list(products_collection.find({'has_sell_back': True}))
    return render_template('sell_back_request.html', sellable_products=sellable_products)

@app.route('/sell_back/submit', methods=['POST'])
def submit_sell_back_request():
    if 'username' not in session:
        flash("Login required to sell back medicine.", "error")
        return redirect(url_for('home'))

    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    try:
        product = products_collection.find_one({'_id': ObjectId(product_id), 'has_sell_back': True})
        if not product:
            flash("Invalid product for sell back.", "error")
            return redirect(url_for('sell_back_request_form'))

        sell_back_requests_collection.insert_one({
            'user_id': session['username'],
            'product_id': str(product['_id']),
            'product_name': product['name'],
            'quantity': quantity,
            'request_date': datetime.datetime.now(),
            'status': 'Pending'
        })
        flash("Your sell back request has been submitted. The admin will review it.", "success")
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Error submitting sell back request: {e}")
        flash("An error occurred while submitting your sell back request.", "error")
        return redirect(url_for('sell_back_request_form'))

@app.route('/sell_back/history')
def sell_back_history():
    if 'username' not in session:
        flash("Login required to view sell back history.", "error")
        return redirect(url_for('home'))
    history = list(sell_back_history_collection.find({'user_id': session['username']}).sort('sell_back_date', -1))
    return render_template('sell_back_history.html', history=history)

if __name__ == '__main__':
    try:
        app.run(debug=True, use_reloader=False)
    finally:
        with scheduler_lock:
            if scheduler_running:
                scheduler_running = False
                schedule.clear()
                scheduler_thread = None
                logger.info("Scheduler shut down")
        client.close()