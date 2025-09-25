from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from chatbot import get_bot_response, enrich_bot_response
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-random-key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.db')


# -------------------- DB Helpers --------------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('donor','recipient')) NOT NULL,
            blood_type TEXT,
            phone TEXT,
            is_admin INTEGER DEFAULT 0
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            blood_type TEXT,
            quantity INTEGER,
            location TEXT,
            donated_at TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            blood_type TEXT,
            quantity INTEGER,
            location TEXT,
            received_at TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            scheduled_at TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
# initialize DB on startup
with app.app_context():
    init_db()


# -------------------- Stock --------------------
BASE_STOCK = {
    "A+": 25, "A-": 10, "B+": 20, "B-": 5,
    "AB+": 8, "AB-": 2, "O+": 35, "O-": 12,
}


def compute_stock():
    """Compute current stock by adding BASE_STOCK, donations, and subtracting recipients."""
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT blood_type, SUM(quantity) as total FROM donations GROUP BY blood_type")
    rows = cur.fetchall()

    cur.execute("SELECT blood_type, SUM(quantity) as total FROM recipients GROUP BY blood_type")
    rec_rows = cur.fetchall()
    rec_map = {r['blood_type']: (r['total'] or 0) for r in rec_rows}

    stock = BASE_STOCK.copy()
    for r in rows:
        bt = r["blood_type"]
        total = r["total"] or 0
        stock[bt] = stock.get(bt, 0) + total - rec_map.get(bt, 0)

    return stock


@app.context_processor
def inject_stock():
    return dict(stock=compute_stock())


# -------------------- Routes --------------------
@app.route('/')
def index():
    user = None
    if session.get('user_id'):
        db = get_db()
        user = db.execute(
            'SELECT id,name,email,role,blood_type,phone,is_admin FROM users WHERE id=?',
            (session['user_id'],)
        ).fetchone()
    return render_template('index.html', user=user)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        role = request.form['role']
        blood_type = request.form.get('blood_type')
        phone = request.form.get('phone')

        if not name or not email or not password or role not in ('donor', 'recipient'):
            return render_template('signup.html', error="Please fill required fields.")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name,email,password,role,blood_type,phone) VALUES (?,?,?,?,?,?)",
                (name, email, generate_password_hash(password), role, blood_type, phone)
            )
            db.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'error')
            return render_template('signup.html', error="Email already registered.")
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'error')
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    db = get_db()
    user = db.execute(
        "SELECT id,name,email,role,blood_type,phone,is_admin FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()
    donations = db.execute(
        "SELECT * FROM donations WHERE user_id=? ORDER BY donated_at DESC",
        (user['id'],)
    ).fetchall()
    appointments = db.execute(
        "SELECT * FROM appointments WHERE user_id=? ORDER BY scheduled_at",
        (user['id'],)
    ).fetchall()

    return render_template('dashboard.html', user=user, donations=donations, appointments=appointments)


@app.route('/donate', methods=['POST'])
def donate():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    user_id = session['user_id']
    blood_type = request.form.get('blood_type')
    try:
        quantity = int(request.form.get('quantity') or 1)
    except:
        quantity = 1
    location = request.form.get('location') or 'Main Center'

    db = get_db()
    db.execute(
        "INSERT INTO donations (user_id,blood_type,quantity,location,donated_at) VALUES (?,?,?,?,?)",
        (user_id, blood_type, quantity, location, datetime.utcnow().isoformat())
    )
    db.commit()
    flash('Donation recorded — thank you!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/history')
def history():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    db = get_db()
    rows = db.execute("""
        SELECT d.id,d.blood_type,d.quantity,d.location,d.donated_at,u.name
        FROM donations d
        JOIN users u ON u.id=d.user_id
        WHERE d.user_id=?
        ORDER BY d.donated_at DESC
    """, (session['user_id'],)).fetchall()

    return render_template('history.html', donations=rows)


@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    db = get_db()
    if request.method == 'POST':
        sched = request.form.get('scheduled_at')
        try:
            dt = datetime.fromisoformat(sched)
        except Exception:
            dt = datetime.utcnow() + timedelta(days=1)

        db.execute(
            "INSERT INTO appointments (user_id,scheduled_at) VALUES (?,?)",
            (session['user_id'], dt.isoformat())
        )
        db.commit()
        flash('Appointment booked.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('book_appointment.html')


@app.route('/receive', methods=['POST'])
def receive():
    if not session.get('user_id'):
        flash('Please login to request blood.', 'error')
        return redirect(url_for('login'))

    user_id = session['user_id']
    blood_type = request.form.get('blood_type')
    try:
        quantity = int(request.form.get('quantity') or 1)
    except:
        quantity = 1
    location = request.form.get('location') or 'Main Center'

    stock = compute_stock()
    available = stock.get(blood_type, 0)
    if quantity > available:
        flash(f'Not enough units available ({available} units).', 'error')
        return redirect(url_for('dashboard'))

    db = get_db()
    db.execute(
        "INSERT INTO recipients (user_id,blood_type,quantity,location,received_at) VALUES (?,?,?,?,?)",
        (user_id, blood_type, quantity, location, datetime.utcnow().isoformat())
    )
    db.commit()
    flash('Request recorded. Please contact center for confirmation.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    db = get_db()
    user = db.execute("SELECT is_admin FROM users WHERE id=?", (session['user_id'],)).fetchone()
    if not user or not user['is_admin']:
        return "Forbidden", 403

    message = None
    if request.method == 'POST':
        bt = request.form.get('blood_type')
        adjust = int(request.form.get('adjust') or 0)
        db.execute(
            "INSERT INTO donations (user_id,blood_type,quantity,location,donated_at) VALUES (?,?,?,?,?)",
            (session['user_id'], bt, adjust, 'admin-adjust', datetime.utcnow().isoformat())
        )
        db.commit()
        message = f"Adjusted {bt} by {adjust} units."

    donations = db.execute(
        "SELECT blood_type, SUM(quantity) as total FROM donations GROUP BY blood_type"
    ).fetchall()

    return render_template('admin.html', donations=donations, message=message)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        bt = request.form.get('blood_type')
        db.execute(
            "UPDATE users SET name=?, phone=?, blood_type=? WHERE id=?",
            (name, phone, bt, session['user_id'])
        )
        db.commit()
        return redirect(url_for('dashboard'))

    user = db.execute(
        "SELECT id,name,email,role,blood_type,phone FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()

    return render_template('profile.html', user=user)


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    user = None
    if session.get('user_id'):
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()

    reply = get_bot_response(user_message)
    reply = enrich_bot_response(reply, user)
    return jsonify({'reply': reply})


@app.route('/ask_bot', methods=['POST'])
def ask_bot():
    return chat()


# -------------------- Main --------------------
if __name__ == '__main__':
    app.run(debug=True)
