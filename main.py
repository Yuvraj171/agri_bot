import json
import os
import time
import streamlit as st
from streamlit_chat import message
import requests
import whisper
import tempfile
from user_manage import log_activity, register_user, login_user
from audio_recorder_streamlit import audio_recorder  # Add this import for audio recording



def ensure_user_database_exists():
    database_path = "user_database"
    os.makedirs(database_path, exist_ok=True)

# Update paths to include the 'user_database' folder
# Correct paths to include the 'user_database' folder
users_db_path = os.path.join("user_database", "users_db.json")
activity_log_path = os.path.join("user_database", "activity_log.json")



def query(payload):
    history_str = " ".join([f"User: {user_msg} , Assistant: {assistant_msg}" for user_msg, assistant_msg in st.session_state.conversation_history])
    headers = {"Authorization": f"Bearer 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"}
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    json_body = {
        "inputs": f"[INST] <<SYS>> Your job is to talk like a farming assistant for a farmer. Every response must sound the same. Also, remember the previous conversation {history_str} and answer accordingly <<SYS>> User: {payload} Assistant: [/INST]",
        "parameters": {"max_new_tokens": 4096, "top_p": 0.9, "temperature": 0.7}
    }
    
    response = requests.post(API_URL, headers=headers, json=json_body)
    
    # Check the response status code before attempting to decode JSON
    if response.status_code == 200:
        return response.json()
    else:
        # Handle non-successful responses or log them for debugging
        print(f"Failed to get a valid response: Status code {response.status_code}, Response text: {response.text}")
        return {"error": f"API request failed with status code {response.status_code}"}


def save_conversation_to_file(conversation_history):
    """Append the conversation history to a JSON file based on today's date."""
    date_today = time.strftime("%Y-%m-%d")
    filename = f"conversation_{date_today}.json"
    filepath = os.path.join("./chat data", filename)  # Adjust the path as needed
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True) # Ensure directory exists
    
    if os.path.exists(filepath):
        # File exists, read the current content and append
        with open(filepath, 'r') as f:
            existing_content = json.load(f)
        existing_content.extend(conversation_history)
        with open(filepath, 'w') as f:
            json.dump(existing_content, f, indent=4)
    else:
        # File does not exist, create a new one
        with open(filepath, 'w') as f:
            json.dump(conversation_history, f, indent=4)
    print(f"Conversation updated in {filepath}")


def apply_custom_css():
    background_image_url = "https://images.pexels.com/photos/289334/pexels-photo-289334.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
    # Additional styles for chat messages
    chat_message_styles = """
    <style>
        /* Background styling */
        .stApp {
            background-image: url(%s);
            background-size: cover;
        }
        /* Style for the chat message bubbles */
        .stChatBubble {
            background-color: rgba(255, 255, 255, 0.8) !important; /* Semi-transparent white */
            border-radius: 20px !important; /* Rounded corners */
            border: 1px solid rgba(0, 0, 0, 0.1) !important; /* Light border */
            padding: 10px 20px !important; /* Adjust padding */
            max-width: fit-content !important; /* Fit to content */
            margin: 10px !important; /* Spacing between messages */
        }
        /* Style adjustments for the text inside chat bubbles for better readability */
        .stMarkdown {
            background-color: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
        }
    </style>
    """ % background_image_url
    st.markdown(chat_message_styles, unsafe_allow_html=True)


def transcribe_audio(audio_file):
    model=whisper.load_model("base")
    result = model.transcribe(audio_file, fp16=False)
    return result["text"]



def transcribe_audio_or_use_text_input(audio_file, text_input=None):
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_audio:
            tmp_audio.write(audio_file.read())
            tmp_audio_path = tmp_audio.name
        transcribed_text = transcribe_audio(tmp_audio_path)
    else:
        transcribed_text = text_input
    return transcribed_text


# Define the login and registration pages
def show_login_page():
    """Displays the login page."""
    st.sidebar.subheader("Login")
    username = st.sidebar.text_input("Username", key="login_username")
    password = st.sidebar.text_input("Password", type="password", key="login_password")
    if st.sidebar.button("Login"):
        if login_user(username, password):
            st.sidebar.success("Logged in successfully!")
            st.session_state["authenticated"] = True
            st.experimental_rerun()  # Rerun the app to update the state
        else:
            st.sidebar.error("Invalid username or password.")

