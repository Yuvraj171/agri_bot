import json
import os
import time
import streamlit as st
from streamlit_chat import message
import requests
from pymongo import MongoClient

from main import save_conversation_to_file

from urllib.parse import quote_plus



def dump_json_to_mongodb(json_filepath, connection_string, db_name, collection_name):
    # Connect to MongoDB
    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]

    # Load JSON file
    with open(json_filepath, 'r') as file:
        data = json.load(file)

    # Check if data is a list of documents or a single document
    if isinstance(data, list):
        # Insert multiple documents
        collection.insert_many(data)
    else:
        # Insert a single document
        collection.insert_one(data)

    print("Data inserted successfully into MongoDB.")




def query(payload, conversation_history, language):
    history_str = " ".join([f"User: {user_msg} , Assistant: {assistant_msg}" for user_msg, assistant_msg in conversation_history])
    headers = {"Authorization": f"Bearer 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"}
    # Assume the API endpoint or model might change based on the language; adjust accordingly.
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    json_body = {
        "inputs": f"[INST] <<SYS>> Your job is to talk like a farming assistant for a farmer in {language}. Every response must sound the same. Also, remember the previous conversation {history_str} and answer accordingly <<SYS>> User: {payload} Assistant: [/INST]",
        "parameters": {"max_new_tokens": 1024, "top_p": 0.9, "temperature": 0.7}
    }
    
    response = requests.post(API_URL, headers=headers, json=json_body)
    return response.json()


def save_conversation_to_mongodb(conversation_history, connection_string, db_name, collection_name):
    # Prepare the conversation history in a dictionary format
    conversation_dict = {user_msg: bot_msg for user_msg, bot_msg in conversation_history}

    # Connect to MongoDB
    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]

    # Create a document with today's date and the conversation history
    document = {
        "date": time.strftime("%Y-%m-%d"),
        "conversations": conversation_dict
    }

    # Insert the document into the collection
    collection.insert_one(document)

    print("Conversation updated in MongoDB.")



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
    # username = quote_plus('yuvraj171')
    # password = quote_plus('Vtvg2n0K8L17I2fT')
    # connection_string = f"mongodb+srv://{username}:{password}@streamlitdb.xnixowo.mongodb.net/?retryWrites=true&w=majority&appName=streamlitDB"
    
    connection_string = 'mongodb+srv://yuvraj171:Vtvg2n0K8L17I2fT@streamlitdb.xnixowo.mongodb.net/?retryWrites=true&w=majority&appName=streamlitDB'
    json_filepath = filepath
    db_name = 'Personal'
    collection_name = 'chatbot'
    
    dump_json_to_mongodb(json_filepath, connection_string, db_name, collection_name)


def apply_custom_css():
    background_image_url = "https://images.pexels.com/photos/289334/pexels-photo-289334.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1s"  # Replace this with the URL to your image
    
    st.markdown(
        f"""
        <style>
        /* This targets the main content area */
        .stApp {{
            background-image: url({background_image_url});
            background-size: cover;
        }}
        /* This ensures sidebar's background remains solid */
        .css-1d391kg {{
            background: #fff; /* or any color you want for the sidebar background */
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def main():
    st.set_page_config(
        page_title="AgriChat",
        page_icon="🌾",
        layout="wide",
    )
    
    apply_custom_css()
    
    st.header("AgriChat 🌾")
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []

    message("Good Morning, How can i assist you today!")
    
    with st.sidebar:
        language = st.selectbox("Choose your language:", ("English", "Punjabi", "Hindi"), key="language")
        prompt = st.text_input("Enter your prompt:", key="user_prompt")

    if prompt:
        with st.spinner("Thinking..."):
            data = query(prompt, st.session_state.conversation_history, language)
            res = data[0]['generated_text'].split('[/INST]')[1]
            st.session_state.conversation_history.append((prompt, res))
            save_conversation_to_file([(prompt, res)])

    for i, (user_msg, bot_msg) in enumerate(st.session_state.conversation_history):
        message(user_msg, is_user=True, key=f"user_{i}")
        message(bot_msg, is_user=False, key=f"bot_{i}")

if __name__ == '__main__':
    main()