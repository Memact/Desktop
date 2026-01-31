import time
import sqlite3
import os
from engine.main import get_active_window_info, database_writer
import threading
from queue import Queue

DB_PATH = 'test_activity.db'

def print_db_contents():
    if not os.path.exists(DB_PATH):
        print("Database file not created yet.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, process_name, window_title FROM events ORDER BY timestamp DESC")
    events = cursor.fetchall()
    conn.close()
    
    print(f"\n--- Found {len(events)} events in the database ---")
    for event in events:
        print(f"- {event[1]}: {event[2]}")
    print("-----------------------------------------")

def test_activity_capture():
    """Verifies the core logic of the activity capture module."""
    print("--- Starting Test: Activity Capture Verification ---")

    # 1. Setup: Create a temporary database and writer thread
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    log_queue = Queue()
    db_thread = threading.Thread(target=database_writer, args=(log_queue, DB_PATH))
    db_thread.daemon = True
    db_thread.start()

    last_hwnd = None
    
    # 2. Test: Idle period
    print("\nStep 1: Testing idle detection. Please do NOT change the active window for 5 seconds...")
    start_time = time.time()
    while time.time() - start_time < 5:
        current_hwnd, process_name, window_title = get_active_window_info()
        if current_hwnd is not None and current_hwnd != last_hwnd:
            log_queue.put((int(time.time() * 1000), process_name, window_title))
            last_hwnd = current_hwnd
        time.sleep(0.75)

    print("Idle test complete. Verifying no duplicate events were logged...")
    log_queue.join() # Wait for the queue to be empty
    print_db_contents()
    print("Verification: If only one event is listed above, the idle test passed.")

    # 3. Test: Window switching
    print("\nStep 2: Testing window switching. Please switch to a DIFFERENT window now.")
    print("Waiting for a window change...")
    
    start_time = time.time()
    change_detected = False
    while time.time() - start_time < 10: # 10-second timeout
        current_hwnd, process_name, window_title = get_active_window_info()
        if current_hwnd is not None and current_hwnd != last_hwnd:
            print(f"Change detected! New window: {process_name} - {window_title}")
            log_queue.put((int(time.time() * 1000), process_name, window_title))
            last_hwnd = current_hwnd
            change_detected = True
            break
        time.sleep(0.75)

    if not change_detected:
        print("No window change was detected within the timeout.")

    # 4. Final Verification
    print("\nStep 3: Final verification.")
    log_queue.join()
    print_db_contents()
    print("Verification: If two distinct events are listed, the switching test passed.")

    # 5. Cleanup
    log_queue.put(None) # Signal thread to exit
    db_thread.join()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    print("\n--- Test Complete --- ")

if __name__ == "__main__":
    test_activity_capture()
