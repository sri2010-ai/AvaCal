# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
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
conversation_histories: Dict[str, List[Dict[str, Any]]] = {}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    session_id = request.session_id
    user_message = request.message
    messages = [HumanMessage(content=user_message)]   
    inputs = {"messages": messages}    
    final_state = agent_graph.invoke(inputs, {"recursion_limit": 100})
    agent_response_message = final_state['messages'][-1]
    agent_response_text = agent_response_message.content
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
