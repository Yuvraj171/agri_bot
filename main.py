from dotenv import load_dotenv
import os

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
# from langchain.chat_models import ChatOpenAI
from langchain_community.llms import HuggingFaceHub



def main():
    load_dotenv()

    # Load the OpenAI API key from the environment variable
    if os.getenv("HUGGINGFACEHUB_API_TOKEN") is None or os.getenv("HUGGINGFACEHUB_API_TOKEN") == "":
        print("HUGGINGFACEHUB_API_TOKEN is not set")
        exit(1)
    else:
        print("HUGGINGFACEHUB_API_TOKEN is set")

    # llm = ChatOpenAI(temperature=0)
    llm = HuggingFaceHub(repo_id="mistralai/Mistral-7B-Instruct-v0.1", model_kwargs={"temperature":0.5, "max_length":512})
    conversation = ConversationChain(
        llm=llm, verbose=True, memory=ConversationBufferMemory())

    print("Hello, I am ChatGPT CLI!")

    while True:
        user_input = input("> ")

        ai_response = conversation.predict(input=user_input)

        print("\nAssistant:\n", ai_response, "\n")


if __name__ == '__main__':
    main()