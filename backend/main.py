# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage

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
    history: List[Dict[str, Any]] # Frontend should send the history

class ChatResponse(BaseModel):
    response: str
    session_id: str
    history: List[Dict[str, Any]] # Send back the updated history

# LangGraph now manages state internally per run, so we don't need a server-side history store.
# However, the frontend needs to maintain and send the history for the LLM's context.

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Endpoint to chat with the calendar booking agent.
    """
    session_id = request.session_id
    user_message = request.message

    # Reconstruct message history for LangGraph
    # For this simple bot, we can just pass the latest message.
    # A more robust solution would pass the whole history.
    messages = [HumanMessage(content=user_message)]

    # --- CHANGE 3: The way we invoke and get the final response ---
    # The input dictionary must match the AgentState structure.
    inputs = {"messages": messages}
    
    # Use .invoke() for a single final response, which is simpler here.
    final_state = agent_graph.invoke(inputs, {"recursion_limit": 100})

    # The agent's final response is the last message in the state
    agent_response_message = final_state['messages'][-1]
    agent_response_text = agent_response_message.content

    # The new history includes the user's message and the bot's response
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
