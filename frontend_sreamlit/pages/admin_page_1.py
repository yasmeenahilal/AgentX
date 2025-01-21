import requests
import streamlit as st

st.title("Admin Page 1 - Index Management")

# Example API usage: Insert Data to Index
st.header("Insert Data to Index")

# Select the VectorDB
vectordb = st.selectbox("Select VectorDB", ["Pinecone", "FAISS"])

# Common inputs
user_id = st.text_input("User ID")
index_name = st.text_input("Index Name")
file = st.file_uploader("Upload File")
embedding = st.text_input("Embedding", value="sentence-transformers/all-mpnet-base-v2")

# Conditional inputs based on VectorDB selection
if vectordb == "Pinecone":
    st.subheader("Pinecone Configuration")
    pinecone_api_key = st.text_input("Pinecone API Key", type="password")
    pinecone_environment = st.text_input("Pinecone Environment")
elif vectordb == "FAISS":
    st.subheader("FAISS Configuration")
    faiss_file_path = st.text_input("FAISS File Path")

# Button to insert data
if st.button("Insert Data"):
    if user_id and index_name and file:
        # Prepare common payload
        files = {"file": file.getvalue()}
        payload = {
            "user_id": user_id,
            "index_name": index_name,
            "embedding": embedding,
            "vectordb": vectordb,
        }

        # Add VectorDB-specific data to payload
        if vectordb == "Pinecone":
            if not pinecone_api_key or not pinecone_environment:
                st.error("Pinecone API Key and Environment are required!")
            else:
                payload.update(
                    {
                        "pinecone_api_key": pinecone_api_key,
                        "pinecone_environment": pinecone_environment,
                    }
                )
        elif vectordb == "FAISS":

            # if not faiss_file_path:
            #     st.error("FAISS File Path is required!")
            # else:
            payload.update(
                {
                    "faiss_file_path": faiss_file_path,
                }
            )

        # Send the request
        try:
            response = requests.post(
                "http://0.0.0.0:5016/index/insert_data_to_index",
                data=payload,
                files=files,
            )
            if response.status_code == 200:
                st.success("Data inserted successfully!")
                st.json(response.json())
            else:
                st.error(f"Error: {response.status_code}")
                st.json(response.json())
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("All fields are required!")
