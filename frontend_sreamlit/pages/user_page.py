import requests
import streamlit as st

st.title("User Page - Query Agent")

# Example API usage: Ask Agent
st.header("Ask Agent")
agent_name = st.text_input("Agent Name", value="MyBot")
user_id = st.text_input("User ID", value="user1")
question = st.text_area("Question", value="What is the name of the candidate?")

if st.button("Query Agent"):
    payload = {
        "agent_name": agent_name,
        "user_id": user_id,
        "question": question,
    }
    response = requests.post("http://0.0.0.0:5016/agent/ask_agent", json=payload)
    st.json(response.json())
