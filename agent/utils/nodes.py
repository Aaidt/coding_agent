from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import ToolNode
from .state import AgentState
from .tools import tools

tool_node = ToolNode(tools=tools)

def make_agent_node(model):
    def agent_node(state: AgentState) -> AgentState:
        model_with_tools = model.bind_tools(tools)

        response = model_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    return agent_node