#importing libraries
#this is agri bot

import json
import os
from huggingface_hub import InferenceClient
import gradio as gr
import time
from matplotlib.colors import CSS4_COLORS

my_db ={}
client = InferenceClient(
    "mistralai/Mistral-7B-Instruct-v0.1"
)
    

def format_prompt(message, history):
    prompt = "<s>"
    for user_prompt, bot_response in history:
        print("history:",history)
        prompt += f"[INST] {user_prompt} [/INST]"
        prompt += f" {bot_response}</s> "
        my_db[user_prompt]=bot_response
    prompt += f"[INST] {message} [/INST]"
    
    return prompt

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


# additional_inputs=[
#     gr.Slider(
#         label="Temperature",
#         value=0.9,
#         minimum=0.0,
#         maximum=1.0,
#         step=0.05,
#         interactive=True,
#         info="Higher values produce more diverse outputs",
#     ),
#     gr.Slider(
#         label="Max new tokens",
#         value=256,
#         minimum=0,
#         maximum=1048,
#         step=64,
#         interactive=True,
#         info="The maximum numbers of new tokens",
#     ),
#     gr.Slider(
#         label="Top-p (nucleus sampling)",
#         value=0.90,
#         minimum=0.0,
#         maximum=1,
#         step=0.05,
#         interactive=True,
#         info="Higher values sample more low-probability tokens",
#     ),
#     gr.Slider(
#         label="Repetition penalty",
#         value=1.2,
#         minimum=1.0,
#         maximum=2.0,
#         step=0.05,
#         interactive=True,
#         info="Penalize repeated tokens",
#     )
# ]


gr.ChatInterface(
    fn=generate,
    chatbot=gr.Chatbot(show_label=False, show_share_button=False, show_copy_button=True, likeable=True, layout="panel"),
    # additional_inputs=additional_inputs,
    title="""AgriChat""",
    css= "style.css"
).launch(show_api=False)
