import requests
import whisper
import tempfile
import streamlit as st
from streamlit_chat import message
from audio_recorder_streamlit import audio_recorder  # Add this import for audio recording
import json
import datetime
import os
from pymongo import MongoClient
from auth import log_activity
from styles import chat_message_styles

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
def apply_custom_css():
    st.markdown(chat_message_styles, unsafe_allow_html=True)

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

def show_logout_interface():
    if st.sidebar.button("Logout"):
        # Log the logout activity
        log_activity(st.session_state["username"], "logout")
        del st.session_state["username"]
        st.session_state["authenticated"] = False
        st.rerun()            