import os

def ensure_user_database_exists():
    database_path = "user_database"
    os.makedirs(database_path, exist_ok=True)