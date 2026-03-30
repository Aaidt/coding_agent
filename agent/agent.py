import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI  

from .utils.state import AgentState
from .utils.nodes import make_agent_node, tool_node
from .utils.tools import tools

load_dotenv()

model = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="nvidia/nemotron-3-super-120b-a12b:free",    
    temperature=0.2
)

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


graph = StateGraph(AgentState)

graph.add_node("agent", make_agent_node(model))
graph.add_node("tools", tool_node)

graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    should_continue,
    ["tools", END]
)
graph.add_edge("tools", "agent")


app = graph.compile()