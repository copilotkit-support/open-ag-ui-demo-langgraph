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
import pandas as pd

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
    
def get_revenue_data_tool(tickers: list[str]) -> str:
    try:
        tickers_list = json.loads(tickers)['tickers']
        tikers = [yf.Ticker(ticker) for ticker in tickers_list]
        results = []
        for ticker_obj, symbol in zip(tikers, tickers_list):
            info = ticker_obj.info
            company_name = info.get("longName", "N/A")
            # Get annual financials (income statement)
            financials = ticker_obj.financials
            # financials is a DataFrame with columns as years (ending date)
            # Revenue is usually under 'Total Revenue' or 'TotalRevenue'
            revenue_row = None
            for key in ["Total Revenue", "TotalRevenue"]:
                if key in financials.index:
                    revenue_row = financials.loc[key]
                    break
            if revenue_row is not None:
                # Get the last 5 years (or less if not available)
                revenue_dict = {str(year.year): int(revenue_row[year]) if not pd.isna(revenue_row[year]) else None for year in revenue_row.index[:5]}
            else:
                revenue_dict = {}
            results.append({
                "ticker": symbol,
                "company_name": company_name,
                "revenue_by_year": revenue_dict
            })
        return json.dumps({"results": results})
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

get_revenue_data = {
    "name": "get_revenue_data",
    "description": "Get the revenue data of Respective ticker symbols.",
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
                    messages.append(SystemMessage(content="""
                    Please act as an efficient, competent, conscientious, and industrious professional assistant.
                    
                    Help the user achieve their goals, and you do so in a way that is as efficient as possible, without unnecessary fluff, but also without sacrificing professionalism.
                    Always be polite and respectful, and prefer brevity over verbosity.
                    
                    They have provided you with tools you can call to initiate actions on their behalf, or functions you can call to receive more information.
                    
                    Please assist them as best you can.
                    
                    You can ask them for clarifying questions if needed, but don't be annoying about it. If you can reasonably 'fill in the blanks' yourself, do so.
                    
                    When a tool call is made and tool message is received:
                    - If the tool call is accepted, you can use the tool message context to update the user.
                    - If the tool message is rejected, you need to use the tool message context to update the user and not trigger any other tool calls.
                                                 """))
                case "assistant" | "ai":
                    tool_calls_converted = [convert_tool_call_for_model(tc) for tc in message.tool_calls or []]
                    messages.append(AIMessage(invalid_tool_calls=[], tool_calls=tool_calls_converted, type="ai", content=message.content or ""))
                case "tool":
                    # ToolMessage may require additional fields, adjust as needed
                    messages.append(ToolMessage(tool_call_id = message.tool_call_id, content=message.content))
                case _:
                    raise ValueError(f"Unsupported message role: {message.role}")
        
        response = await model.bind_tools([get_stock_price,get_revenue_data,*tools]).ainvoke(messages,config=config)
        if(response.tool_calls):
            if(('get' in response.tool_calls[0]['name'])):
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
    
    if(state['messages'][-1].tool_calls ):
        tool_res = []
        for i in range(len(state['messages'][-1].tool_calls)):
            
            if(state['messages'][-1].tool_calls[i].function.name == "get_stock_price"):
                tool_res.append(get_stock_price_tool(state['messages'][-1].tool_calls[i].function.arguments))
            elif(state['messages'][-1].tool_calls[i].function.name == "get_revenue_data"):
                tool_res.append(get_revenue_data_tool(state['messages'][-1].tool_calls[i].function.arguments))
        
        messages = []
        for message in state['messages']:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(SystemMessage(content="""
                    Please act as an efficient, competent, conscientious, and industrious professional assistant.
                    
                    Help the user achieve their goals, and you do so in a way that is as efficient as possible, without unnecessary fluff, but also without sacrificing professionalism.
                    Always be polite and respectful, and prefer brevity over verbosity.
                    
                    They have provided you with functions you can call to initiate actions on their behalf, or functions you can call to receive more information.
                    
                    Please assist them as best you can.
                    
                    You can ask them for clarifying questions if needed, but don't be annoying about it. If you can reasonably 'fill in the blanks' yourself, do so.
                    
                    When a tool call is made and tool message is received:
                    - If the tool call is accepted, you can use the tool message context to update the user.
                    - If the tool message is rejected, you need to use the tool message context to update the user and not trigger any other tool calls.
                                                 """))
                case "assistant" | "ai":
                    tool_calls_converted = [convert_tool_call_for_model(tc) for tc in message.tool_calls or []]
                    messages.append(AIMessage(invalid_tool_calls=[], tool_calls=tool_calls_converted, type="ai", content=message.content or ""))
                case "tool":
                    # ToolMessage may require additional fields, adjust as needed
                    messages.append(ToolMessage(tool_call_id = message.tool_call_id, content=message.content))
                case _:
                    raise ValueError(f"Unsupported message role: {message.role}")
        for i in range(len(tool_res)):
            messages.append(ToolMessage(content=tool_res[i],tool_call_id=state['messages'][-1].tool_calls[i].id))
        
        
        response = await model.bind_tools([get_stock_price,get_revenue_data,*tools]).ainvoke(messages,config=config)
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