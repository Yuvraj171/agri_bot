import json
import os
from huggingface_hub import InferenceClient
import time
import streamlit as st
from transformers import pipeline


my_db ={}
client = InferenceClient(
    "mistralai/Mistral-7B-Instruct-v0.1"
)

# Initialize the generator only once to avoid reloading the model on each interaction
if 'generator' not in st.session_state:
    st.session_state['generator'] = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.1")

# Initialize an empty chat history if it doesn't exist in session state
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

chat_history_folder = "chat_history"

# Ensure the chat history folder exists
if not os.path.exists(chat_history_folder):
    os.makedirs(chat_history_folder)

def format_prompt(message):
    prompt = "<s>"
    for user_prompt, bot_response in st.session_state['chat_history']:
        prompt += f"[INST] {user_prompt} [/INST]"
        prompt += f" {bot_response}</s> "
    prompt += f"[INST] {message} [/INST]"
    return prompt

def generate(prompt, temperature=0.9, max_new_tokens=256, top_p=0.95, repetition_penalty=1.0):
    formatted_prompt = format_prompt(prompt)
    output = st.session_state['generator'](formatted_prompt, max_length=100)[0]["generated_text"]
    # Append the latest interaction to the chat history
    st.session_state['chat_history'].append((prompt, output))
    
    # Optionally, save conversation history to a file periodically or based on a trigger
    return output

def main():
    st.title("AgriChat: Your Agricultural Assistant")
    st.markdown("---")
    st.subheader("Talk to AgriBot")
    
    user_input = st.text_input("You:", "")
    if st.button("Send"):
        if user_input.strip() != "":
            bot_response = generate(user_input)
            st.session_state['chat_history'].append(("You:", user_input))
            st.session_state['chat_history'].append(("AgriBot:", bot_response))
    
    st.markdown("---")
    st.subheader("Conversation History")
    # Display chat history
    for user_prompt, bot_response in st.session_state['chat_history']:
        st.text_area(user_prompt, bot_response, height=100)

if __name__ == "__main__":
    main()
