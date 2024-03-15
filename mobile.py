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

        /* Custom styles for radio buttons to make them bolder and bigger */
        .stRadio > div > label {{
            font-size: 25px; /* Increase font size */
            font-weight: bold; /* Make font bolder */
        }}

        /* Enhanced visibility for headings */
        .stHeader, .stSubheader {{
            color: #ffffff; /* White text for better contrast */
            background-color: #007BFF; /* Example background color */
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}

        /* Ensure text fields are easily readable */
        .stTextInput > div > div > input, .stPassword > div > div > input {{
            background-color: rgba(255, 255, 255, 1) !important;
            color: #000;
            border-radius: 4px;
            border: 1px solid #ced4da;
            padding: 10px;
        }}
        
        .login-highlight {{
            font-size: 24px !important;
            font-weight: bold !important;
            color: #000000; /* Black color */
            background-color: rgba(255, 255, 255, 0.5); /* Translucent white background */
            padding: 5px 10px; /* Slightly larger padding for visual appeal */
            border-radius: 5px; /* Rounded corners */
            margin: 10px 0; /* Margins to separate from surrounding content */
            display: inline-block; /* Ensure the background only surrounds the text */
        }}
        
        /* Adjusted styles for Log-In and Registration */
        .login-highlight, .registration-highlight {{
            font-size: 28px !important; /* Increased font size */
            font-weight: bold !important;
            color: #000000; /* Black color */
            background-color: rgba(255, 255, 255, 0.5); /* Translucent white background */
            padding: 5px 10px; /* Padding around the text */
            border-radius: 5px; /* Rounded corners */
            margin: 10px 0; /* Margins to separate from surrounding content */
            display: inline-block; /* Ensure the background only surrounds the text */
        }}

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
    # Use "Log-In" instead of "Login" and apply the 'login-highlight' class
    st.markdown('<div class="login-highlight">Log-In</div>', unsafe_allow_html=True)
    
    username = st.text_input("", placeholder="Enter your username", key="login_username")
    password = st.text_input("", type="password", placeholder="Enter your password", key="login_password")
    
    if st.button("Login"):
        if login_user(username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Logged in successfully!")
            st.experimental_rerun()
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
            st.experimental_rerun()
        else:
            st.error("Registration failed. Username might already exist.")




def main():
    ensure_user_database_exists()
    st.set_page_config(page_title="AgriChat", page_icon="🌾", layout="wide")
    apply_custom_css()

    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.image("background/logo.png", width=100)  # Ensure the path is correct

            # Updated CSS with minimal padding
            st.markdown("""
                <style>
                    .welcome-text, .option-text {
                        color: #000000; /* Black color */
                        background-color: rgba(255, 255, 255, 0.5); /* Translucent white background */
                        padding: 2px 5px; /* Reduced padding around the text */
                        border-radius: 5px; /* Rounded corners */
                        display: inline; /* Align highlight with text */
                        margin: 0; /* Remove default margins */
                    }
                    .welcome-text {
                        font-size:50px !important;
                        font-weight: bold !important;
                    }
                    .option-text {
                        font-size:28px !important;
                        font-weight: bold !important;
                    }
                </style>
                """, unsafe_allow_html=True)

            # Use markdown to insert styled text without additional space
            st.markdown('<div class="welcome-text">Welcome to AgriBot 🌾</div>', unsafe_allow_html=True)
            
            # Ensuring there's a break between the welcome message and the options
            st.write("")
            
            st.markdown('<div class="option-text">Choose an option:</div>', unsafe_allow_html=True)
            
            # Radio buttons without a label, as the label is now part of the styled markdown above
            form_selection = st.radio("", ["Login", "Register"], horizontal=True)

            if form_selection == "Login":
                show_login_page()
            elif form_selection == "Register":
                show_registration_page()
    else:
        chat_interface()

if __name__ == "__main__":
    main()
