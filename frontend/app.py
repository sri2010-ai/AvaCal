# frontend/app.py

import streamlit as st
import requests
import uuid
import os

# --- Configuration ---
st.set_page_config(
    page_title="Calendar Booking Bot",
    page_icon="📅",
    layout="wide"
)

# --- State Management ---
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your friendly booking assistant. How can I help you schedule an appointment today?"}]

# --- Backend API ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/chat")

# --- UI Rendering ---
st.title("📅 Calendar Booking Bot")
st.caption("I can help you find available slots and book a 1-hour meeting on my calendar.")

# Display chat messages from history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User Input and Chat Logic ---
if prompt := st.chat_input("e.g., Can you book a meeting for tomorrow?"):
    # Add user message to UI immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display a thinking spinner while waiting for the backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # --- CHANGE 4: Send the history along with the message ---
                payload = {
                    "session_id": st.session_state.session_id,
                    "message": prompt,
                    "history": st.session_state.messages[:-1] # Send history *before* the new user message
                }
                
                response = requests.post(BACKEND_URL, json=payload, timeout=120)
                response.raise_for_status()
                
                response_data = response.json()
                bot_response = response_data.get("response")
                
                # Display the bot's response
                st.markdown(bot_response)
                
                # --- CHANGE 5: Update the entire message history from the backend ---
                # The backend now manages the state, so we just update the frontend
                # We add the bot's response to our local history for display
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                # We can do a full re-render if state becomes complex, but this is fine for now.

            except requests.exceptions.RequestException as e:
                error_message = f"Sorry, I couldn't connect to my brain. Please try again later. (Error: {e})"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

    # Rerun to update the chat display cleanly, especially if history was fully replaced.
    st.rerun()
