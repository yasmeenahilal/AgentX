# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page


# # Authentication (Mock Example)
# def authenticate(username, password):
#     if username == "admin" and password == "admin123":
#         return "admin"
#     elif username == "user" and password == "user123":
#         return "user"
#     else:
#         return None


# # Login Page
# st.title("Login Page")

# username = st.text_input("Username")
# password = st.text_input("Password", type="password")

# if st.button("Login"):
#     role = authenticate(username, password)
#     if role == "admin":
#         switch_page("admin_page_1")
#     elif role == "user":
#         switch_page("user_page")
#     else:
#         st.error("Invalid credentials!")
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

# Mock storage for users (in a real application, this would be a database)
users_db = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}

# Authentication (Mock Example)
def authenticate(username, password):
    if username in users_db and users_db[username]["password"] == password:
        return users_db[username]["role"]
    return None

# Signup (Mock Example)
def signup(username, password, role):
    if username in users_db:
        return False  # User already exists
    else:
        users_db[username] = {"password": password, "role": role}
        return True

# Login Page
st.title("Login Page")

# Login or Signup Option
option = st.radio("Select an option", ("Login", "Signup"))

if option == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = authenticate(username, password)
        if role == "admin":
            switch_page("admin_page_1")
        elif role == "user":
            switch_page("user_page")
        else:
            st.error("Invalid credentials!")

elif option == "Signup":
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    role = st.selectbox("Select role", ["user", "admin"])

    if st.button("Sign Up"):
        if signup(new_username, new_password, role):
            st.success("Account created successfully! You can now log in.")
        else:
            st.error("Username already exists. Please choose a different one.")
