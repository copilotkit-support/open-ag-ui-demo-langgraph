from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from ag_ui.core.types import AssistantMessage, ToolMessage as ToolMessageAGUI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import yfinance as yf
from copilotkit import CopilotKitState
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import json
import yfinance as yf

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
    
def get_stock_price_tool(tickers: list[str]) -> str:
    try:
        tickers_list = json.loads(tickers)['tickers']
        tikers = [yf.Ticker(ticker) for ticker in tickers_list]
        results = []
        for ticker_obj, symbol in zip(tikers, tickers_list):
            hist = ticker_obj.history(period="1d")
            info = ticker_obj.info
            if not hist.empty:
                price = hist["Close"].iloc[0]
            else:
                price = None
            company_name = info.get("longName", "N/A")
            revenue = info.get("totalRevenue", "N/A")
            results.append({
                "ticker": symbol,
                "price": price,
                "company_name": company_name,
                "revenue": revenue
            })
        return {"results": results}
    except Exception as e:
        print(e)
        return f"Error: {e}"
    

get_stock_price = {
    "name": "get_stock_price",
    "description": "Get the stock prices of Respective ticker symbols.",
    "parameters": {
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "A stock ticker symbol, e.g. 'AAPL', 'GOOGL'."
                },
                "description": "A list of stock ticker symbols, e.g. ['AAPL', 'GOOGL']."
            }
        },
        "required": ["tickers"]
    }
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
                    tool_calls_converted = [convert_tool_call_for_model(tc) for tc in message.tool_calls or []]
                    messages.append(AIMessage(invalid_tool_calls=[], tool_calls=tool_calls_converted, type="ai", content=message.content or ""))
                case "tool":
                    # ToolMessage may require additional fields, adjust as needed
                    messages.append(ToolMessage(tool_call_id = message.tool_call_id, content=message.content))
                case _:
                    raise ValueError(f"Unsupported message role: {message.role}")
        
        response = await model.bind_tools([get_stock_price,*tools]).ainvoke(messages,config=config)
        if(response.tool_calls):
            if(('stock' in response.tool_calls[0]['name'])):
                tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
                a_message = AssistantMessage( role="assistant", tool_calls=tool_calls, id=response.id)
                state['messages'].append(a_message)
                return Command(
                    goto="stock_analysis",
                )
            else:
                tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
                a_message = AssistantMessage( role="assistant", tool_calls=tool_calls, id=response.id)
                state['messages'].append(a_message)
        else:
            a_message = AssistantMessage(id=response.id,content=response.content,role="assistant")
            state['messages'].append(a_message)
        print("hello")
    except Exception as e:
        print(e)
        return Command(
            goto="end",
        )
    return Command(
        goto="end",
    )

async def stock_analysis_node(state: AgentState,config: RunnableConfig):
    
    print("inside stock analysis node")
    model = ChatOpenAI(model="gpt-4o-mini")
    tools = [t.dict() for t in state['tools']]
    
    if(state['messages'][-1].tool_calls and state['messages'][-1].tool_calls[0].function.name == "get_stock_price"):
        a = get_stock_price_tool(state['messages'][-1].tool_calls[0].function.arguments)
        messages = []
        for message in state['messages']:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(SystemMessage(content=message.content))
                case "assistant" | "ai":
                    tool_calls_converted = [convert_tool_call_for_model(tc) for tc in message.tool_calls or []]
                    messages.append(AIMessage(invalid_tool_calls=[], tool_calls=tool_calls_converted, type="ai", content=message.content or ""))
                case "tool":
                    # ToolMessage may require additional fields, adjust as needed
                    messages.append(ToolMessage(tool_call_id = message.tool_call_id, content=message.content))
                case _:
                    raise ValueError(f"Unsupported message role: {message.role}")

        messages.append(ToolMessage(content=a,tool_call_id=state['messages'][-1].tool_calls[0].id))
        response = await model.bind_tools([get_stock_price,*tools]).ainvoke(messages,config=config)
        if(response.tool_calls):
            tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
            a_message = AssistantMessage( role="assistant", tool_calls=tool_calls, id=response.id)
            state['messages'].append(a_message)
        else:
            a_message = AssistantMessage(id=response.id,content=response.content,role="assistant")
            state['messages'].append(a_message)
        
    return Command(
        goto="end",
    )

async def end_node(state: AgentState,config: RunnableConfig):
    print("inside end node")
    

async def agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("chat", chat_node)
    workflow.add_node("stock_analysis", stock_analysis_node)
    workflow.add_node("end", end_node)
    workflow.set_entry_point("chat")
    workflow.set_finish_point("end")
    
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", "stock_analysis")
    workflow.add_edge("stock_analysis", "end")
    workflow.add_edge("chat", "end")
    workflow.add_edge("end", END)
    
    # from langgraph.checkpoint.memory import MemorySaver
    # graph = workflow.compile(MemorySaver())
    graph = workflow.compile()
    return graph