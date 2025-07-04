import os
from typing import TypedDict, Annotated, Sequence
from datetime import datetime
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from tools import check_availability, create_appointment, TZ

# Load API Key from .env for local dev
from dotenv import load_dotenv
load_dotenv()

# --- State Management ---
# The reducer function tells LangGraph how to add new messages to the existing list.
def add_messages(left: list, right: list) -> list:
    """Adds messages to the state. Ensures the new messages are always at the end."""
    return left + right

# 1. Define the state for our graph.
# The `Annotated` type hint with `add_messages` is the key to managing the conversation history.
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# 2. Setup the tools and the LLM
tools = [check_availability, create_appointment]
tool_node = ToolNode(tools)

model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, convert_system_message_to_human=True)
model_with_tools = model.bind_tools(tools)


# 3. Define the nodes of the graph
# The agent_node is now defined within the build_agent_graph function to include the prompt.

# 4. Define the conditional edge logic
def should_continue(state: AgentState) -> str:
    """Determines whether to continue with another tool call or end."""
    last_message = state["messages"][-1]
    # If the model did not make a tool call, then we end the process.
    if not last_message.tool_calls:
        return "end"
    # Otherwise, we continue and call the tools.
    return "continue"

# 5. Build and compile the graph
def build_agent_graph():
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
    
    # This is our main agent node. It invokes the model with the current state.
    def agent_node_with_prompt(state: AgentState):
        today = datetime.now(TZ).strftime("%Y-%m-%d")
        # Chain the prompt with the model
        runnable_agent = prompt_template | model_with_tools
        # Invoke the chain
        response = runnable_agent.invoke({
            "messages": state["messages"],
            "today": today
        })
        return {"messages": [response]}
        
    graph = StateGraph(AgentState)

    # We are defining the agent_node_with_prompt as the 'agent' node
    graph.add_node("agent", agent_node_with_prompt)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")

    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )
    graph.add_edge("tools", "agent")

    return graph.compile()

# Pre-compile the graph for efficiency
agent_graph = build_agent_graph()
