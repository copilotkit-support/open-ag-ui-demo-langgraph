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
    
async def get_stock_price_tool(tickers: list[str], config: RunnableConfig) -> str:
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
        return {"results": results}
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


def get_top_stocks_by_sector(sector: str, top_n: int = 10, period: str = '1mo') -> pd.DataFrame:
    """
    Fetches the top-performing stocks in a given sector based on return over a specified period.

    Parameters:
    - sector (str): The industry sector to filter (e.g., 'Technology', 'Healthcare').
    - top_n (int): Number of top stocks to return. Default is 10.
    - period (str): Performance period for return calculation (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y').

    Returns:
    - DataFrame with columns ['Ticker', 'Name', 'Sector', 'Return'] sorted by Return descending.
    """
    # 1. Load S&P 500 constituents from Wikipedia
    wiki_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    resp = requests.get(wiki_url)
    tables = pd.read_html(StringIO(resp.text))
    sp500 = tables[0]
    sp500 = sp500.rename(columns={'Security': 'Name', 'GICS Sector': 'Sector'})

    # 2. Filter by sector
    sector_df = sp500[sp500['Sector'].str.lower() == sector.lower()].copy()
    tickers = sector_df['Symbol'].tolist()

    if not tickers:
        raise ValueError(f"No tickers found for sector '{sector}'")

    # 3. Download price history
    data = yf.download(tickers, period=period, group_by='ticker', threads=True, progress=False)

    # 4. Calculate returns
    returns = []
    for ticker in tickers:
        try:
            hist = data[ticker]['Close'] if len(tickers) > 1 else data['Close']
            ret = (hist.iloc[-1] / hist.iloc[0] - 1) * 100
        except Exception:
            ret = float('nan')
        returns.append(ret)

    # 5. Assemble result DataFrame
    result = sector_df[['Symbol', 'Name', 'Sector']].copy()
    result['Return'] = returns
    result = result.dropna(subset=['Return'])
    result = result.sort_values('Return', ascending=False).reset_index(drop=True)
    print(result.head(top_n))






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
    try:
       
        model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        tools = [t.dict() for t in state['tools']]
        messages = []
        for message in state['messages']:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(SystemMessage(content="""
You are a professional financial assistant. Your core priorities:

**INTELLIGENCE & EFFICIENCY**
- Be efficient & concise
- Deliver exactly what the user needs, without fluff
- Maintain a professional, respectful tone
- Anticipate needs and fill in missing details when reasonable
- Evenif the user say top stocks from a sector, then assume the top companies and tickers that are in that sector based on your knowledge and call the tools to get the data. Dont ask the user for clarification. They will mentiont he changes if they want to.

**AUTONOMOUS COMPANY DETECTION (CRITICAL)**
- Automatically identify companies from user queries without asking for clarification
- Map company names to correct ticker symbols (e.g., "Apple" → AAPL, "Microsoft" → MSFT, "Tesla" → TSLA)
- Handle common variations: abbreviations, informal names, subsidiaries
- If the user mention a sector or more general term, then based on your knowledge of the stock market, assume the companies and tickers that are in that sector and call the tools to get the data. Dont ask the user for clarification.
- If the user mentions an ambiguous term, then assuem the companies in that sector based on your knowledge and do the tool calls. As much as possible, dont ask the user for clarification, and deduct the companies and tickers yourself.
- For ambiguous references, use the most likely/prominent company match
- Evenif the user say top stocks from a sector, then assume the top companies and tickers that are in that sector based on your knowledge and call the tools to get the data. Dont ask the user for clarification. They will mentiont he changes if they want to.

**FINANCIAL DATA HANDLING**
- Call stock data tools immediately when company is identified
- Use proper ticker symbols in tool calls
- Provide relevant financial context and analysis with raw data

**TOOL USAGE**
- Use available tools smartly, especially for charts, tables, and data visualization
- Handle responses: Success → relay results; Failure → inform clearly without immediate retry
- Sequential renders: For multiple render_ tools, suggest one at a time

**EXAMPLES OF EXPECTED BEHAVIOR**
- Query: "How's Apple doing?" → Detect AAPL, call stock tools, provide data
- Query: "Compare Tesla and Ford" → Identify TSLA & F, get both datasets
- Query: "Microsoft earnings" → Recognize MSFT, fetch earnings data

Stay proactive and keep user goals central. Proceed with intelligent financial assistance.
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
                    messages.append(SystemMessage(content="""
You are a professional financial assistant. Your core priorities:

**INTELLIGENCE & EFFICIENCY**
- Be efficient & concise
- Deliver exactly what the user needs, without fluff
- Maintain a professional, respectful tone
- Anticipate needs and fill in missing details when reasonable

**AUTONOMOUS COMPANY DETECTION (CRITICAL)**
- Automatically identify companies from user queries without asking for clarification
- Map company names to correct ticker symbols (e.g., "Apple" → AAPL, "Microsoft" → MSFT, "Tesla" → TSLA)
- Handle common variations: abbreviations, informal names, subsidiaries
- If the user mention a sector or more general term, then based on your knowledge of the stock market, assume the companies and tickers that are in that sector and call the tools to get the data. Dont ask the user for clarification.
- If the user mentions an ambiguous term, then assuem the companies in that sector based on your knowledge and do the tool calls. As much as possible, dont ask the user for clarification, and deduct the companies and tickers yourself.
- For ambiguous references, use the most likely/prominent company match
- Evenif the user say top stocks from a sector, then assume the top companies and tickers that are in that sector based on your knowledge and call the tools to get the data. Dont ask the user for clarification. They will mentiont he changes if they want to.

**FINANCIAL DATA HANDLING**
- Call stock data tools immediately when company is identified
- Use proper ticker symbols in tool calls
- Provide relevant financial context and analysis with raw data

**TOOL USAGE**
- Use available tools smartly, especially for charts, tables, and data visualization
- Handle responses: Success → relay results; Failure → inform clearly without immediate retry
- Sequential renders: For multiple render_ tools, suggest one at a time
- Always use the provided visual tools to show the data to the user. Just use the tools directly, overuse of these tools are what is expected.
- IMPORTANT: Dont ask the user to render the data, just use the tools like Bar chart and table directly. 
                                                   
**EXAMPLES OF EXPECTED BEHAVIOR**
- Query: "How's Apple doing?" → Detect AAPL, call stock tools, provide data
- Query: "Compare Tesla and Ford" → Identify TSLA & F, get both datasets
- Query: "Microsoft earnings" → Recognize MSFT, fetch earnings data

Stay proactive and keep user goals central. Proceed with intelligent financial assistance."""))
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