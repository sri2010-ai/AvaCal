# backend/agent.py

import os
from typing import TypedDict, Annotated, List
from operator import itemgetter
from datetime import datetime # Import datetime here
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
# THIS IS THE KEY CHANGE
from langgraph.prebuilt import ToolNode
from tools import check_availability, create_appointment, TZ # Import TZ from tools

# Load API Key from .env for local dev
from dotenv import load_dotenv
load_dotenv()

# 1. Define the state for our graph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], itemgetter("messages")]

# 2. Setup the tools
tools = [check_availability, create_appointment]

# THIS IS THE NEW, SIMPLER WAY TO CREATE THE TOOL NODE
tool_node = ToolNode(tools)

# Use Gemini 1.5 Flash - it's fast and supports tool calling well
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
model_with_tools = model.bind_tools(tools)

# 3. Define the nodes of the graph
# The agent_node is defined later with the full prompt chain

# 4. Define the conditional edge logic
def should_continue(state):
    """Determines whether to continue with another tool call or end."""
    last_message = state["messages"][-1]
    # If the LLM returned a message with no tool calls, we are done
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "end"
    # Otherwise, we continue and call the tools
    return "continue"

# 5. Build and compile the graph
def build_agent_graph():
    graph = StateGraph(AgentState)

    # The system prompt is crucial for guiding the agent's behavior
    system_prompt = """You are a helpful and friendly assistant for booking appointments.
    Your goal is to help the user book a 1-hour appointment in the connected Google Calendar.

    - Be conversational. Start by greeting the user and asking how you can help.
    - When a user wants to book, first check for availability using the `check_availability` tool. You must know the exact date (YYYY-MM-DD) to check. If the user gives a vague date like "next Tuesday", figure out the exact date based on today's date, which is {today}.
    - After checking, present the available slots to the user.
    - Once the user chooses a time, ask them for a summary or title for the appointment (e.g., "Dental Check-up", "Project Meeting").
    - To book the appointment using the `create_appointment` tool, you MUST have the exact start time in ISO 8601 format (e.g., '2024-07-30T14:00:00-07:00') and the summary. You need to construct the full ISO string from the date and the user's chosen time.
    - If any information is missing, ask the user for it.
    - Once the appointment is successfully booked, confirm this with the user.
    - If you encounter an error, inform the user clearly and politely.
    """
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    runnable_agent = prompt_template | model_with_tools
    
    def agent_node(state):
        today = datetime.now(TZ).strftime("%Y-%m-%d")
        response = runnable_agent.invoke({"messages": state["messages"], "today": today})
        # The agent returns a single message, but the state expects a list of messages.
        # We append the new message to the existing ones.
        return {"messages": [response]}
    
    # Define the nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node) # Use the new ToolNode directly

    # Define the edges
    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END
        }
    )
    
    graph.add_edge("tools", "agent")

    return graph.compile()

# Pre-compile the graph for efficiency
agent_graph = build_agent_graph()
