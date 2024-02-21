import json
import os
from huggingface_hub import InferenceClient
import gradio as gr
import time
from matplotlib.colors import CSS4_COLORS

my_db = {}
client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.1")

def format_prompt(message, history):
    prompt = "<s>"
    for user_prompt, bot_response in history:
        print("history:", history)
        prompt += f"[INST] {user_prompt} [/INST]"
        prompt += f" {bot_response}</s> "
        my_db[user_prompt] = bot_response
    prompt += f"[INST] {message} [/INST]"
    return prompt

def generate(prompt, history, temperature=0.9, max_new_tokens=256, top_p=0.95, repetition_penalty=1.0):
    temperature = float(temperature)
    if temperature < 1e-2:
        temperature = 1e-2
    top_p = float(top_p)

    generate_kwargs = {
        "temperature": temperature,
        "max_new_tokens": max_new_tokens,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty,
        "do_sample": True,
        "seed": 42,
    }

    formatted_prompt = format_prompt(prompt, history)

    stream = client.text_generation(formatted_prompt, **generate_kwargs, stream=True, details=True, return_full_text=False)
    output = ""

    for response in stream:
        output += response.token.text
        yield output
    my_db[prompt] = output
    print(my_db)
    os.chdir('./chat data')
    _file_name = ""
    for i in time.ctime().split(" "):
        _file_name += i
    file_name = ""
    for i, name in enumerate(_file_name.split(":")):
        if i <= 0:
            file_name += name
        else:
            file_name += '_' + name
    print(file_name)

    json_data = json.dumps(my_db, indent=4)  # `indent` for pretty formatting (optional)

    with open(f"{file_name}.json", "w") as json_file:
        json_file.write(json_data)
    os.chdir('C:\\Users\\Yuvraj Singh\\Desktop\\agri_bot')
    return output

# Direct CSS template

# CSS string
custom_css = """
body {
    background-image: url('https://www.logineko.com/wp-content/uploads/2023/10/organic-cereals-768x513.webp');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}
/* Add other custom CSS here */
"""

gr.ChatInterface(
    fn=generate,
    chatbot=gr.Chatbot(show_label=False, show_share_button=False, show_copy_button=True, likeable=True, layout="panel"),
    title="AgriChat",
    css=custom_css  # Inject your custom CSS here
).launch(show_api=False)
