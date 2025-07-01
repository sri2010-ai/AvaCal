from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import uuid

from agent import agent_graph
from tools import TZ

app = FastAPI(
    title="Conversational Calendar Booking Agent API",
    description="An API for a LangGraph agent that can book appointments on Google Calendar.",
    version="1.0.0"
)

# CORS Middleware to allow requests from our Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

# In-memory store for conversation histories. For production, use Redis or a DB.
conversation_histories: Dict[str, List[Dict[str, Any]]] = {}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Endpoint to chat with the calendar booking agent.
    """
    session_id = request.session_id
    user_message = request.message

    # Retrieve or create conversation history
    if session_id not in conversation_histories:
        conversation_histories[session_id] = []
    
    history = conversation_histories[session_id]

    # Format the input for the LangGraph agent
    inputs = {"messages": [("human", user_message)]}

    # Invoke the agent
    response_generator = agent_graph.stream(inputs, {"recursion_limit": 100}, stream_mode="values")
    
    # The final response is the last one from the stream
    final_response = None
    for value in response_generator:
        final_response = value

    # The agent's response is in the 'messages' key, and it's the last message
    agent_response_message = final_response['messages'][-1]
    agent_response_text = agent_response_message.content

    # Update history (optional, as LangGraph state is self-contained for each call)
    # history.append({"human": user_message, "ai": agent_response_text})

    return ChatResponse(response=agent_response_text, session_id=session_id)

@app.get("/")
def read_root():
    return {"status": "Calendar Booking Agent API is running"}