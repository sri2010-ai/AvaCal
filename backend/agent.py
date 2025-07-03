import os
from typing import TypedDict, Annotated, List
from datetime import datetime
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from tools import check_availability, create_appointment, TZ
from dotenv import load_dotenv
load_dotenv()
def a_plus_b(a, b):
    return a + b

class AgentState(TypedDict):
    messages: Annotated[list, a_plus_b]

tools = [check_availability, create_appointment]
tool_node = ToolNode(tools)
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
model_with_tools = model.bind_tools(tools)

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return "end"
    return "continue"

def agent_node(state: AgentState):
    today = datetime.now(TZ).strftime("%Y-%m-%d")
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
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ]) 
    chain = prompt | model_with_tools
    response = chain.invoke({
        "messages": state["messages"], 
        "today": today
    })
    
    return {"messages": [response]}
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", tool_node)
graph_builder.set_entry_point("agent")
graph_builder.add_conditional_edges(
    "agent",
    should_continue,
    {"continue": "tools", "end": END}
)
graph_builder.add_edge("tools", "agent")

agent_graph = graph_builder.compile()
