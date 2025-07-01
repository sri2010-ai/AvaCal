# Conversational Google Calendar Booking Agent

A conversational AI agent built with Python, FastAPI, LangGraph, and Streamlit that assists users in booking appointments on a Google Calendar through a natural chat interface.

**Live Demo URL:** [https://calendar-booking-agent-frontend.up.railway.app/](https://calendar-booking-agent-frontend.up.railway.app/)

*(Note: The live demo is hosted on a free tier and may take a moment to wake up on the first visit.)*

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Setup & Installation](#-setup--installation)
- [Running Locally](#-running-locally)
- [Deployment](#-deployment)

---

## ✨ Features

- **Natural Conversation:** Engage in a back-and-forth dialogue to determine user needs.
- **Calendar Availability Check:** The agent can check a Google Calendar for open 1-hour slots within working hours (9 AM - 5 PM).
- **Intelligent Tool Use:** Utilizes the LangGraph framework and LLM function calling to decide when to check availability vs. when to book an appointment.
- **Appointment Booking:** Creates events directly on the connected Google Calendar.
- **Confirmation:** Confirms the successful booking with the user.
- **Simple Web Interface:** A clean and user-friendly chat interface built with Streamlit.

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI
- **Agent Framework:** LangGraph
- **LLM:** Google Gemini 1.5 Flash (via API)
- **Frontend:** Streamlit
- **Database/State:** In-memory dictionary (can be swapped for Redis)
- **Deployment:** Railway
- **Google Integration:** `google-api-python-client` with a Service Account

---

## 🏗️ Architecture

The system follows a simple frontend-backend architecture:

1.  **Frontend (Streamlit):** The user interacts with the chat UI. It sends user messages to the FastAPI backend.
2.  **Backend (FastAPI):** An API endpoint (`/chat`) receives the message.
3.  **Agent (LangGraph):** The backend invokes the LangGraph agent with the current conversation history.
4.  **LLM (Gemini):** The agent's brain. It processes the conversation and decides whether to respond directly or use a tool.
5.  **Tools (Python Functions):** The agent can call two tools:
    - `check_availability`: Connects to the Google Calendar API to find open slots.
    - `create_appointment`: Connects to the Google Calendar API to create a new event.
6.  **Google Calendar:** The ultimate source of truth for availability and the destination for new bookings.

---

## 🚀 Setup & Installation

Follow these steps to set up the project on your local machine.

### Prerequisites

- Python 3.9+
- Git
- A Google Cloud Platform account

### 1. Clone the Repository

```bash
git clone https://github.com/phat-tran/calendar-booking-agent.git
cd calendar-booking-agent
```

### 2. Google Calendar & Service Account Setup

This is the most critical part of the setup.

1.  **Enable API:** In the [Google Cloud Console](https://console.cloud.google.com/), create a new project and enable the **Google Calendar API**.
2.  **Create Service Account:**
    - Navigate to `APIs & Services > Credentials`.
    - Click `Create Credentials > Service account`.
    - Give it a name (e.g., `calendar-bot`) and the `Editor` role.
3.  **Generate JSON Key:**
    - After creating the service account, go to its "Keys" tab.
    - Click `Add Key > Create new key` and select **JSON**.
    - A file will be downloaded. **Rename this file to `service_account.json` and place it in the `backend/` directory.**
4.  **Share Your Calendar:**
    - Open your `service_account.json` file and copy the `client_email` value.
    - Go to your Google Calendar's "Settings and sharing".
    - Under "Share with specific people," add the `client_email` and give it **"Make changes to events"** permissions.
    - Copy the **Calendar ID** from the "Integrate calendar" section.

### 3. Get LLM API Key

1.  Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Create and copy your API key.

### 4. Configure Environment Variables

Create a file named `.env` inside the `backend/` directory. **This file is git-ignored for security.**

```
# backend/.env

GOOGLE_API_KEY="your_gemini_api_key_here"
CALENDAR_ID="your_google_calendar_id_here"
```

### 5. Install Dependencies

You'll need to install requirements for both the backend and frontend.

```bash
# Install backend dependencies
python -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
deactivate

# Install frontend dependencies
python -m venv frontend/venv
source frontend/venv/bin/activate
pip install -r frontend/requirements.txt
deactivate
```

---

## 🏃 Running Locally

Run the backend and frontend servers in separate terminal windows.

**Terminal 1: Start the Backend**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

The backend will be running at `http://127.0.0.1:8000`.

**Terminal 2: Start the Frontend**

First, ensure the `BACKEND_URL` in `frontend/app.py` is pointing to your local server: `http://127.0.0.1:8000/chat`.

```bash
cd frontend
source venv/bin/activate
streamlit run app.py
```

The frontend will be running at `http://localhost:8501`. Open this URL in your browser to start chatting with the bot.

---

## ☁️ Deployment

This project is deployed on [Railway](https://railway.app) using a monorepo setup.

1.  **Backend Service (`backend` directory):**
    - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
    - **Environment Variables:**
        - `GOOGLE_API_KEY`
        - `CALENDAR_ID`
        - `GOOGLE_SERVICE_ACCOUNT_JSON` (Paste the entire content of the JSON file here)

2.  **Frontend Service (`frontend` directory):**
    - **Start Command:** `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
    - Update the `BACKEND_URL` in `frontend/app.py` to the public URL of your deployed backend service.