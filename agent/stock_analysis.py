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
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
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

react_prompt = PromptTemplate(
    input_variables=["input", "agent_scratchpad"],
    template="""
You are a professional financial assistant. Your job is to answer user questions about stocks and companies using the tools at your disposal.

When you need to look up information, use the tools. Think step by step, and after each action, observe the result before continuing.

Question: {input}

{agent_scratchpad}
""")

llm = ChatOpenAI(model="gemini-2.0-flash", model_provider="google_genai")

tools = [get_stock_price, get_revenue_data]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.REACT_DESCRIPTION,
    verbose=True,
    prompt=react_prompt
)

    
