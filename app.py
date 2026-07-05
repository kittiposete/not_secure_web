from flask import Flask, request, render_template, render_template_string, redirect, url_for, session, jsonify
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecret_lab_key"

conn = sqlite3.connect(':memory:', check_same_thread=False)

def init_db():
    cursor = conn.cursor()
    # Schema
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            bio TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task TEXT NOT NULL,
            completed INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            receiver_id INTEGER,
            subject TEXT,
            body TEXT,
            read INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Seed Data
    cursor.execute("INSERT INTO users (email, password, bio) VALUES ('test@example.com', 'password123', 'Security Lab Admin')")
    cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (1, 'Learn OWASP ZAP basics', 1)")
    cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (1, 'Practice SQL Injection on this app', 0)")
    cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (1, 'Write a vulnerability report', 0)")
    
    # Generate mass users and tasks for spidering
    for i in range(2, 30):
        email = f"user{i}@example.com"
        cursor.execute("INSERT INTO users (email, password, bio) VALUES (?, ?, ?)", (email, "password123", f"Hello I am user {i}"))
        for j in range(3):
            cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (?, ?, 0)", (i, f"Sample task {j} for user {i}"))
            
    # Seed messages
    for i in range(2, 30):
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, subject, body) VALUES (?, ?, ?, ?)", 
                       (i, 1, "Hello Admin", f"Just testing the system. From user {i}"))
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, subject, body) VALUES (?, ?, ?, ?)", 
                       (1, i, "Welcome", "Welcome to the system!"))
    
    conn.commit()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor()
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        # Secured login to force ZAP to authenticate
        query = "SELECT id FROM users WHERE email = ? AND password = ?"
        try:
            cursor.execute(query, (email, password))
            user = cursor.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid email or password.'
        except sqlite3.Error as e:
            error = f"Database Error: {e}"
            
    return render_template('login.html', error=error)

@app.route('/dashboard')
def dashboard():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM todos WHERE user_id = ? AND completed = 1", (session['user_id'],))
    tasks_completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND read = 0", (session['user_id'],))
    unread = cursor.fetchone()[0]
    
    stats = {'users': users_count, 'tasks_completed': tasks_completed, 'unread': unread}
    return render_template('dashboard.html', stats=stats)

@app.route('/todos')
def todos():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user_id = session['user_id']
    search = request.args.get('search', '')
    
    # INTENTIONAL VULNERABILITY: SQL Injection after login
    if search:
        query = f"SELECT id, task, completed FROM todos WHERE user_id = {user_id} AND task LIKE '%{search}%'"
    else:
        query = f"SELECT id, task, completed FROM todos WHERE user_id = {user_id}"
        
    try:
        cursor.execute(query)
        tasks = cursor.fetchall()
        error = None
    except sqlite3.Error as e:
        tasks = []
        error = f"Database Error: {e}"
    
    return render_template('todos.html', todos=tasks, search=search, error=error)

@app.route('/add_todo', methods=['POST'])
def add_todo():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    task = request.form.get('task')
    if task:
        cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (?, ?, 0)", (session['user_id'], task))
        conn.commit()
    return redirect(url_for('todos'))

@app.route('/toggle_todo/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    cursor.execute("SELECT completed FROM todos WHERE id = ? AND user_id = ?", (todo_id, session['user_id']))
    result = cursor.fetchone()
    if result:
        cursor.execute("UPDATE todos SET completed = ? WHERE id = ?", (0 if result[0] else 1, todo_id))
        conn.commit()
    return redirect(url_for('todos'))

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    cursor.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, session['user_id']))
    conn.commit()
    return redirect(url_for('todos'))

@app.route('/users')
def users_list():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page
    cursor.execute("SELECT id, email FROM users LIMIT ? OFFSET ?", (per_page, offset))
    users = cursor.fetchall()
    return render_template('users.html', users=users, page=page)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404
    return render_template('profile.html', user=user)

@app.route('/inbox')
def inbox():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    cursor.execute('''
        SELECT m.*, u.email 
        FROM messages m 
        JOIN users u ON m.sender_id = u.id 
        WHERE m.receiver_id = ? 
        ORDER BY m.timestamp DESC
    ''', (session['user_id'],))
    messages = cursor.fetchall()
    # Mark as read
    cursor.execute("UPDATE messages SET read = 1 WHERE receiver_id = ?", (session['user_id'],))
    conn.commit()
    return render_template('inbox.html', messages=messages)

@app.route('/message/send', methods=['POST'])
def send_message():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    recipient_email = request.form.get('recipient')
    subject = request.form.get('subject')
    body = request.form.get('body')
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (recipient_email,))
    user = cursor.fetchone()
    if user:
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, subject, body) VALUES (?, ?, ?, ?)",
                       (session['user_id'], user[0], subject, body))
        conn.commit()
    return redirect(url_for('inbox'))

@app.route('/settings')
def settings():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cursor.fetchone()
    return render_template('settings.html', user=user, msg=request.args.get('msg'))

@app.route('/settings/profile', methods=['POST'])
def update_profile():
    cursor = conn.cursor()
    if 'user_id' not in session: return redirect(url_for('login'))
    bio = request.form.get('bio')
    cursor.execute("UPDATE users SET bio = ? WHERE id = ?", (bio, session['user_id']))
    conn.commit()
    return redirect(url_for('settings', msg='Profile updated successfully'))

@app.route('/settings/password', methods=['POST'])
def change_password():
    if 'user_id' not in session: return redirect(url_for('login'))
    return redirect(url_for('settings', msg='Password change simulated.'))

@app.route('/settings/upload', methods=['POST'])
def upload_avatar():
    if 'user_id' not in session: return redirect(url_for('login'))
    # Mock upload endpoint for ZAP
    return redirect(url_for('settings', msg='File upload simulated.'))

@app.route('/help')
def help_center():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('help.html')

# API Endpoints for crawling
@app.route('/api/v1/users')
def api_users():
    cursor = conn.cursor()
    cursor.execute("SELECT id, email FROM users LIMIT 5")
    return jsonify([{'id': u[0], 'email': u[1]} for u in cursor.fetchall()])

@app.route('/api/v1/todos/stats')
def api_stats():
    return jsonify({'status': 'ok', 'completed': 100, 'pending': 50})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# --- PUBLIC ROUTES ---
@app.route('/public/<page>')
def public_page(page):
    valid_pages = ['privacy', 'about', 'document', 'contact', 'copyright']
    if page not in valid_pages:
        return "Page not found", 404
    
    titles = {
        'privacy': 'Privacy Policy',
        'about': 'About This Website',
        'document': 'Documentation',
        'contact': 'Contact Us',
        'copyright': 'Copyright Information'
    }
    
    return render_template_string('''
        {% extends "base.html" %}
        {% block title %}{{ title }}{% endblock %}
        {% block content %}
        <div class="card" style="max-width: 800px; margin: 0 auto;">
            <h2>{{ title }}</h2>
            <p style="color: var(--text-muted); line-height: 1.6;">
                This is the {{ title }} page. It is accessible to the public without requiring authentication.
            </p>
            <a href="/" class="btn btn-outline" style="margin-top: 2rem;">Back to Login</a>
        </div>
        {% endblock %}
    ''', title=titles[page])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
