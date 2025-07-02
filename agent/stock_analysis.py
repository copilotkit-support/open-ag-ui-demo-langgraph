from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from ag_ui.core.types import AssistantMessage, ToolMessage as ToolMessageAGUI
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import yfinance as yf
from copilotkit import CopilotKitState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
load_dotenv()
class AgentState(CopilotKitState):
    """
    This is the state of the agent.
    It is a subclass of the MessagesState class from langgraph.
    """
    tools: list
    messages: list


def convert_tool_call(tc):
    return {
        "id": tc.get("id"),
        "type": "function",
        "function": {
            "name": tc.get("name"),
            "arguments": json.dumps(tc.get("args", {}))
        }
    }

def convert_tool_call_for_model(tc):
    return {
        "id": tc.id,
        "name": tc.function.name,
        "args": json.loads(tc.function.arguments)
    }

async def chat_node(state: AgentState,config: RunnableConfig):
    # print(state)
    try:
        model = ChatOpenAI(model="gpt-4o-mini")
        tools = [t.dict() for t in state['tools']]
        messages = []
        for message in state['messages']:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(SystemMessage(content=message.content))
                case "assistant" | "ai":
                    tool_calls_converted = [convert_tool_call_for_model(tc) for tc in message.tool_calls]
                    messages.append(AIMessage(invalid_tool_calls=[], tool_calls=tool_calls_converted, type="ai", content=message.content or ""))
                case "tool":
                    # ToolMessage may require additional fields, adjust as needed
                    messages.append(ToolMessage(tool_call_id = message.tool_call_id, content=message.content))
                case _:
                    raise ValueError(f"Unsupported message role: {message.role}")
        
        response = await model.bind_tools(tools).ainvoke(messages,config=config)
        if(response.tool_calls):
            tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
            a_message = AssistantMessage( role="assistant", tool_calls=tool_calls, id=response.id)
            state['messages'].append(a_message)
        else:
            a_message = ToolMessageAGUI(content=response.content, role="tool", tool_call_id=state['messages'][-1].tool_call_id)
            state['messages'].append(a_message)
        print("hello")
    except Exception as e:
        print(e)
        return Command(
            goto=END,
        )
    return Command(
        goto=END,
    )

async def stock_analysis_node(state: AgentState,config: RunnableConfig):
    print("HERE")
    return Command(
        goto=END,
        update={"messages" : []}
    )


async def agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("chat", chat_node)
    workflow.add_node("stock_analysis", stock_analysis_node)
    
    workflow.set_entry_point("chat")
    # workflow.add_edge(START, "chat")
    workflow.add_edge("chat", "stock_analysis")
    workflow.add_edge("chat", END)
    workflow.add_edge("stock_analysis", END)
    
    # from langgraph.checkpoint.memory import MemorySaver
    # graph = workflow.compile(MemorySaver())
    graph = workflow.compile()
    return graph