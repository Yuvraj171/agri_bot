import streamlit as st
from transformers import pipeline
import os
import datetime

# Initialize the text generation pipeline with the Hugging Face model
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
generator = pipeline("text-generation", model=model_name)

# Define the chat history folder path
chat_history_folder = "chat_history"
# Ensure the chat history folder exists
if not os.path.exists(chat_history_folder):
    os.makedirs(chat_history_folder)

def get_todays_chat_history_file_path():
    today = datetime.date.today()
    filename = f"chat_history_{today}.txt"
    return os.path.join(chat_history_folder, filename)

def save_chat_to_history(user_input, bot_response):
    file_path = get_todays_chat_history_file_path()
    with open(file_path, "a") as file:
        file.write(f"User: {user_input}\n")
        file.write(f"Bot: {bot_response}\n\n")

def load_todays_chat_history():
    file_path = get_todays_chat_history_file_path()
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            chat_history = file.read().strip().split("\n\n")
            for exchange in chat_history:
                user_line, bot_line = exchange.split("\n")
                user_input = user_line[len("User: "):]
                bot_response = bot_line[len("Bot: "):]
                st.session_state['chat_history'].append((user_input, bot_response))

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
    load_todays_chat_history()

def generate_response(user_input):
    prompt = f"{user_input}\n\n###\n\n"
    for user_input, bot_response in reversed(st.session_state['chat_history'][-5:]):
        prompt += f"{user_input} {bot_response} "

    responses = generator(prompt, max_length=512, num_return_sequences=1, temperature=0.7, top_p=0.9, repetition_penalty=1.2)
    bot_response = responses[0]["generated_text"].strip()

    st.session_state['chat_history'].append((user_input, bot_response))
    save_chat_to_history(user_input, bot_response)

    return bot_response





def apply_custom_css():
    background_image_url = "https://www.logineko.com/wp-content/uploads/2023/10/organic-cereals-768x513.webp"
    
    st.markdown(f"""
        <style>
        /* Full page background */
        .stApp {{
            background-image: url("{background_image_url}");
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Enhancements for text input and button to stand out */
        .stTextInput>div>div>input, .stButton>button {{
            border-radius: 20px;
            padding: 10px;
            margin: 5px 0;
            background-color: #fff; /* Ensure input and button are visible */
        }}

        .stButton>button {{
            border: 1px solid #4CAF50;
            color: white;
            background-color: #4CAF50;
        }}

        /* Specific styles to make title, messages, and responses stand out */
        /* Adjustments for markdown containers to prevent overlapping */
        .stMarkdownContainer {{
            background-color: rgba(255, 255, 255, 0.9); /* Slightly transparent white for readability */
            border-radius: 15px;
            margin-bottom: 20px; /* Add space between chat messages */
        }}

        h1 {{
            background-color: rgba(255, 255, 255, 0.8); /* Slightly more transparency for the title */
            border-radius: 10px;
            padding: 10px;
            border: 1px solid #ccc;
            margin-top: 20px; /* Ensure there's space above the title */
            margin-bottom: 20px; /* Space below the title */
        }}

        /* Adjust padding and margins to ensure content is not too cramped */
        .css-1d391kg, .stTextInput, .stButton {{
            padding-top: 10px;
            padding-bottom: 10px;
            margin: 10px 0; /* Ensure spacing around input and buttons */
        }}

        /* Ensure chat area has a distinct background to differentiate from the main background */
        .stBlock {{
            background-color: rgba(255, 255, 255, 0.6); /* Lighter background for chat area */
            border-radius: 15px;
            padding: 20px;
            z-index: 100;
            margin-bottom: 20px; /* Space between chat messages and input area */
        }}

        </style>
    """, unsafe_allow_html=True)

def display_chat_history(chat_area):
    with chat_area.container():
        for user_input, bot_response in st.session_state['chat_history']:
            st.text_area("You", value=user_input, height=100, disabled=True)
            st.text_area("AgriBot", value=bot_response, height=100, disabled=True)

def main():
    apply_custom_css()
    st.title("AgriChat: Your Agricultural Assistant")
    
    chat_area = st.empty()
    
    user_input = st.text_input("Type your message here:", "", key="user_input")
    if st.button("Send") and user_input.strip():
        bot_response = generate_response(user_input.strip())
        st.session_state.user_input = ""  # Clear input after sending
        display_chat_history(chat_area)

if __name__ == "__main__":
    main()