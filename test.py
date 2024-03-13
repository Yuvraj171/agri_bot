import os
import time
import streamlit as st
from streamlit_chat import message
import requests
import whisper
import tempfile
from audio_recorder_streamlit import audio_recorder  # Add this import for audio recording
from pymongo import MongoClient
import datetime

from main import show_login_page, show_registration_page

# MongoDB connection string. Update "localhost" with your MongoDB host if necessary
client = MongoClient("mongodb://localhost:27017/")
# Select your database
db = client["agri_chat_db"]

def ensure_user_database_exists():
    database_path = "user_database"
    os.makedirs(database_path, exist_ok=True)

def query(payload):
    history_str = " ".join([f"User: {user_msg} , Assistant: {assistant_msg}" for user_msg, assistant_msg in st.session_state.conversation_history])
    headers = {"Authorization":f"Bearer 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"}
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    json_body = {
        "inputs": f"[INST] <<SYS>> Your job is to talk like a farming assistant for a farmer. Every response must sound the same. Also, remember the previous conversation {history_str} and answer accordingly <<SYS>> User: {payload} Assistant: [/INST]",
        "parameters": {"max_new_tokens": 4096, "top_p": 0.9, "temperature": 0.7}
    }
    
    response = requests.post(API_URL, headers=headers, json=json_body)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get a valid response: Status code {response.status_code}, Response text: {response.text}")
        return {"error": f"API request failed with status code {response.status_code}"}

def apply_custom_css():
    background_image_url = "https://images.pexels.com/photos/289334/pexels-photo-289334.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"
    chat_message_styles = """
    <style>
        .stApp {
            background-image: url(%s);
            background-size: cover;
        }
        .stChatBubble {
            background-color: rgba(255, 255, 255, 0.8) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(0, 0, 0, 0.1) !important;
            padding: 10px 20px !important;
            max-width: fit-content !important;
            margin: 10px !important;
        }
        .stMarkdown {
            background-color: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
        }
    </style>
    """ % background_image_url
    st.markdown(chat_message_styles, unsafe_allow_html=True)

def transcribe_audio(audio_file):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file, fp16=False)
    return result["text"]

def transcribe_audio_or_use_text_input(audio_file, text_input=None):
    if audio_file:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_audio:
            tmp_audio.write(audio_file.read())
            tmp_audio_path = tmp_audio.name
        return transcribe_audio(tmp_audio_path)
    else:
        return text_input

def register_user(username, password):
    users_collection = db["users"]
    if users_collection.find_one({"username": username}):
        return False  # User already exists
    else:
        users_collection.insert_one({"username": username, "password": password})
        return True

def login_user(username, password):
    users_collection = db["users"]
    user = users_collection.find_one({"username": username, "password": password})
    if user:
        log_activity(username, "login")
        return True
    else:
        return False

def log_activity(username, activity_type):
    activities_collection = db["activities"]
    current_time = datetime.datetime.now()
    activities_collection.insert_one({"username": username, "activity_type": activity_type, "timestamp": current_time})


            
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
