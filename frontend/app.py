import streamlit as st
import requests
import uuid

# --- Configuration ---
st.set_page_config(
    page_title="Calendar Booking Bot",
    page_icon="📅",
    layout="wide"
)

# --- State Management ---
# Initialize session state variables if they don't exist
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your friendly booking assistant. How can I help you schedule an appointment today?"}]

# --- Backend API ---
# The URL for the FastAPI backend.
# For local development: "http://127.0.0.1:8000/chat"
# For Railway deployment, Streamlit and FastAPI run in different containers.
# Railway provides the backend URL via an environment variable.
# We will set this in the Railway service variables.
# For example, if your backend service is named 'backend', the URL might be
# 'https://backend.production.app/chat' or similar. We will hardcode it here
# after deploying the backend for simplicity, or ideally, read from env vars.
BACKEND_URL = "https://calendar-booking-agent-backend.up.railway.app/chat"

# --- UI Rendering ---
st.title("📅 Calendar Booking Bot")
st.caption("I can help you find available slots and book a 1-hour meeting on my calendar.")

# Display chat messages from history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User Input and Chat Logic ---
if prompt := st.chat_input("e.g., Can you book a meeting for tomorrow?"):
    # Add user message to chat history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display a thinking spinner while waiting for the backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Prepare the request payload
                payload = {
                    "session_id": st.session_state.session_id,
                    "message": prompt
                }
                
                # Send the message to the backend
                response = requests.post(BACKEND_URL, json=payload, timeout=120)
                response.raise_for_status()  # Raise an exception for bad status codes
                
                # Extract the bot's response
                bot_response = response.json().get("response")
                
                # Display the bot's response
                st.markdown(bot_response)
                
                # Add bot response to chat history
                st.session_state.messages.append({"role": "assistant", "content": bot_response})

            except requests.exceptions.RequestException as e:
                error_message = f"Sorry, I couldn't connect to my brain. Please try again later. (Error: {e})"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})