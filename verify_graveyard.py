import sqlite3
import os
from app import get_db_connection, init_db, app

def verify_graveyard_logic():
    print("--- Starting Graveyard Logic Verification ---")
    
    # 1. Initialize clean state
    with app.app_context():
        init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM graveyard")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password_hash) VALUES (1, 'tester', 'hash')")
    conn.commit()

    # 2. Add base tasks
    print("Adding base tasks...")
    # Task 1: P2, 4 hours
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status) VALUES (1, 'Low Prio', '2026-03-29', 2, 4, 8, 'Possible')")
    # Task 2: P3, 3 hours (Total: 7/8)
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status) VALUES (1, 'Mid Prio', '2026-03-29', 3, 3, 8, 'Possible')")
    conn.commit()

    # 3. Simulate "add_task" for a high priority task (P5, 5 hours)
    # Total: 7 + 5 = 12 > 8. 
    # Current active: Low Prio (P2), Mid Prio (P3).
    # Expected: Low Prio (P2) is dropped to graveyard. Mid Prio (P3) + New Task (P5) = 3 + 5 = 8 (Fits!)
    
    user_id = 1
    new_task_name = "Critical Task"
    new_task_priority = 5
    new_task_hours = 5
    total_capacity = 8

    print(f"Adding '{new_task_name}' (Priority {new_task_priority}, {new_task_hours} hrs)...")

    # Fetch existing active tasks ordered by priority ASC (lowest first)
    cursor.execute("SELECT id, name, deadline, priority, hours_per_day FROM tasks WHERE user_id = ? AND status = 'Possible' ORDER BY priority ASC, id ASC", (user_id,))
    existing_tasks = cursor.fetchall()
    
    current_load = sum(t['hours_per_day'] for t in existing_tasks)
    temp_load = current_load + new_task_hours
    
    # Run the transaction logic
    for task in existing_tasks:
        if temp_load > total_capacity:
            if task['priority'] < new_task_priority:
                print(f"Moving '{task['name']}' to graveyard...")
                try:
                    cursor.execute("BEGIN TRANSACTION")
                    cursor.execute("""
                        INSERT INTO graveyard (id, user_id, name, deadline, priority, hours_per_day)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (task['id'], user_id, task['name'], task['deadline'], task['priority'], task['hours_per_day']))
                    cursor.execute("DELETE FROM tasks WHERE id = ?", (task['id'],))
                    conn.commit()
                    temp_load -= task['hours_per_day']
                except Exception as e:
                    conn.rollback()
                    print(f"Transaction failed: {e}")
            else:
                break
        else:
            break

    # Insert the new task
    status = 'Possible' if temp_load <= total_capacity else 'Impossible'
    cursor.execute("""
        INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, new_task_name, '2026-03-29', new_task_priority, new_task_hours, total_capacity, status))
    conn.commit()

    # 4. Final verification
    print("\n--- Verification Results ---")
    cursor.execute("SELECT name FROM tasks WHERE status = 'Possible'")
    active = [row['name'] for row in cursor.fetchall()]
    print(f"Active Tasks: {active}")

    cursor.execute("SELECT name FROM graveyard")
    graveyard = [row['name'] for row in cursor.fetchall()]
    print(f"Graveyard Tasks: {graveyard}")

    # Assertions
    assert "Low Prio" in graveyard, "Low Prio task should be in graveyard"
    assert "Mid Prio" in active, "Mid Prio task should be active"
    assert "Critical Task" in active, "Critical task should be active"
    
    print("\nPASS: Graveyard logic verified successfully!")
    conn.close()

if __name__ == "__main__":
    try:
        verify_graveyard_logic()
    except Exception as e:
        print(f"\nFAIL: Verification failed with error: {e}")
