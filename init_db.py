"""
init_db.py — Run this once to set up the database fresh.
Usage: python init_db.py
"""
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'mulla_water.db'

def init():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Drop existing tables (fresh start)
    c.executescript('''
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS users;
    ''')

    # Create tables
    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer',
        phone TEXT,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT,
        image_url TEXT,
        is_active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE orders (
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

    c.execute('''CREATE TABLE order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    # Seed admin
    c.execute("INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
              ('Admin', 'admin@mullawater.com', generate_password_hash('admin123'), 'admin'))

    # Seed owner
    c.execute("INSERT INTO users (name, email, password, role, phone) VALUES (?,?,?,?,?)",
              ('Mulla Owner', 'owner@mullawater.com', generate_password_hash('owner123'), 'owner', '+91 98765 43210'))

    # Seed products
    c.execute("""INSERT INTO products (name, category, price, description, image_url) VALUES
        ('Cold Water', 'cold', 30.0, 'Chilled purified water. Refreshing and clean. Perfect for hot days.', '/static/images/cold_water.svg'),
        ('Normal Water', 'normal', 20.0, 'Pure filtered water. Safe and healthy for daily drinking needs.', '/static/images/normal_water.svg')
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")
    print("   Admin login: admin@mullawater.com / admin123")
    print("   Owner login: owner@mullawater.com / owner123")

if __name__ == '__main__':
    init()
