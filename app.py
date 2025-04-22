from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
import random

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Bazani yaratish va ulashish
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                balance INTEGER,
                energy INTEGER,
                last_click INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_name TEXT,
                reward INTEGER
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer TEXT,
                referred TEXT
                )''')
    conn.commit()
    conn.close()

# Ro'yxatdan o'tish sahifasi
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        referral = request.form['referral']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Ro'yxatdan o'tish
        c.execute("INSERT INTO users (username, password, balance, energy, last_click) VALUES (?, ?, ?, ?, ?)",
                  (username, hashed_password, 0, 100, 0))
        conn.commit()

        # Referalni saqlash
        if referral:
            c.execute("INSERT INTO referrals (referrer, referred) VALUES (?, ?)", (referral, username))
            conn.commit()

        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# Kirish sahifasi
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials, please try again"
    return render_template('login.html')

# Dashboard (Foydalanuvchi sahifasi)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    return render_template('dashboard.html', user=user)

# Tanga bosish va balansni yangilash
@app.route('/click')
def click():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    
    # Energiya tiklash
    if user[4] > 0:
        new_balance = user[3] + 0.001
        new_energy = user[4] - 1
        c.execute("UPDATE users SET balance = ?, energy = ? WHERE username = ?", (new_balance, new_energy, username))
        conn.commit()
    else:
        return "No energy left. Come back in 1 hour."
    
    conn.close()
    return redirect(url_for('dashboard'))

# Missiyalarni ko'rsatish va qo'shish (admin uchun)
@app.route('/missions', methods=['GET', 'POST'])
def missions():
    if 'username' not in session or session['username'] != '@UCMINEGA':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':
        mission_name = request.form['mission_name']
        reward = int(request.form['reward'])
        c.execute("INSERT INTO missions (mission_name, reward) VALUES (?, ?)", (mission_name, reward))
        conn.commit()

    c.execute("SELECT * FROM missions")
    missions = c.fetchall()
    conn.close()

    return render_template('missions.html', missions=missions)

# Referal tizimi
@app.route('/ref')
def ref():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM referrals WHERE referred = ?", (username,))
    referrers = c.fetchall()
    conn.close()

    return render_template('referrals.html', referrers=referrers)

# Yechish sahifasi
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount < 120:
            return "Minimum withdrawal is 120 UC."
        
        username = session['username']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()

        if user[3] < amount:
            return "Insufficient balance."
        
        new_balance = user[3] - amount
        c.execute("UPDATE users SET balance = ? WHERE username = ?", (new_balance, username))
        conn.commit()
        conn.close()

        return "Withdrawal successful."

    return render_template('withdraw.html')

# Saytni ishga tushurish
if __name__ == '__main__':
    init_db()  # Baza yaratish
    app.run(debug=True)
