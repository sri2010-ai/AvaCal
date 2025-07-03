import streamlit as st
import requests
import uuid
import os
st.set_page_config(
    page_title="Calendar Booking Bot",
    page_icon="📅",
    layout="wide"
)
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your friendly booking assistant. How can I help you schedule an appointment today?"}]

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/chat")
st.title("📅 Calendar Booking Bot")
st.caption("I can help you find available slots and book a 1-hour meeting on my calendar.")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("e.g., Can you book a meeting for tomorrow?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                payload = {
                    "session_id": st.session_state.session_id,
                    "message": prompt,
                    "history": st.session_state.messages[:-1] 
                }           
                response = requests.post(BACKEND_URL, json=payload, timeout=120)
                response.raise_for_status()    
                response_data = response.json()
                bot_response = response_data.get("response")
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            except requests.exceptions.RequestException as e:
                error_message = f"Sorry, I couldn't connect to my brain. Please try again later. (Error: {e})"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"An unexpected error occurred: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
    st.rerun()
