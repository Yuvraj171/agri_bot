import json
import os
import time
import streamlit as st
from streamlit_chat import message
import requests
import whisper
import tempfile
from user_manage import log_activity, register_user, login_user




def query(payload):
    history_str = " ".join([f"User: {user_msg} , Assistant: {assistant_msg}" for user_msg, assistant_msg in st.session_state.conversation_history])
    headers = {"Authorization": f"Bearer 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"}
    # Assume the API endpoint or model might change based on the language; adjust accordingly.~
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    json_body = {
        "inputs": f"[INST] <<SYS>> Your job is to talk like a farming assistant for a farmer. Every response must sound the same. Also, remember the previous conversation {history_str} and answer accordingly <<SYS>> User: {payload} Assistant: [/INST]",
        "parameters": {"max_new_tokens": 1024, "top_p": 0.9, "temperature": 0.7}
    }
    
    response = requests.post(API_URL, headers=headers, json=json_body)
    return response.json()


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
    background_image_url = "https://images.pexels.com/photos/289334/pexels-photo-289334.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1s"
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url({background_image_url});
            background-size: cover;
        }}
        .css-1d391kg {{
            background: #fff;
        }}
        </style>
        """, unsafe_allow_html=True)


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
            
            
def chat_interface():
    st.header("AgriChat 🌾 - Chat")

    # Check for existing conversation history in the session state
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    # Input options for the user
    input_type = st.radio("Choose input type:", ["Text", "Audio"])

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
