"""
Mulla Water Filter Delivery & Service App
Main Flask Application
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'mulla-water-secret-key-2024'  # Change in production!

DATABASE = 'mulla_water.db'

# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    """Connect to the database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    return conn

def init_db():
    """Initialize database tables and seed default data."""
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        phone TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        image_url TEXT,
        is_active INTEGER DEFAULT 1
    )''')

    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        delivery_date TEXT NOT NULL,
        delivery_time TEXT NOT NULL,
        total_price REAL NOT NULL,
        address TEXT NOT NULL,
        payment_method TEXT DEFAULT 'Cash on Delivery',
        payment_status TEXT DEFAULT 'Pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Order items table
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # Seed default admin
    admin_exists = c.execute("SELECT id FROM users WHERE role='admin'").fetchone()
    if not admin_exists:
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                  ('Admin', 'admin@mullawater.com', generate_password_hash('admin123'), 'admin'))

    # Seed default owner
    owner_exists = c.execute("SELECT id FROM users WHERE role='owner'").fetchone()
    if not owner_exists:
        c.execute("INSERT INTO users (name, email, password, role, phone) VALUES (?, ?, ?, ?, ?)",
                  ('Mulla Owner', 'owner@mullawater.com', generate_password_hash('owner123'), 'owner', '+91 98765 43210'))

    # Seed products
    product_count = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if product_count == 0:
        c.execute("""INSERT INTO products (name, category, price, description, image_url) VALUES
            ('Cold Water', 'cold', 30.0, 'Chilled purified water. Refreshing and clean. Perfect for hot days.', '/static/images/cold_water.svg'),
            ('Normal Water', 'normal', 20.0, 'Pure filtered water. Safe and healthy for daily drinking needs.', '/static/images/normal_water.svg')
        """)

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# AUTH DECORATORS
# ─────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─────────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    products = db.execute("SELECT * FROM products WHERE is_active=1").fetchall()
    db.close()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            flash('Email already registered. Please login.', 'warning')
            db.close()
            return render_template('register.html')

        hashed = generate_password_hash(password)
        db.execute("INSERT INTO users (name, email, password, role, phone, address) VALUES (?,?,?,?,?,?)",
                   (name, email, hashed, 'customer', phone, address))
        db.commit()
        db.close()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']
            session['email'] = user['email']

            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'owner':
                return redirect(url_for('owner_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# ─────────────────────────────────────────────
# PRODUCT ROUTES
# ─────────────────────────────────────────────

@app.route('/products')
def products():
    db = get_db()
    products = db.execute("SELECT * FROM products WHERE is_active=1").fetchall()
    db.close()
    return render_template('products.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    db.close()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('products'))
    return render_template('product_detail.html', product=product)

# ─────────────────────────────────────────────
# CART ROUTES (Session-based)
# ─────────────────────────────────────────────

@app.route('/cart')
@login_required
def cart():
    cart_items = session.get('cart', {})
    db = get_db()
    detailed_cart = []
    total = 0
    for pid, qty in cart_items.items():
        p = db.execute("SELECT * FROM products WHERE id=?", (int(pid),)).fetchone()
        if p:
            item_total = p['price'] * qty
            total += item_total
            detailed_cart.append({'product': p, 'quantity': qty, 'item_total': item_total})
    db.close()
    return render_template('cart.html', cart=detailed_cart, total=total)

@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = str(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))

    cart = session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + quantity
    session['cart'] = cart
    session.modified = True

    flash('Added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    product_id = str(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))

    cart = session.get('cart', {})
    if quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = quantity
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/cart/remove/<product_id>')
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    session.modified = True
    flash('Item removed.', 'info')
    return redirect(url_for('cart'))

# ─────────────────────────────────────────────
# ORDER ROUTES
# ─────────────────────────────────────────────

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = session.get('cart', {})
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()

    if request.method == 'POST':
        delivery_date = request.form['delivery_date']
        delivery_time = request.form['delivery_time']
        address = request.form['address']
        payment_method = request.form.get('payment_method', 'Cash on Delivery')
        notes = request.form.get('notes', '')

        # Calculate total
        total = 0
        items = []
        for pid, qty in cart_items.items():
            p = db.execute("SELECT * FROM products WHERE id=?", (int(pid),)).fetchone()
            if p:
                total += p['price'] * qty
                items.append({'product': p, 'quantity': qty})

        # Insert order
        cur = db.execute("""INSERT INTO orders (user_id, delivery_date, delivery_time, total_price, address, payment_method, notes)
                            VALUES (?,?,?,?,?,?,?)""",
                         (session['user_id'], delivery_date, delivery_time, total, address, payment_method, notes))
        order_id = cur.lastrowid

        # Insert order items
        for item in items:
            db.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?,?,?,?)",
                       (order_id, item['product']['id'], item['quantity'], item['product']['price']))

        db.commit()

        # Build WhatsApp message
        wa_items = ', '.join([f"{i['quantity']}x {i['product']['name']}" for i in items])
        wa_msg = (f"New Order #{order_id}! "
                  f"Customer: {session['name']}, "
                  f"Items: {wa_items}, "
                  f"Total: ₹{total:.0f}, "
                  f"Delivery: {delivery_date} {delivery_time}, "
                  f"Address: {address}")

        # Get owner phone
        owner = db.execute("SELECT phone FROM users WHERE role='owner' LIMIT 1").fetchone()
        owner_phone = owner['phone'].replace('+', '').replace(' ', '') if owner and owner['phone'] else '919876543210'

        db.close()

        # Clear cart
        session.pop('cart', None)
        session.modified = True

        flash(f'Order #{order_id} placed successfully!', 'success')
        return redirect(url_for('order_success', order_id=order_id, wa_msg=wa_msg, wa_phone=owner_phone))

    # Prepare cart detail for display
    detailed_cart = []
    total = 0
    for pid, qty in cart_items.items():
        p = db.execute("SELECT * FROM products WHERE id=?", (int(pid),)).fetchone()
        if p:
            item_total = p['price'] * qty
            total += item_total
            detailed_cart.append({'product': p, 'quantity': qty, 'item_total': item_total})

    db.close()
    return render_template('checkout.html', cart=detailed_cart, total=total, user=user)

@app.route('/order/success/<int:order_id>')
@login_required
def order_success(order_id):
    wa_msg = request.args.get('wa_msg', '')
    wa_phone = request.args.get('wa_phone', '919876543210')
    return render_template('order_success.html', order_id=order_id, wa_msg=wa_msg, wa_phone=wa_phone)

@app.route('/my-orders')
@login_required
def my_orders():
    db = get_db()
    orders = db.execute("""
        SELECT o.*, GROUP_CONCAT(p.name || ' x' || oi.quantity, ', ') as items_summary
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.id
        WHERE o.user_id = ?
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """, (session['user_id'],)).fetchall()
    db.close()
    return render_template('my_orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order or (order['user_id'] != session['user_id'] and session['role'] not in ['admin', 'owner']):
        flash('Order not found.', 'danger')
        return redirect(url_for('my_orders'))

    items = db.execute("""
        SELECT oi.*, p.name, p.category
        FROM order_items oi JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,)).fetchall()

    user = db.execute("SELECT name, email, phone, address FROM users WHERE id=?", (order['user_id'],)).fetchone()
    db.close()
    return render_template('order_detail.html', order=order, items=items, user=user)

# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────

@app.route('/admin')
@role_required('admin')
def admin_dashboard():
    db = get_db()
    stats = {
        'total_users': db.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0],
        'total_orders': db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        'pending_orders': db.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0],
        'total_revenue': db.execute("SELECT SUM(total_price) FROM orders WHERE status='Delivered'").fetchone()[0] or 0,
    }
    recent_orders = db.execute("""
        SELECT o.*, u.name as customer_name FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC LIMIT 10
    """).fetchall()
    owners = db.execute("SELECT * FROM users WHERE role='owner'").fetchall()
    users = db.execute("SELECT * FROM users WHERE role='customer' ORDER BY created_at DESC LIMIT 20").fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders, owners=owners, users=users)

@app.route('/admin/orders')
@role_required('admin')
def admin_orders():
    db = get_db()
    orders = db.execute("""
        SELECT o.*, u.name as customer_name, u.phone as customer_phone
        FROM orders o JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC
    """).fetchall()
    db.close()
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/add-owner', methods=['POST'])
@role_required('admin')
def admin_add_owner():
    name = request.form['name'].strip()
    email = request.form['email'].strip().lower()
    password = request.form['password']
    phone = request.form.get('phone', '').strip()

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    if existing:
        flash('Email already exists.', 'danger')
    else:
        db.execute("INSERT INTO users (name, email, password, role, phone) VALUES (?,?,?,?,?)",
                   (name, email, generate_password_hash(password), 'owner', phone))
        db.commit()
        flash(f'Owner {name} added successfully!', 'success')
    db.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-user/<int:user_id>')
@role_required('admin')
def admin_delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=? AND role != 'admin'", (user_id,))
    db.commit()
    db.close()
    flash('User removed.', 'info')
    return redirect(url_for('admin_dashboard'))

# ─────────────────────────────────────────────
# OWNER PANEL
# ─────────────────────────────────────────────

@app.route('/owner')
@role_required('owner')
def owner_dashboard():
    db = get_db()
    stats = {
        'pending': db.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0],
        'accepted': db.execute("SELECT COUNT(*) FROM orders WHERE status='Accepted'").fetchone()[0],
        'out_for_delivery': db.execute("SELECT COUNT(*) FROM orders WHERE status='Out for Delivery'").fetchone()[0],
        'delivered_today': db.execute("SELECT COUNT(*) FROM orders WHERE status='Delivered' AND DATE(created_at)=DATE('now')").fetchone()[0],
    }
    orders = db.execute("""
        SELECT o.*, u.name as customer_name, u.phone as customer_phone,
               GROUP_CONCAT(p.name || ' x' || oi.quantity, ', ') as items_summary
        FROM orders o
        JOIN users u ON o.user_id = u.id
        LEFT JOIN order_items oi ON o.id = oi.order_id
        LEFT JOIN products p ON oi.product_id = p.id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """).fetchall()
    db.close()
    return render_template('owner/dashboard.html', stats=stats, orders=orders)

@app.route('/owner/update-status', methods=['POST'])
@role_required('owner')
def update_order_status():
    order_id = request.form['order_id']
    status = request.form['status']
    allowed = ['Pending', 'Accepted', 'Out for Delivery', 'Delivered', 'Cancelled']
    if status in allowed:
        db = get_db()
        db.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        db.commit()
        db.close()
        flash(f'Order #{order_id} updated to {status}.', 'success')
    return redirect(url_for('owner_dashboard'))

# ─────────────────────────────────────────────
# API ENDPOINTS (for dynamic cart totals)
# ─────────────────────────────────────────────

@app.route('/api/cart-count')
def cart_count():
    cart = session.get('cart', {})
    count = sum(cart.values())
    return jsonify({'count': count})

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        init_db()  # Safe to call multiple times (CREATE IF NOT EXISTS)
    app.run(debug=True, port=5000)
