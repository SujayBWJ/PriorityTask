import sqlite3
import os
from app import get_db_connection, init_db, app

def reproduce_issue():
    print("--- Reproducing Reported Issue ---")
    
    with app.app_context():
        init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM graveyard")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password_hash) VALUES (1, 'repro', 'hash')")
    conn.commit()

    # User's State:
    # Task b: P3, 3h
    # Task a: P2, 3h
    print("Setting up initial state: Task b (P3, 3h), Task a (P2, 3h)")
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status) VALUES (1, 'task b', '2026-03-30', 3, 3.0, 8.0, 'Possible')")
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status) VALUES (1, 'task a', '2026-03-30', 2, 3.0, 8.0, 'Possible')")
    conn.commit()

    # User adds: Task c (P5, 2h)
    new_name = "task c"
    new_priority = 5
    new_hours = 2.0
    total_capacity = 8.0
    user_id = 1

    print(f"Adding '{new_name}' (P{new_priority}, {new_hours}h) with Capacity {total_capacity}")

    # --- Logic from add_task ---
    cursor.execute("SELECT SUM(hours_per_day) FROM tasks WHERE user_id = ? AND status = 'Possible'", (user_id,))
    current_load = cursor.fetchone()[0] or 0.0
    print(f"Current load: {current_load}")

    if current_load + new_hours > total_capacity:
        print(f"Detected over capacity: {current_load + new_hours} > {total_capacity}")
        cursor.execute("SELECT id, hours_per_day, priority, name, deadline FROM tasks WHERE user_id = ? AND status = 'Possible' ORDER BY priority ASC, id ASC", (user_id,))
        existing_tasks = cursor.fetchall()
        temp_load = current_load + new_hours
        
        for task in existing_tasks:
            print(f"Checking existing task: {task['name']} (P{task['priority']})")
            if temp_load > total_capacity:
                if task['priority'] < new_priority:
                    print(f"-> Moving {task['name']} to graveyard")
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        cursor.execute("INSERT INTO graveyard (id, user_id, name, deadline, priority, hours_per_day) VALUES (?, ?, ?, ?, ?, ?)", 
                                       (task['id'], user_id, task['name'], task['deadline'], task['priority'], task['hours_per_day']))
                        cursor.execute("DELETE FROM tasks WHERE id = ?", (task['id'],))
                        conn.commit()
                        temp_load -= task['hours_per_day']
                        print(f"   New temp_load: {temp_load}")
                    except Exception as e:
                        conn.rollback()
                        print(f"   FAILED to move: {e}")
                else:
                    print(f"-> Task priority {task['priority']} >= new priority {new_priority}, stopping drop logic.")
                    break
            else:
                break
        
        if temp_load > total_capacity:
            status = 'Impossible'
        else:
            status = 'Possible'
    else:
        print(f"Load {current_load + new_hours} <= {total_capacity}. No drops needed.")
        status = 'Possible'

    print(f"Final status for '{new_name}': {status}")
    conn.close()

if __name__ == "__main__":
    reproduce_issue()
