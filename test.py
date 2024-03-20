import json
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
            background-color: rgba(255, 255, 255, 1) !important; /* Ensure white background */
            color: #000; /* Text color */
            border-radius: 4px;
            border: 1px solid #ced4da;
            padding: 10px;
        }}
        
        .login-highlight, .registration-highlight {{
            font-size: 24px !important;
            font-weight: bold !important;
            color: #000000; /* Black color */
            background-color: rgba(255, 255, 255, 0.5); /* Translucent white background */
            padding: 5px 10px;
            border-radius: 5px;
            margin: 10px 0;
            display: inline-block;
        }}

        /* Custom style to ensure prompt box is white */
        /* If your app still shows a green box, it might be necessary to inspect the element
           and identify the specific CSS class or ID that requires overriding */
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

            
def chat_interface():
    st.header("AgriBot 🌾 - Chat")

    # Initialize conversation_history if it doesn't exist
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # Iterate over conversation history and display messages
    for idx, (role, msg) in enumerate(st.session_state.conversation_history):
        if role == "User":
            message(msg, is_user=True, key=f"user_{idx}")
        elif role == "Assistant":
            message(msg, is_user=False, key=f"assistant_{idx}")

    # Sidebar for choosing input type
    input_type = st.sidebar.selectbox("Choose input type:", ["Text", "Audio", "Record Audio"], key='input_type_selection_sidebar')

    # Logout button in the sidebar
    show_logout_interface()  # Call to display the logout button

    # Create some vertical space before the input box
    for _ in range(10):  # Adjust the range for more or less space
        st.write("")  # Each call adds a bit of vertical space

    with st.form(key='message_form'):
        user_input, audio_input, audio_bytes = None, None, None
        
        # Use the input_type selected from the sidebar
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



def save_chat_history(user_message, assistant_message):
    chat_data_path = os.path.join("chat_data", "chat_history.json")
    os.makedirs("chat_data", exist_ok=True)  # Ensure the directory exists

    # Load existing chat history or initialize if not present
    if os.path.exists(chat_data_path):
        with open(chat_data_path, 'r') as file:
            chat_history = json.load(file)
    else:
        chat_history = []
    
    # Append the new conversation entry and save
    chat_history.append({
        "user": user_message[1], 
        "assistant": assistant_message[1], 
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    with open(chat_data_path, 'w') as file:
        json.dump(chat_history, file)


            
def handle_user_input(input_text):
    if input_text:
        # Ensure conversation history is initialized
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []

        # Display the user's query above the prompt box, on the right side
        message(input_text, is_user=True, key=f"user_{len(st.session_state.conversation_history)}")

        # Add the new user message to the conversation history
        st.session_state.conversation_history.append(("User", input_text))
        
        # Format the history for the model
        history_str = "\n".join([f"{user}: {text}" for user, text in st.session_state.conversation_history])
        
        # Construct the payload with the formatted history
        json_body = {
            "inputs": f"Your job is to talk like a farming assistant for a farmer. Every response must sound the same. Also, remember the previous conversation:\n{history_str}\nUser: {input_text} Assistant: ",
            "parameters": {"max_new_tokens": 4096, "top_p": 0.9, "temperature": 0.7}
        }

        response = query(json_body)
        
        try:
            # Process the API response
            if isinstance(response, list) and len(response) > 0:
                assistant_response = response[0].get('generated_text', '').strip()

                # Clean up the response
                if "Assistant: " in assistant_response:
                    assistant_response = assistant_response.split("Assistant: ")[-1]
                assistant_response = assistant_response.replace("[/INST]", "").strip()

                if assistant_response:
                    # Display the assistant's response
                    message(assistant_response, key=f"assistant_{len(st.session_state.conversation_history)}")

                    # Save the assistant's response in the conversation history
                    st.session_state.conversation_history.append(("Assistant", assistant_response))
                    
                    save_chat_history(("User", input_text), ("Assistant", assistant_response))
                else:
                    st.error("No assistant response was found in the API response.")
            else:
                st.error("The response structure is not as expected.")
                print("Unexpected response structure:", response)
        except Exception as e:
            st.error("An error occurred while processing the response from the assistant.")
            st.error(str(e))
            print("Error processing response:", e)



def show_logout_interface():
    if st.sidebar.button("Logout"):
        # Log the logout activity
        log_activity(st.session_state["username"], "logout")
        del st.session_state["username"]
        st.session_state["authenticated"] = False
        st.rerun()
        

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



def main():
    ensure_user_database_exists()
    st.set_page_config(page_title="AgriBot", page_icon="🌾", layout="wide")

    if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
        # Apply background image for login and registration pages
        background_image_url = "https://ideogram.ai/api/images/direct/FnjrEUIXQUqCwRYC-BkEtg.png"
        background_style = f"""
        <style>
            .stApp {{
                background-image: url('{background_image_url}');
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
        </style>
        """
        st.markdown(background_style, unsafe_allow_html=True)

        # Login and registration interface
        page_container = st.empty()
        with page_container.container():
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                # Make sure to adjust the path to your logo image
                st.image("background/logo.png", width=100)

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

                st.markdown('<div class="welcome-text">Welcome to AgriBot 🌾</div>', unsafe_allow_html=True)
                st.write("")
                st.markdown('<div class="option-text">Choose an option:</div>', unsafe_allow_html=True)
                
                form_selection = st.radio("", ["Register", "Login"], horizontal=True)

                if form_selection == "Register":
                    show_registration_page()
                elif form_selection == "Login":
                    show_login_page()
    else:
        # For the chat interface, no specific background
        # The CSS reset for background might not be effective once the app has loaded
        chat_interface()

if __name__ == "__main__":
    main()
