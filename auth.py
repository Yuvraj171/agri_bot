import json
import os
import datetime
import streamlit as st

def register_user(username, password):
    users_file_path = os.path.join("user_database", "users.json")
    
    # Load existing users
    if os.path.exists(users_file_path):
        with open(users_file_path, 'r') as file:
            users = json.load(file)
    else:
        users = {}
    
    # Check if the user already exists
    if username in users:
        return False  # User already exists
    
    # Add the new user
    users[username] = password
    
    # Save the updated users back to the file
    with open(users_file_path, 'w') as file:
        json.dump(users, file)
    
    return True

def login_user(username, password):
    users_file_path = os.path.join("user_database", "users.json")
    
    if os.path.exists(users_file_path):
        with open(users_file_path, 'r') as file:
            users = json.load(file)
        
        # Check credentials
        if username in users and users[username] == password:
            log_activity(username, "login")
            return True
    return False

def log_activity(username, activity_type):
    activities_file_path = os.path.join("user_database", "activities.json")
    current_time = datetime.datetime.now().isoformat()
    
    activities = []  # Initialize as empty list
    
    # Load existing activities if the file exists and is not empty
    if os.path.exists(activities_file_path):
        try:
            with open(activities_file_path, 'r') as file:
                activities = json.load(file)
        except json.JSONDecodeError:
            # Handle empty or invalid JSON by initializing activities as an empty list
            activities = []
        except Exception as e:
            print(f"An unexpected error occurred while loading activities: {e}")
            # Depending on your error handling policies, you might want to raise the error or handle it
    
    # Append the new activity
    activities.append({"timestamp": current_time, "username": username, "activity_type": activity_type})
    
    # Save the updated activities back to the file
    with open(activities_file_path, 'w') as file:
        json.dump(activities, file)

def show_login_page():
    # Use "Log-In" instead of "Login" and apply the 'login-highlight' class
    st.markdown('<div class="login-highlight">Log-In</div>', unsafe_allow_html=True)
    
    username = st.text_input("", placeholder="Enter your username", key="login_username")
    password = st.text_input("", type="password", placeholder="Enter your password", key="login_password")
    
    if st.button("Login"):
        if login_user(username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Login failed. Please check your username and password.")


def show_registration_page():
    # Use "Register" text and apply the 'registration-highlight' class
    st.markdown('<div class="registration-highlight">Register</div>', unsafe_allow_html=True)
    
    username = st.text_input("", placeholder="Choose your username", key="register_username")
    password = st.text_input("", type="password", placeholder="Choose your password", key="register_password")
    
    if st.button("Create account"):
        if register_user(username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Account created successfully! You're now logged in.")
            st.rerun()
        else:
            st.error("Registration failed. Username might already exist.")