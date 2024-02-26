import json
import os
import time
import streamlit as st
from streamlit_chat import message
import requests

def query(payload):
    history_str = " ".join([f"User: {user_msg} , Assistant: {assistant_msg}" for user_msg, assistant_msg in st.session_state.conversation_history])
    headers = {"Authorization": f"Bearer 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"}
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    
    json_body = {
        "inputs": f"[INST] <<SYS>> Your job is to talk like a farming assistant for a farmer. Every response must sound like the same. Also, do remember the previous conversation {history_str} and answer accordingly <<SYS>> User: {payload} Assistant: [/INST]",
        "parameters": {"max_new_tokens": 128, "top_p": 0.9, "temperature": 0.7}
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

def main():
    st.set_page_config(
        page_title="AgriChat",
        page_icon="🌾",  # Changed to an ear of rice emoji
        layout="wide",
    )
    st.header("AgriChat 🌾")
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    message("Good Morning, How can i assist you today!")
    with st.sidebar:
        prompt = st.text_input("Enter your prompt:", key="user_prompt")
    if prompt:
        with st.spinner("Thinking..."):
            data = query(prompt)
            res = data[0]['generated_text'].split('[/INST]')[1]
            st.session_state.conversation_history.append((prompt, res))
        
        # Save or update the conversation history in a JSON file
        save_conversation_to_file([(prompt, res)])

    for i, (user_msg, bot_msg) in enumerate(st.session_state.conversation_history):
        message(user_msg, is_user=True, key=f"user_{i}")
        message(bot_msg, is_user=False, key=f"bot_{i}")

if __name__ == '__main__':
    main()
