from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain.tools import tool
from langgraph.graph import StateGraph
from langgraph.types import Command
import yfinance as yf


async def agent_graph():
    workflow = StateGraph()
    workflow.add_node("chat", chat_node)
    workflow.add_node("stock_analysis", stock_analysis_node)
    
    
    from langgraph.checkpoint.memory import MemorySaver
    graph = workflow.compile(memory)
    return graph