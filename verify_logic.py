import sqlite3
from app import get_db_connection

def test_capacity_logic():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 0. Clean tasks
    cursor.execute("DELETE FROM tasks")
    conn.commit()

    # 1. Add User if not exists
    cursor.execute("INSERT OR IGNORE INTO users (id, username, password_hash) VALUES (1, 'testuser', 'hash')")
    conn.commit()

    # 2. Add high priority task (Priority 5, 4 hours, Capacity 8)
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status) VALUES (1, 'High Prio', '2026-03-27', 5, 4, 8, 'Possible')")
    
    # 3. Add medium priority task (Priority 3, 5 hours, Capacity 8)
    # Total = 4+5 = 9 > 8. Should drop nothing yet because it's not implemented in this raw insert.
    # But wait, I want to test the logic in add_task route.
    # I'll simulate the logic manually or use the app context.
    
    cursor.execute("INSERT INTO tasks (user_id, name, deadline, priority, hours_per_day, total_capacity, status) VALUES (1, 'Med Prio', '2026-03-27', 3, 5, 8, 'Possible')")
    conn.commit()
    
    # 4. Run "Auto-Drop" logic (simulating add_task)
    cursor.execute("SELECT id, hours_per_day, priority FROM tasks WHERE user_id = 1 AND status = 'Possible' ORDER BY priority ASC, id ASC")
    tasks = cursor.fetchall()
    
    total_load = sum(t['hours_per_day'] for t in tasks)
    capacity = 8
    
    print(f"Initial Load: {total_load}")
    
    if total_load > capacity:
        for task in tasks:
            if total_load > capacity:
                print(f"Dropping task ID {task['id']} (Priority {task['priority']})")
                cursor.execute("UPDATE tasks SET status = 'Impossible' WHERE id = ?", (task['id'],))
                total_load -= task['hours_per_day']
            else:
                break
    conn.commit()
    
    # Check results
    cursor.execute("SELECT name, status FROM tasks WHERE user_id = 1")
    results = cursor.fetchall()
    print("\nResults:")
    for res in results:
        print(f"Task: {res['name']}, Status: {res['status']}")
    
    conn.close()

if __name__ == "__main__":
    test_capacity_logic()
