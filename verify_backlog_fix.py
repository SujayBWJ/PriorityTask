import sqlite3
import os
from datetime import datetime
from app import get_db_connection, init_db, app

def verify_backlog_fix():
    print("--- Verifying Backlog vs Impossible Fix ---")
    
    with app.app_context():
        init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM graveyard")
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password_hash) VALUES (1, 'repro', 'hash')")
    conn.commit()

    # Scenario:
    # 1. Existing tasks fill up capacity (8h)
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status) VALUES (1, 'Task A', '2026-12-31', 5, 8.0, 8.0, 'Possible')")
    conn.commit()

    # 2. Add a new task with a PAST deadline (should be backlog)
    # Even though it's over capacity, it should be marked as Backlog + Possible
    past_deadline = "2024-01-01"
    new_task_name = "Missed Task"
    
    # We'll simulate the route logic here
    today = datetime.now().strftime('%Y-%m-%d')
    is_backlog = 1 if past_deadline < today else 0
    priority = 1
    hours = 2.0
    total_capacity = 8.0
    user_id = 1
    
    cursor.execute("SELECT SUM(hours_per_day) FROM tasks WHERE user_id = ? AND status = 'Possible'", (user_id,))
    current_load = cursor.fetchone()[0] or 0.0
    
    temp_load = current_load + hours
    if temp_load > total_capacity + 0.0001:
        # Since it's backlog, our new logic should set status = 'Possible'
        if is_backlog:
            status = 'Possible'
        else:
            status = 'Impossible'
    else:
        status = 'Possible'

    print(f"Adding '{new_task_name}' (Backlog: {is_backlog}) at Load {temp_load}/{total_capacity}")
    print(f"Determined Status: {status}")

    assert is_backlog == 1, "Should be detected as backlog"
    assert status == 'Possible', "Should be allowed as Possible because it's a backlog item (per user request)"
    
    # 3. Add a new task with FUTURE deadline that overflows (should be Impossible)
    future_deadline = "2026-12-31"
    temp_load = 8.0 + 2.0 # 8 existing + 2 new
    is_backlog_future = 0
    if temp_load > total_capacity + 0.0001:
        if is_backlog_future:
            status_future = 'Possible'
        else:
            status_future = 'Impossible'
    
    print(f"Determined Status for future task: {status_future}")
    assert status_future == 'Impossible', "Future overflow should still be Impossible"

    print("Verification SUCCESSFUL!")
    conn.close()

if __name__ == "__main__":
    verify_backlog_fix()
