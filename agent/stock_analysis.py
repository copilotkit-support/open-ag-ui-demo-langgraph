from langchain_core.runnables import RunnableConfig
from ag_ui.core import StateDeltaEvent, EventType
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from ag_ui.core.types import AssistantMessage, ToolMessage as ToolMessageAGUI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import yfinance as yf
from copilotkit import CopilotKitState
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import json
import yfinance as yf
import pandas as pd
import requests
import asyncio
from prompts import system_prompt
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
    
async def get_stock_price_tool(tickers: list[str],config: RunnableConfig, period: str = "1d", interval: str = "1m" ) -> str:
    try:
        config.get("configurable").get("tool_logs")["items"].append({
            "toolName": "GET_STOCK_PRICE",
            "status": "inProgress"
        })
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "add",
                        "path": "/items/-",
                        "value": {
                            "toolName": "GET_STOCK_PRICE",
                            "status": "inProgress"
                        }
                    }
                ]
            )
        )
        await asyncio.sleep(2)
        
        
        tickers_list = json.loads(tickers)['tickers']
        tikers = [yf.Ticker(ticker) for ticker in tickers_list]
        results = []
        for ticker_obj, symbol in zip(tikers, tickers_list):
            print(json.loads(tickers)['interval'],'intervalintervalinterval')
            hist = ticker_obj.history(period=json.loads(tickers)['period'], interval=json.loads(tickers)['interval'])
            info = ticker_obj.info
            price = [
                {"date": str(hist.index[i].date()), "close": hist['Close'].iloc[i]}
                for i in range(len(hist))
            ]
            company_name = info.get("longName", "N/A")
            revenue = info.get("totalRevenue", "N/A")
        
            results.append({
                "ticker": symbol,
                "price": price,
                "company_name": company_name,
                "revenue": revenue
            })
        index = len(config.get("configurable").get("tool_logs")["items"]) - 1
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "replace",
                        "path": f"/items/{index}/status",
                        "value": "completed"
                    }
                ]
            )
        )
        await asyncio.sleep(0)
        return json.dumps({"results": results})
    except Exception as e:
        print(e)
        return f"Error: {e}"
    
async def get_revenue_data_tool(tickers: list[str], config: RunnableConfig) -> str:
    try:
        config.get("configurable").get("tool_logs")["items"].append({
            "toolName": "GET_REVENUE_DATA",
            "status": "inProgress"
        })
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "add",
                        "path": "/items/-",
                        "value": {
                            "toolName": "GET_REVENUE_DATA",
                            "status": "inProgress"
                        }
                    }
                ]
            )
        )
        await asyncio.sleep(2)
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
        index = len(config.get("configurable").get("tool_logs")["items"]) - 1
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "replace",
                        "path": f"/items/{index}/status",
                        "value": "completed"
                    }
                ]
            )
        )
        await asyncio.sleep(0)
        return json.dumps({"results": results})
    except Exception as e:
        print(e)
        return f"Error: {e}"

get_stock_price = {
    "name": "get_stock_price",
    "description": "Get the stock prices over a period of specific time of Respective ticker symbols.",
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
            },
            "period": {
                "type": "string",
                "description": "The period of time to get the stock prices for, e.g. '1d', '5d', '1mo', '3mo', '6mo', '1y'1d', '5d', '7d', '1mo', '3mo', '6mo', '1y', '2y', '3y', '4y', '5y'."
            },
            "interval": {
                "type": "string",
                "description": "The interval of time to get the stock prices for, e.g. '1m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'. You itself choose the interval based on the period of time you want to get the stock prices for. If the period is small like 1d, then choose the interval as '1m' or '5m' or '15m' or '30m' or '60m' or '90m' or '1h'. If the period is large like 1y, then choose the interval as '1mo' or '3mo'. If it like more than 1y, then choose the interval as '6mo'."
            }
        },
        "required": ["tickers", "period", "interval"]
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
    try:
       
        model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        tools = [t.dict() for t in state['tools']]
        messages = []
        for message in state['messages']:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(SystemMessage(content=system_prompt))
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
    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    tools = [t.dict() for t in state['tools']]
    
    if(state['messages'][-1].tool_calls ):
        tool_res = []
        for i in range(len(state['messages'][-1].tool_calls)):
            
            if(state['messages'][-1].tool_calls[i].function.name == "get_stock_price"):
                tool_res.append(await get_stock_price_tool(state['messages'][-1].tool_calls[i].function.arguments,config))
            elif(state['messages'][-1].tool_calls[i].function.name == "get_revenue_data"):
                tool_res.append(await get_revenue_data_tool(state['messages'][-1].tool_calls[i].function.arguments,config))
        
        messages = []
        for message in state['messages']:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(SystemMessage(content=system_prompt))
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
        
        
        response = await model.bind_tools(tools).ainvoke(messages,config=config)
        if(response.tool_calls):
            tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
            a_message = AssistantMessage( role="assistant", tool_calls=tool_calls, id=response.id)
            state['messages'].append(a_message)
        else:
            if(response.content == '' and response.tool_calls == []):
                response.content = "Something went wrong! Please try again."
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