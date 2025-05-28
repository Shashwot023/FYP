from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = '05cfe106218586fd598df4bbdba0b334'  

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Existing tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            business_name TEXT NOT NULL,
            industry TEXT NOT NULL,
            location TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # New tables for inventory and sales
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            stock INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            transaction_amount REAL NOT NULL,
            items_sold INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def validate_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email)

# Helper function to generate a SKU based on product name and category
def generate_sku(name, category):
    name_part = ''.join(word[:3].upper() for word in name.split()[:2])
    category_part = category[:3].upper()
    unique_id = str(uuid.uuid4())[:4].upper()
    return f"{name_part}-{category_part}-{unique_id}"

# Helper function to determine status (default to Pending, but not used for auto-assignment anymore)
def determine_status(stock):
    return "Pending"  # Kept for compatibility, but overridden by form selection

# Helper function to seed initial data (for demonstration purposes)
def seed_data():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Check if a user exists, if not, create one
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        user_id = str(uuid.uuid4())
        c.execute('''
            INSERT INTO users (id, name, email, password, business_name, industry, location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, "John Doe", "john@example.com", generate_password_hash("password123"), "Tech Solutions", "Electronics", "Kathmandu"))
        
        # Seed inventory data with new status options
        inventory_items = [
            (str(uuid.uuid4()), user_id, "LAP-P-2023", "Laptop Pro", "Tech", 50, 1200.00, "In Progress"),
            (str(uuid.uuid4()), user_id, "KB-MECH-BLU", "Mechanical Keyboard", "Tech", 15, 85.00, "Pending"),
            (str(uuid.uuid4()), user_id, "MSE-WIRE-BLK", "Wireless Mouse", "Tech", 5, 25.00, "Completed"),
            (str(uuid.uuid4()), user_id, "SSD-EXT-1TB", "External SSD 1TB", "Tech", 30, 99.99, "In Progress"),
            (str(uuid.uuid4()), user_id, "USB-USBC-THN", "USB-C Hub", "Tech", 0, 45.00, "Pending"),
        ]
        for item in inventory_items:
            c.execute('''
                INSERT INTO inventory (id, user_id, sku, name, category, stock, price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', item)

        # Seed sales data for the last 60 days
        today = datetime.now()
        for i in range(60):
            date = today - timedelta(days=i)
            transaction_amount = 500 + (i * 10)  # Example: increasing trend
            items_sold = 50 + (i * 2)
            c.execute('''
                INSERT INTO sales (id, user_id, transaction_amount, items_sold, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), user_id, transaction_amount, items_sold, date))

    conn.commit()
    conn.close()

seed_data()

@app.route('/', endpoint='index')
def index():
    return render_template('index.html')

@app.route('/features-overview', endpoint='features_overview')
def features_overview():
    return render_template('features-overview.html')

@app.route('/inventory', endpoint='inventory')
def inventory():
    if 'user_id' not in session:
        flash('Please log in to access the inventory page.', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        # Fetch inventory items for the logged-in user
        c.execute('SELECT id, sku, name, category, stock, price, status FROM inventory WHERE user_id = ?', (session['user_id'],))
        inventory_items = []
        for row in c.fetchall():
            inventory_items.append({
                'id': row[0],
                'sku': row[1],
                'name': row[2],
                'category': row[3],
                'stock': row[4],
                'price': row[5],
                'status': row[6]
            })

        # Calculate inventory metrics
        total_items = len(inventory_items)
        total_stock = sum(item['stock'] for item in inventory_items)
        inventory_value = sum(item['stock'] * item['price'] for item in inventory_items)
        low_stock = sum(1 for item in inventory_items if 0 < item['stock'] <= 15)
        out_of_stock = sum(1 for item in inventory_items if item['stock'] == 0)
        on_backorder = 1  # Mock value; replace with actual logic if needed

    except sqlite3.OperationalError as e:
        flash(f'Database error: {str(e)}. Please ensure the database is initialized correctly.', 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()

    return render_template('inventory.html', 
                          inventory_items=inventory_items,
                          total_items=total_items,
                          total_stock=total_stock,
                          inventory_value=inventory_value,
                          low_stock=low_stock,
                          out_of_stock=out_of_stock,
                          on_backorder=on_backorder)

@app.route('/add-inventory-item', methods=['GET', 'POST'])
def add_inventory_item():
    if 'user_id' not in session:
        flash('Please log in to add an inventory item.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        print("Received POST request to /add-inventory-item")  # Debug print
        name = request.form.get('name')
        category = request.form.get('category')
        stock = request.form.get('stock')
        price = request.form.get('price')

        print(f"Form data - Name: {name}, Category: {category}, Stock: {stock}, Price: {price}")  # Debug print

        # Validate inputs
        if not all([name, category, stock, price]):
            flash('All fields are required.', 'error')
            print("Validation failed: Missing fields")  # Debug print
            return redirect(url_for('inventory'))

        try:
            stock = int(stock)
            price = float(price)
            if stock < 0 or price < 0:
                flash('Stock and price must be non-negative.', 'error')
                print("Validation failed: Negative stock or price")  # Debug print
                return redirect(url_for('inventory'))
        except ValueError as e:
            flash('Stock must be an integer and price must be a number.', 'error')
            print(f"Validation failed: Invalid stock or price - {str(e)}")  # Debug print
            return redirect(url_for('inventory'))

        # Validate category
        valid_categories = ['Grocery', 'Tech', 'Daily Essentials', 'Clothing', 'Home Appliances']
        if category not in valid_categories:
            flash('Invalid category selected.', 'error')
            print(f"Validation failed: Invalid category - {category}")  # Debug print
            return redirect(url_for('inventory'))

        # Automatically generate id, sku, and status
        item_id = str(uuid.uuid4())  # Generate unique ID
        sku = generate_sku(name, category)  # Generate SKU based on name and category
        status = "Pending"  # Default status for new items

        print(f"Generated - ID: {item_id}, SKU: {sku}, Status: {status}")  # Debug print

        # Insert into database
        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO inventory (id, user_id, sku, name, category, stock, price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, session['user_id'], sku, name, category, stock, price, status))
            conn.commit()
            print("Successfully inserted item into database")  # Debug print
            flash('Item added successfully!', 'success')
        except sqlite3.Error as e:
            flash(f'Error adding item to database: {str(e)}', 'error')
            print(f"Database error: {str(e)}")  # Debug print
        finally:
            conn.close()

        return redirect(url_for('inventory'))
    
    # Handle GET request (if the route is accessed directly)
    return redirect(url_for('inventory'))

@app.route('/update-inventory-item', methods=['POST'])
def update_inventory_item():
    if 'user_id' not in session:
        flash('Please log in to update inventory items.', 'error')
        return redirect(url_for('login'))

    item_id = request.form.get('item_id')
    if not item_id:
        flash('Invalid item ID.', 'error')
        return redirect(url_for('inventory'))

    # Fetch the current item data to use as defaults for unchanged fields
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute('SELECT name, category, stock, price, status FROM inventory WHERE id = ? AND user_id = ?', (item_id, session['user_id']))
        current_item = c.fetchone()
        if not current_item:
            flash('Item not found or you do not have permission to update it.', 'error')
            return redirect(url_for('inventory'))

        current_name, current_category, current_stock, current_price, current_status = current_item

        # Get submitted values, using current values as defaults if not provided
        name = request.form.get('name', current_name)
        category = request.form.get('category', current_category)
        stock = request.form.get('stock', str(current_stock))
        price = request.form.get('price', str(current_price))
        status = request.form.get('status', current_status)

        # Convert to appropriate types
        try:
            stock = int(stock)
            price = float(price)
            if stock < 0 or price < 0:
                flash('Stock and price must be non-negative.', 'error')
                return redirect(url_for('inventory'))
        except ValueError as e:
            flash('Stock must be an integer and price must be a number.', 'error')
            return redirect(url_for('inventory'))

        # Validate category and status
        valid_categories = ['Grocery', 'Tech', 'Daily Essentials', 'Clothing', 'Home Appliances']
        valid_statuses = ['Pending', 'In Progress', 'Completed']
        if category not in valid_categories:
            flash('Invalid category selected.', 'error')
            return redirect(url_for('inventory'))
        if status not in valid_statuses:
            flash('Invalid status selected.', 'error')
            return redirect(url_for('inventory'))

        # Log the update parameters for debugging
        print(f"Updating item {item_id} with: name={name}, category={category}, stock={stock}, price={price}, status={status}")

        # Perform the update
        c.execute('''
            UPDATE inventory 
            SET name = ?, category = ?, stock = ?, price = ?, status = ?
            WHERE id = ? AND user_id = ?
        ''', (name, category, stock, price, status, item_id, session['user_id']))
        conn.commit()
        print(f"Rows affected: {c.rowcount}")  # Log the number of rows affected

        if c.rowcount == 0:
            flash('Item not found or no changes were made.', 'error')
        else:
            flash('Item updated successfully!', 'success')
    except sqlite3.Error as e:
        flash(f'Error updating item: {str(e)}', 'error')
        print(f"Database error: {str(e)}")
    finally:
        conn.close()

    return redirect(url_for('inventory'))

@app.route('/delete-inventory-item', methods=['POST'])
def delete_inventory_item():
    if 'user_id' not in session:
        flash('Please log in to delete inventory items.', 'error')
        return redirect(url_for('login'))

    item_id = request.form.get('item_id')
    if not item_id:
        flash('Invalid item ID.', 'error')
        return redirect(url_for('inventory'))

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('DELETE FROM inventory WHERE id = ? AND user_id = ?', (item_id, session['user_id']))
        conn.commit()
        if c.rowcount == 0:
            flash('Item not found or you do not have permission to delete it.', 'error')
        else:
            flash('Item deleted successfully!', 'success')
    except sqlite3.Error as e:
        flash(f'Error deleting item: {str(e)}', 'error')
    finally:
        conn.close()

    return redirect(url_for('inventory'))

@app.route('/sales', endpoint='sales')
def sales():
    if 'user_id' not in session:
        flash('Please log in to access the sales page.', 'error')
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Fetch sales data for the last 30 days for metrics
    thirty_days_ago = datetime.now() - timedelta(days=30)
    c.execute('''
        SELECT transaction_amount, items_sold 
        FROM sales 
        WHERE user_id = ? AND created_at >= ?
    ''', (session['user_id'], thirty_days_ago))
    sales_data = c.fetchall()

    # Calculate sales metrics for the last 30 days
    total_revenue = sum(row[0] for row in sales_data)
    total_transactions = len(sales_data)
    avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
    items_sold = sum(row[1] for row in sales_data)

    # Fetch sales data for the previous 30 days (days 31-60) for comparison
    sixty_days_ago = datetime.now() - timedelta(days=60)
    c.execute('''
        SELECT transaction_amount, items_sold 
        FROM sales 
        WHERE user_id = ? AND created_at >= ? AND created_at < ?
    ''', (session['user_id'], sixty_days_ago, thirty_days_ago))
    prev_sales_data = c.fetchall()

    prev_total_revenue = sum(row[0] for row in prev_sales_data)
    prev_total_transactions = len(prev_sales_data)
    prev_avg_transaction = prev_total_revenue / prev_total_transactions if prev_total_transactions > 0 else 0
    prev_items_sold = sum(row[1] for row in prev_sales_data)

    # Calculate percentage changes
    revenue_change = ((total_revenue - prev_total_revenue) / prev_total_revenue * 100) if prev_total_revenue > 0 else 0
    transactions_change = total_transactions - prev_total_transactions
    avg_transaction_change = ((avg_transaction - prev_avg_transaction) / prev_avg_transaction * 100) if prev_avg_transaction > 0 else 0
    items_sold_change = items_sold - prev_items_sold

    sales_metrics = {
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'avg_transaction': avg_transaction,
        'items_sold': items_sold,
        'revenue_change': f"+{revenue_change:.1f}% from last month" if revenue_change >= 0 else f"{revenue_change:.1f}% from last month",
        'transactions_change': f"+{transactions_change} since last month" if transactions_change >= 0 else f"{transactions_change} since last month",
        'avg_transaction_change': f"+{avg_transaction_change:.1f}% from last month" if avg_transaction_change >= 0 else f"{avg_transaction_change:.1f}% from last month",
        'items_sold_change': f"+{items_sold_change} since last month" if items_sold_change >= 0 else f"{items_sold_change} since last month"
    }

    conn.close()

    return render_template('sales.html', sales_metrics=sales_metrics)

@app.route('/contact-us', methods=['GET', 'POST'])
def contact_us():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not all([name, email, subject, message]):
            flash('All fields are required.', 'error')
            return redirect(url_for('contact_us'))
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('contact_us'))

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO contact_submissions (id, name, email, subject, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), name, email, subject, message))
            conn.commit()
            conn.close()
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact_us'))
        except sqlite3.Error as e:
            flash('An error occurred while submitting your message. Please try again.', 'error')
            return redirect(url_for('contact_us'))

    return render_template('contact-us.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return redirect(url_for('login'))
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('login'))

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            print("Redirecting to dashboard")  # Debug statement
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        business_name = request.form.get('business_name')
        industry = request.form.get('industry')
        location = request.form.get('location')
        terms_agreed = request.form.get('terms')

        if not all([name, email, password, business_name, industry, location]):
            flash('All fields are required.', 'error')
            return redirect(url_for('signup'))
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('signup'))
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('signup'))
        if not terms_agreed:
            flash('You must agree to the Terms of Service and Privacy Policy.', 'error')
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO users (id, name, email, password, business_name, industry, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), name, email, hashed_password, business_name, industry, location))
            conn.commit()
            conn.close()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'error')
            return redirect(url_for('signup'))
        except sqlite3.Error as e:
            flash('An error occurred while creating your account. Please try again.', 'error')
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/newsletter', methods=['POST'])
def newsletter():
    email = request.form.get('email')

    if not email:
        flash('Email is required.', 'error')
        return redirect(url_for('index'))
    if not validate_email(email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO newsletter_subscriptions (id, email)
            VALUES (?, ?)
        ''', (str(uuid.uuid4()), email))
        conn.commit()
        conn.close()
        flash('Subscribed successfully! Thank you for joining SME Analytics.', 'success')
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        flash('This email is already subscribed.', 'error')
        return redirect(url_for('index'))
    except sqlite3.Error as e:
        flash('An error occurred while subscribing. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # Clear session data
    session.pop('user_id', None)
    session.pop('user_name', None)
    return redirect(url_for('index'))  

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'error')
        print("No user_id in session, redirecting to login")  
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        # Fetch user data
        c.execute('SELECT id, name, email, business_name, industry, location FROM users WHERE id = ?', (session['user_id'],))
        user = c.fetchone()
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('login'))

        # Fetch inventory items for the logged-in user
        c.execute('SELECT id, name, category, stock, price FROM inventory WHERE user_id = ?', (session['user_id'],))
        inventory_items = []
        for row in c.fetchall():
            inventory_items.append({
                'id': row[0],
                'name': row[1],
                'category': row[2],
                'stock': row[3],
                'price': row[4]
            })
            
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('login'))
    finally:
        conn.close()

    return render_template('dashboard.html', user=user, inventory_items=inventory_items)

if __name__ == '__main__':
    app.run(debug=True)