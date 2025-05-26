from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import re

app = Flask(__name__)
app.secret_key = '05cfe106218586fd598df4bbdba0b334'  

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
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
    conn.commit()
    conn.close()

init_db()

def validate_email(email):
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email)

@app.route('/', endpoint='index')
def index():
    return render_template('index.html')

@app.route('/features-overview', endpoint='features_overview')
def features_overview():
    return render_template('features-overview.html')

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
    c.execute('SELECT id, name, email, business_name, industry, location FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()

    if user:
        print("User found, rendering dashboard")
        return render_template('dashboard.html', user=user)
    else:
        flash('User not found.', 'error')
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)