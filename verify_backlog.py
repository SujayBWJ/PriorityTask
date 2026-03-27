import sqlite3
from datetime import datetime, timedelta
from app import get_db_connection

def test_backlog_logic():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 0. Clean tasks
    cursor.execute("DELETE FROM tasks")
    conn.commit()

    # 1. Add User if not exists
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password_hash) VALUES (1, 'testuser', 'hash')")
    conn.commit()

    # 2. Add a task with a past deadline (yesterday)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status, is_backlog) VALUES (1, 'Past Task', ?, 4, 3, 5, 'Possible', 0)", (yesterday,))
    
    # 3. Add a future task (today/tomorrow)
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status, is_backlog) VALUES (1, 'Future Task', ?, 5, 3, 5, 'Possible', 0)", (today,))
    conn.commit()

    # Total load = 3 + 3 = 6 > 5.

    # 4. Run Backlog / Recalculate Logic
    # Identify missed tasks
    cursor.execute("UPDATE tasks SET is_backlog = 1 WHERE user_id = 1 AND deadline < ? AND status = 'Possible' AND is_backlog = 0", (today,))
    
    # Recalculate
    cursor.execute("SELECT SUM(hours_per_day), MAX(total_capacity) FROM tasks WHERE user_id = 1 AND status = 'Possible'")
    total_required, total_capacity = cursor.fetchone()
    
    print(f"Total Required: {total_required}, Capacity: {total_capacity}")
    
    if total_required > total_capacity:
        cursor.execute("SELECT id, hours_per_day, priority FROM tasks WHERE user_id = 1 AND status = 'Possible' ORDER BY priority ASC, id ASC")
        tasks = cursor.fetchall()
        temp_load = total_required
        for task in tasks:
            if temp_load > total_capacity:
                print(f"Dropping task ID {task['id']} (Priority {task['priority']})")
                cursor.execute("UPDATE tasks SET status = 'Impossible' WHERE id = ?", (task['id'],))
                temp_load -= task['hours_per_day']
            else:
                break
    conn.commit()
    
    # Check results
    cursor.execute("SELECT name, status, is_backlog FROM tasks WHERE user_id = 1")
    results = cursor.fetchall()
    print("\nResults:")
    for res in results:
        print(f"Task: {res['name']}, Status: {res['status']}, Backlog: {res['is_backlog']}")
    
    conn.close()

if __name__ == "__main__":
    test_backlog_logic()
