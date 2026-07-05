from flask import Flask, request, render_template_string, redirect, url_for, session
import sqlite3

app = Flask(__name__)
# Secret key required for session management
app.secret_key = "supersecret_lab_key"

# In-memory database connection
# check_same_thread=False allows Flask's worker threads to share the in-memory DB
conn = sqlite3.connect(':memory:', check_same_thread=False)
cursor = conn.cursor()

# Initialize Database Schema
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        password TEXT NOT NULL
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

# Seed Initial Data
cursor.execute("INSERT INTO users (email, password) VALUES ('test@example.com', 'password123')")
cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (1, 'Learn OWASP ZAP basics', 1)")
cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (1, 'Practice SQL Injection on this app', 0)")
cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (1, 'Write a vulnerability report', 0)")
conn.commit()


LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Login - Security Lab</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg-color: #0f172a;
            --surface: rgba(30, 41, 59, 0.7);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --error: #ef4444;
        }
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }
        .container {
            background: var(--surface);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 3rem;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            width: 100%;
            max-width: 400px;
        }
        h2 { margin-top: 0; font-weight: 800; font-size: 2rem; margin-bottom: 0.5rem; text-align: center; }
        p.subtitle { text-align: center; color: var(--text-muted); margin-bottom: 2rem; font-size: 0.9rem; }
        .error { color: var(--error); background: rgba(239, 68, 68, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 1rem; border: 1px solid rgba(239, 68, 68, 0.2); }
        label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; font-weight: 600; color: var(--text-muted); }
        input[type="text"], input[type="password"] { 
            width: 100%; 
            padding: 12px 16px; 
            margin-bottom: 1.5rem; 
            border: 1px solid rgba(255,255,255,0.1); 
            background: rgba(0,0,0,0.2);
            color: white;
            border-radius: 12px;
            box-sizing: border-box;
            transition: all 0.3s ease;
            font-size: 1rem;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        input[type="submit"] { 
            width: 100%; 
            padding: 12px; 
            background: var(--primary); 
            color: white; 
            border: none; 
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        input[type="submit"]:hover {
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -10px rgba(99, 102, 241, 0.6);
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Security Lab</h2>
        <p class="subtitle">Log in to view your tasks</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/">
            <label>Email</label>
            <input type="text" name="email" placeholder="test@example.com" required>
            
            <label>Password</label>
            <input type="password" name="password" placeholder="••••••••" required>
            
            <input type="submit" value="Sign In">
        </form>
    </div>
</body>
</html>
'''

TODO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>To-Do List</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --bg-color: #0f172a;
            --surface: rgba(30, 41, 59, 0.7);
            --surface-hover: rgba(30, 41, 59, 0.9);
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --danger: #ef4444;
            --danger-hover: #dc2626;
            --success: #10b981;
        }
        body { 
            font-family: 'Inter', sans-serif; 
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: var(--text);
            min-height: 100vh;
            margin: 0;
            padding: 40px 20px;
        }
        .container {
            background: var(--surface);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 3rem;
            border-radius: 24px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        h2 { margin: 0; font-weight: 800; font-size: 2rem; }
        .logout-btn {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            transition: color 0.3s;
        }
        .logout-btn:hover { color: var(--text); }
        
        .add-form {
            display: flex;
            gap: 10px;
            margin-bottom: 2rem;
        }
        .add-form input[type="text"] {
            flex-grow: 1;
            padding: 12px 16px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(0,0,0,0.2);
            color: white;
            border-radius: 12px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .add-form input[type="text"]:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        .add-form button {
            background: var(--primary);
            color: white;
            border: none;
            padding: 0 24px;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .add-form button:hover {
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -10px rgba(99, 102, 241, 0.6);
        }
        
        .todo-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .todo-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 12px;
            margin-bottom: 10px;
            transition: all 0.3s ease;
        }
        .todo-item:hover {
            background: rgba(255,255,255,0.08);
            transform: translateX(4px);
        }
        .todo-item.completed .task-text {
            text-decoration: line-through;
            color: var(--text-muted);
        }
        .task-content {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-grow: 1;
        }
        .task-text {
            font-size: 1.05rem;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .actions {
            display: flex;
            gap: 8px;
        }
        .btn-icon {
            background: none;
            border: none;
            cursor: pointer;
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }
        .btn-toggle {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }
        .btn-toggle:hover {
            background: var(--success);
            color: white;
        }
        .btn-delete {
            background: rgba(239, 68, 68, 0.1);
            color: var(--danger);
        }
        .btn-delete:hover {
            background: var(--danger);
            color: white;
        }
        .empty-state {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Tasks</h2>
            <a href="{{ url_for('logout') }}" class="logout-btn">Logout</a>
        </div>
        
        <form class="add-form" action="{{ url_for('todos') }}" method="GET" style="margin-bottom: 1rem;">
            <input type="text" name="search" placeholder="Search tasks..." value="{{ search }}" autocomplete="off">
            <button type="submit">Search</button>
        </form>
        {% if error %}<div class="error" style="color: var(--danger); background: rgba(239, 68, 68, 0.1); padding: 10px; border-radius: 8px; margin-bottom: 1rem; border: 1px solid rgba(239, 68, 68, 0.2);">{{ error }}</div>{% endif %}
        
        <form class="add-form" action="{{ url_for('add_todo') }}" method="POST">
            <input type="text" name="task" placeholder="What needs to be done?" required autocomplete="off">
            <button type="submit">Add</button>
        </form>
        
        <ul class="todo-list">
            {% for todo in todos %}
                <li class="todo-item {% if todo[2] %}completed{% endif %}">
                    <div class="task-content">
                        <span class="task-text">{{ todo[1] }}</span>
                    </div>
                    <div class="actions">
                        <form action="{{ url_for('toggle_todo', todo_id=todo[0]) }}" method="POST" style="margin:0;">
                            <button type="submit" class="btn-icon btn-toggle" title="Toggle Complete">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
                            </button>
                        </form>
                        <form action="{{ url_for('delete_todo', todo_id=todo[0]) }}" method="POST" style="margin:0;">
                            <button type="submit" class="btn-icon btn-delete" title="Delete Task">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                            </button>
                        </form>
                    </div>
                </li>
            {% else %}
                <div class="empty-state">
                    <p>No tasks yet. Add one above!</p>
                </div>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        # Secured login query: Using parameterized queries to prevent SQLi here
        # This forces the scanner to successfully authenticate to find vulnerabilities deeper in the app
        query = "SELECT id FROM users WHERE email = ? AND password = ?"
        
        try:
            cursor.execute(query, (email, password))
            user = cursor.fetchone()
            
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('todos'))
            else:
                error = 'Invalid email or password.'
        except sqlite3.Error as e:
            # Exposing database errors to the user helps with Error-Based SQLi testing
            error = f"Database Error: {e}"
            
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/todos')
def todos():
    # Basic access control check
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    search = request.args.get('search', '')
    
    # INTENTIONAL VULNERABILITY: SQL Injection after login
    # Directly concatenating the search term into the SQL query
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
        # Exposing database errors to help with Error-Based SQLi testing
        error = f"Database Error: {e}"
    
    return render_template_string(TODO_TEMPLATE, todos=tasks, search=search, error=error)

@app.route('/add_todo', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    task = request.form.get('task')
    if task:
        cursor.execute("INSERT INTO todos (user_id, task, completed) VALUES (?, ?, 0)", (session['user_id'], task))
        conn.commit()
        
    return redirect(url_for('todos'))

@app.route('/toggle_todo/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Check current status securely
    cursor.execute("SELECT completed FROM todos WHERE id = ? AND user_id = ?", (todo_id, session['user_id']))
    result = cursor.fetchone()
    
    if result:
        new_status = 0 if result[0] else 1
        cursor.execute("UPDATE todos SET completed = ? WHERE id = ?", (new_status, todo_id))
        conn.commit()
        
    return redirect(url_for('todos'))

@app.route('/delete_todo/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Secure deletion
    cursor.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, session['user_id']))
    conn.commit()
    
    return redirect(url_for('todos'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Strictly bind to localhost (127.0.0.1) on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
