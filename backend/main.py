# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
# --- CHANGE 1: Import the message types we need ---
from langchain_core.messages import HumanMessage, AIMessage

from agent import agent_graph

app = FastAPI(
    title="Conversational Calendar Booking Agent API",
    description="An API for a LangGraph agent that can book appointments on Google Calendar.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: List[Dict[str, Any]]

class ChatResponse(BaseModel):
    response: str
    session_id: str
    history: List[Dict[str, Any]]

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message

    # --- CHANGE 2: Reconstruct the full conversation history ---
    # This is the most important part. We turn the list of dictionaries
    # from the frontend back into a list of LangChain message objects.
    messages = []
    for msg in request.history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg.get("content")))
        # The first message from the assistant might not have a role in the initial state
        elif msg.get("role") == "assistant":
            messages.append(AIMessage(content=msg.get("content")))
    
    # Add the user's very latest message
    messages.append(HumanMessage(content=user_message))
    
    # The input dictionary must match the AgentState structure.
    inputs = {"messages": messages}
    
    # Invoke the agent with the full history
    final_state = agent_graph.invoke(inputs, {"recursion_limit": 100})

    # The agent's final response is the last message in the state
    agent_response_message = final_state['messages'][-1]
    agent_response_text = agent_response_message.content

    # The new history is the one we started with, plus the user's new message and the bot's final response
    new_history = request.history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": agent_response_text}
    ]

    return ChatResponse(
        response=agent_response_text,
        session_id=session_id,
        history=new_history
    )

@app.get("/")
def read_root():
    return {"status": "Calendar Booking Agent API is running"}
