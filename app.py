import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_key' # In production, use environment variables

# Ensure absolute path for the database file
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'tasks.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Database Initialization script
def init_db():
    with app.app_context():
        conn = get_db_connection()
        schema_path = os.path.join(BASE_DIR, 'schema.sql')
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
            
    return render_template('login.html', show_register=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html', show_register=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    # Sorting descending by priority as per requirements
    cursor.execute("""
        SELECT * FROM tasks 
        WHERE user_id = ? AND status = 'Possible'
        ORDER BY priority DESC
    """, (session['user_id'],))
    tasks = cursor.fetchall()
    
    # Also fetch backlog tasks
    cursor.execute("""
        SELECT * FROM tasks 
        WHERE user_id = ? AND is_backlog = 1 AND status = 'Possible'
        ORDER BY priority DESC
    """, (session['user_id'],))
    backlog_tasks = cursor.fetchall()

    # Also fetch impossible tasks
    cursor.execute("""
        SELECT * FROM tasks 
        WHERE user_id = ? AND status = 'Impossible'
        ORDER BY priority DESC
    """, (session['user_id'],))
    impossible_tasks = cursor.fetchall()
    
    conn.close()
    return render_template('dashboard.html', tasks=tasks, backlog_tasks=backlog_tasks, impossible_tasks=impossible_tasks)

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    name = request.form['name']
    deadline = request.form['deadline']
    priority = int(request.form['priority'])
    hours_per_day = float(request.form['hours_per_day'])
    total_capacity = float(request.form['total_capacity'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Calculate current load
    cursor.execute("SELECT SUM(hours_per_day) FROM tasks WHERE user_id = ? AND status = 'Possible'", (user_id,))
    current_load = cursor.fetchone()[0] or 0.0
    
    # 2. Add current task to DB first (temporarily) to simplify logic, or handle logically
    # We'll handle it logically: if current_load + new_task > total_capacity, execute drop logic
    
    if current_load + hours_per_day > total_capacity:
        # Fetch existing active tasks ordered by priority ASC (lowest first)
        cursor.execute("SELECT id, hours_per_day, priority, name, deadline FROM tasks WHERE user_id = ? AND status = 'Possible' ORDER BY priority ASC, id ASC", (user_id,))
        existing_tasks = cursor.fetchall()
        
        temp_load = current_load + hours_per_day
        dropped_task_ids = []
        
        # Check if the new task itself is lower priority than all others and if it's the one that should be dropped
        # But usually we drop *existing* tasks to make room for *new* ones unless the new one is lower than everything.
        # Requirement: "It must automatically drop the lowest priority task(s) currently in the system to make room for the new task"
        
        for task in existing_tasks:
            if temp_load > total_capacity + 0.0001:
                if task['priority'] < priority:
                    # Move to graveyard using a transaction
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        # 1. Insert into graveyard (let DB handle the ID)
                        cursor.execute("""
                            INSERT INTO graveyard (user_id, name, deadline, priority, hours_per_day)
                            VALUES (?, ?, ?, ?, ?)
                        """, (user_id, task['name'], task['deadline'], task['priority'], task['hours_per_day']))
                        
                        # 2. Delete from tasks
                        cursor.execute("DELETE FROM tasks WHERE id = ?", (task['id'],))
                        conn.commit()
                        
                        temp_load -= task['hours_per_day']
                        dropped_task_ids.append(task['id'])
                    except Exception as e:
                        conn.rollback()
                        print(f"Transaction failed: {e}")
                else:
                    break # All remaining tasks are higher or equal priority.
            else:
                break
                
        if temp_load > total_capacity + 0.0001:
            # If still over capacity, the new task itself is impossible if its priority is the lowest or doesn't fit
            status = 'Impossible'
        else:
            status = 'Possible'
    else:
        status = 'Possible'
        
    cursor.execute("""
        INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, deadline, priority, hours_per_day, total_capacity, status))
    
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/recalculate', methods=['POST'])
def recalculate():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Identify missed tasks (deadline passed and status is Possible)
    # requirements say "identify tasks not completed today and automatically mark them as Backlog"
    # We'll assume a "completed" task is one that's deleted or archived, but for now let's use the 'status' or a 'completed' flag.
    # The requirement says "not completed". I'll add a 'completed' column or just use 'status' logic.
    # Let's add a 'completed' status or similar.
    
    cursor.execute("UPDATE tasks SET is_backlog = 1 WHERE user_id = ? AND deadline < ? AND status = 'Possible' AND is_backlog = 0", (user_id, today))
    conn.commit()
    
    # 2. Recalculate total required hours
    cursor.execute("SELECT SUM(hours_per_day), MAX(total_capacity) FROM tasks WHERE user_id = ? AND status = 'Possible'", (user_id,))
    row = cursor.fetchone()
    total_required = row[0] or 0.0
    total_capacity = row[1] or 0.0
    
    if total_required > total_capacity + 0.0001:
        # Run Auto-Drop Logic again
        cursor.execute("SELECT id, hours_per_day, priority, name, deadline FROM tasks WHERE user_id = ? AND status = 'Possible' ORDER BY priority ASC, id ASC", (user_id,))
        existing_tasks = cursor.fetchall()
        
        temp_load = total_required
        for task in existing_tasks:
            if temp_load > total_capacity + 0.0001:
                try:
                    cursor.execute("BEGIN TRANSACTION")
                    cursor.execute("""
                        INSERT INTO graveyard (user_id, name, deadline, priority, hours_per_day)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, task['name'], task['deadline'], task['priority'], task['hours_per_day']))
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task['id'],))
                    conn.commit()
                    temp_load -= task['hours_per_day']
                except Exception as e:
                    conn.rollback()
                    print(f"Transaction failed: {e}")
            else:
                break
        
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/complete_task/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure current user owns the task
    cursor.execute("UPDATE tasks SET status = 'Completed' WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/api/graveyard')
def get_graveyard():
    if 'user_id' not in session:
        return {"error": "Unauthorized"}, 401
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM graveyard WHERE user_id = ? ORDER BY dropped_at DESC", (session['user_id'],))
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"tasks": tasks}

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