def show_registration_page():
    """Displays the registration page."""
    st.sidebar.subheader("Register")
    new_username = st.sidebar.text_input("Choose a username", key="new_username")
    new_password = st.sidebar.text_input("Choose a password", type="password", key="new_password")
    if st.sidebar.button("Register"):
        if register_user(new_username, new_password):
            st.sidebar.success("Registered successfully. Please login.")
            st.session_state["just_registered"] = True  # Optionally use this state for any post-registration logic
        else:
            st.sidebar.error("Registration failed. User might already exist.")
            

def register_user(username, password):
    # Ensure paths are correct
    ensure_user_database_exists()
    users = load_json(users_db_path)  # Using the corrected path
    if username in users:
        return False  # User already exists
    users[username] = password  # Hash passwords in a real application
    save_json(users_db_path, users)  # Using the corrected path
    return True

def login_user(username, password):
    # Ensure paths are correct
    ensure_user_database_exists()
    users = load_json(users_db_path)  # Using the corrected path
    if username in users and users[username] == password:
        log_activity(username, "login")
        return True
    return False

def load_json(filename):
    # Call here to ensure directory exists before attempting to read
    ensure_user_database_exists()
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return json.load(file)
    return {} if "users_db.json" in filename else []  # Return appropriate empty structure

def save_json(filename, data):
    # Call here to ensure directory exists before attempting to write
    ensure_user_database_exists()
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)

# Rest of your functions (register_user, login_user, log_activity, etc.) remain the same


def log_activity(username, activity_type):
    # Ensure paths are correct
    ensure_user_database_exists()
    activities = load_json(activity_log_path)  # Using the corrected path
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    new_activity = {"username": username, "activity_type": activity_type, "timestamp": current_time}
    activities.append(new_activity)
    save_json(activity_log_path, activities)  # Using the corrected path


            
def chat_interface():
    st.header("AgriChat 🌾 - Chat")

    # Check for existing conversation history in the session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # Input options for the user
    input_type = st.radio("Choose input type:", ["Text", "Audio", "Record Audio"])  # Add "Record Audio" option

    if input_type == "Text":
        user_input = st.text_input("Type your message here:")
        if st.button("Send"):
            handle_user_input(user_input)

    elif input_type == "Audio":
        audio_input = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg"])
        if st.button("Transcribe and Send"):
            if audio_input is not None:
                transcribed_text = transcribe_audio_or_use_text_input(audio_input)
                handle_user_input(transcribed_text)

    elif input_type == "Record Audio":  # New option for recording audio
        audio_bytes = audio_recorder()  # Call the audio_recorder function
        if audio_bytes:
            # You could play the audio back to the user or proceed directly to transcribing it
            st.audio(audio_bytes, format="audio/wav")
            if st.button("Transcribe and Send"):
                transcribed_text = transcribe_audio_or_use_text_input(None, audio_bytes)
                handle_user_input(transcribed_text)

    # Display the conversation history
    for idx, (user_msg, assistant_msg) in enumerate(st.session_state.conversation_history):
        message(user_msg, is_user=True, key=f"user_{idx}")
        message(assistant_msg, key=f"assistant_{idx}")

            

def handle_user_input(input_text):
    if input_text:
        response = query(input_text)
        try:
            assistant_response = response[0]['generated_text'].split('[/INST]')[1].strip()
            st.session_state.conversation_history.append((input_text, assistant_response))
        except Exception as e:
            st.error("An error occurred while processing the response from the assistant.")
            st.error(e)                        
            

def show_logout_interface():
    if st.sidebar.button("Logout"):
        # Log the logout activity
        log_activity(st.session_state["username"], "logout")
        del st.session_state["username"]
        st.session_state["authenticated"] = False
        st.experimental_rerun()
        


def main():
    # Ensure the user_database folder exists at the start
    ensure_user_database_exists()
    st.set_page_config(page_title="AgriChat", page_icon="🌾", layout="wide")
    apply_custom_css()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    menu_items = ["Home", "Login", "Register"]
    if st.session_state["authenticated"]:
        menu_items.append("Chat")
    choice = st.sidebar.selectbox("Menu", menu_items)

    if choice == "Home":
        st.subheader("Welcome to AgriChat 🌾")
    elif choice == "Login":
        show_login_page()
    elif choice == "Register":
        show_registration_page()
    elif choice == "Chat":
        if st.session_state["authenticated"]:
            chat_interface()
        else:
            st.warning("Please login to access the chat.")

if __name__ == "__main__":
    main()
