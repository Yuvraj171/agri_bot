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
    background_image_url = "https://ideogram.ai/api/images/direct/FnjrEUIXQUqCwRYC-BkEtg.png"
    chat_message_styles = f"""
    <style>
        .stApp {{
            background-image: url({background_image_url});
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        /* Adjust chat bubble transparency and text color */
        div[role="list"] > div:first-child {{
            background-color: rgba(255, 255, 255, 0.8) !important; /* Semi-transparent white for user message */
            color: #000; /* Dark text for readability */
        }}
        div[role="list"] > div:last-child {{
            background-color: rgba(245, 245, 245, 0.8) !important; /* Semi-transparent grey for bot message */
            color: #000; /* Dark text for readability */
        }}

        /* Ensure all text is readable */
        .stTextInput > div {{
            color: #000; /* Dark text for input boxes */
        }}

        /* Set all static text to be dark for readability */
        .stMarkdown, .stText, .stTextArea, .stSubheader, .stHeader {{
            color: #000 !important;
        }}

        /* Remove background from Streamlit's default containers */
        .css-1lcbmhc, .css-1v3fvcr, .css-1d391kg {{
            background-color: transparent !important;
        }}

        /* Additional styles can be added as needed */
    </style>
    """
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
    st.header("AgriBot 🌾 - Chat")

    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # Display the conversation history
    for idx, (user_msg, assistant_msg) in enumerate(st.session_state.conversation_history):
        message(user_msg, is_user=True, key=f"user_{idx}")
        message(assistant_msg, key=f"assistant_{idx}")

    # Create some vertical space before the input box
    for _ in range(10):  # Adjust the range for more or less space
        st.write("")  # Each call adds a bit of vertical space

    input_type = st.radio("Choose input type:", ["Text", "Audio", "Record Audio"], key='input_type_selection')

    with st.form(key='message_form'):
        user_input, audio_input, audio_bytes = None, None, None
        
        if input_type == "Text":
            user_input = st.text_input("Type your message here:", key="text_input")
        elif input_type == "Audio":
            audio_input = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg"], key="audio_uploader")
        elif input_type == "Record Audio":
            audio_bytes = audio_recorder(key="audio_recorder")
        
        submit_button = st.form_submit_button("Send")

    if submit_button:
        if input_type == "Text" and user_input:
            handle_user_input(user_input)
        elif input_type == "Audio" and audio_input:
            transcribed_text = transcribe_audio_or_use_text_input(audio_input)
            handle_user_input(transcribed_text)
        elif input_type == "Record Audio" and audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            transcribed_text = transcribe_audio_or_use_text_input(None, audio_bytes)
            handle_user_input(transcribed_text)



            

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
        

def show_login_page():
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Perform login logic
        ...

def show_registration_page():
    st.subheader("Register")
    username = st.text_input("Choose a username", key="register_username")
    password = st.text_input("Choose a password", type="password", key="register_password")
    if st.button("Create account"):
        # Perform registration logic
        ...

def main():
    ensure_user_database_exists()
    st.set_page_config(page_title="AgriChat", page_icon="🌾", layout="wide")
    apply_custom_css()

    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.image("background/logo.png", width=100)  # If you have a logo to display
            st.subheader("Welcome to AgriBot 🌾")

            # Choose between login and registration
            form_selection = st.radio("Choose an option:", ["Login", "Register"])

            if form_selection == "Login":
                show_login_page()
            elif form_selection == "Register":
                show_registration_page()
    else:
        chat_interface()

if __name__ == "__main__":
    main()