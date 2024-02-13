import streamlit as st
from hugchat import hugchat
from hugchat.login import Login
import json
import os
from huggingface_hub import InferenceClient
import time


my_db ={}
client = InferenceClient(
    "mistralai/Mistral-7B-Instruct-v0.1")

#App Title
st.set_page_config(page_title="🤗💬 AgriChat")

#Hugging face credentials
with st.sidebar:
    st.title('🤗💬 AgriChat')
    if ('EMAIL' in st.secrets) and ('PASS' in st.secrets):
        st.success('HuggingFace Login credentials already provided!', icon='✅')
        hf_email = st.secrets['EMAIL']
        hf_pass = st.secrets['PASS']
    else:
        hf_email = st.text_input('Enter E-mail:', type='password')
        hf_pass = st.text_input('Enter password:', type='password')
        if not (hf_email and hf_pass):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')       

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I help you?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
# Function for generating LLM response
def generate_response(prompt_input, email, passwd):
    # Hugging Face Login
    sign = Login(email, passwd)
    cookies = sign.login()
    # Create ChatBot                        
    chatbot = hugchat.ChatBot(cookies=cookies.get_dict())
    return chatbot.chat(prompt_input)
             


#Defining Prompt

def format_prompt(message, history):
    
    prompt = "<s>"
    for user_prompt, bot_response in history:
        print("history:",history)
        prompt += f"[INST] {user_prompt} [/INST]"
        prompt += f" {bot_response}</s> "
        my_db[user_prompt]=bot_response
    prompt += f"[INST] {message} [/INST]"
    
    return prompt
if prompt := st.chat_input(disabled=not (hf_email and hf_pass)):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)


# User-provided prompt
if prompt := st.chat_input(key="user_input1", disabled=not (hf_email and hf_pass)):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)  

# User-provided prompt (second instance)
if prompt := st.chat_input(key="user_input2", disabled=not (hf_email and hf_pass)):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt, hf_email, hf_pass) 
            st.write(response) 
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)

#generating Prompt

def generate(
    prompt, history, temperature=0.9, max_new_tokens=256, top_p=0.95, repetition_penalty=1.0,
):
    temperature = float(temperature)
    if temperature < 1e-2:
        temperature = 1e-2
    top_p = float(top_p)

    generate_kwargs = dict(
        temperature=temperature,
        max_new_tokens=max_new_tokens,
        top_p=top_p,
        repetition_penalty=repetition_penalty,
        do_sample=True,
        seed=42,
    )

    formatted_prompt = format_prompt(prompt, history)

    stream = client.text_generation(formatted_prompt, **generate_kwargs, stream=True, details=True, return_full_text=False)
    output = ""

    for response in stream:
        output += response.token.text
        yield output
    my_db[prompt]=output
    print(my_db)
    os.chdir('./chat data')
    _file_name=""
    for  i in time.ctime().split(" "):
        _file_name += i
    file_name =""
    for i,name in enumerate(_file_name.split(":")):
        if i<=0:
            file_name+=name
        else:
            file_name+='_'+name
    print(file_name)

    json_data = json.dumps(my_db, indent=4)  # `indent` for pretty formatting (optional)

    with open(f"{file_name}.json", "w") as json_file:
        json_file.write(json_data)
    os.chdir(r'C:\Users\Yuvraj\Desktop\AgriChat2')
    return output 

additional_inputs=[
    st.slider(
        label="Temperature",
        value=0.9,
        min_value=0.0,  # Make sure this is a float
        max_value=1.0,
        step=0.05,      # Make sure this is a float
        format="%.2f",  # Format to two decimal places
        help="Higher values produce more diverse outputs",
    ),
    st.slider(
        label="Max new tokens",
        value=256,
        min_value=0,    # Make sure this is an integer
        max_value=1048, # Make sure this is an integer
        step=64,        # Make sure this is an integer
        help="The maximum numbers of new tokens",
    ),
    st.slider(
        label="Top-p (nucleus sampling)",
        value=0.90,
        min_value=0.0,
        max_value=1.0,
        step=0.05,
        help="Higher values sample more low-probability tokens",
    ),
    st.slider(
        label="Repetition penalty",
        value=1.2,
        min_value=1.0,
        max_value=2.0,
        step=0.05,
        help="Penalize repeated tokens",
    )
]
