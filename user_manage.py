import json
import os
import time

users_db_path = "users_db.json"
activity_log_path = "activity_log.json"

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return [] if filename == activity_log_path else {}
    return [] if filename == activity_log_path else {}

def save_json(filename, data):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

def register_user(username, password):
    users = load_json(users_db_path)
    if username in users:
        return False  # User already exists
    users[username] = password  # Hash passwords in a real application
    save_json(users_db_path, users)
    return True

def login_user(username, password):
    users = load_json(users_db_path)
    return username in users and users[username] == password

def log_activity(username, action):
    log = load_json(activity_log_path)
    log.append({"username": username, "action": action, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")})
    save_json(activity_log_path, log)
