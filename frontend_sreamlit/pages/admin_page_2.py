import requests
import streamlit as st

st.title("Admin Page 2 - Agent Management")

# Example API usage: Create Agent
st.header("Create Agent")
agent_name = st.text_input("Agent Name", value="MyBot")
user_id = st.text_input("User ID", value="user1")
index_name = st.text_input("Index Name", value="thursday")
llm_provider = st.text_input("LLM Provider", value="huggingface")
llm_model_name = st.text_input(
    "LLM Model Name", value="mistralai/Mixtral-8x7B-Instruct-v0.1"
)
llm_api_key = st.text_input("LLM API Key", value="pass")
prompt_template = st.text_input(
    "Propmt",
    value="You are a knowledgeable assistant trained to provide answers based on accurate, reliable, and factual information. If you do not have enough data to answer a question, do not invent information or provide a speculative response. Instead, acknowledge the lack of sufficient data and refrain from answering. Only answer questions that you can confirm with the provided data. If the query is ambiguous or outside the scope of the data, state 'I do not have enough information to answer that.",
)


if st.button("Create Agent"):
    payload = {
        "agent_name": agent_name,
        "user_id": user_id,
        "index_name": index_name,
        "llm_provider": llm_provider,
        "llm_model_name": llm_model_name,
        "llm_api_key": llm_api_key,
        "prompt_template": prompt_template,
    }
    response = requests.post("http://0.0.0.0:5016/agent/create_agent", json=payload)
    st.json(response.json())
