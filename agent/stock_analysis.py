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

# import yfinance as yf
import pandas as pd
import requests
import asyncio
from prompts import system_prompt, insights_prompt
from datetime import datetime
from typing import Any
import uuid
from tavily import TavilyClient
import os

load_dotenv()


class AgentState(CopilotKitState):
    """
    This is the state of the agent.
    It is a subclass of the MessagesState class from langgraph.
    """

    tools: list
    messages: list
    be_stock_data: Any
    be_arguments: dict
    available_cash: int
    investment_summary: dict


def convert_tool_call(tc):
    return {
        "id": tc.get("id"),
        "type": "function",
        "function": {
            "name": tc.get("name"),
            "arguments": json.dumps(tc.get("args", {})),
        },
    }


def convert_tool_call_for_model(tc):
    return {
        "id": tc.id,
        "name": tc.function.name,
        "args": json.loads(tc.function.arguments),
    }


async def get_stock_price_tool(
    tickers: list[str], config: RunnableConfig, period: str = "1d", interval: str = "1m"
) -> str:
    try:
        config.get("configurable").get("tool_logs")["items"].append(
            {"toolName": "GET_STOCK_PRICE", "status": "inProgress"}
        )
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "add",
                        "path": "/items/-",
                        "value": {
                            "toolName": "GET_STOCK_PRICE",
                            "status": "inProgress",
                        },
                    }
                ],
            )
        )
        await asyncio.sleep(2)

        tickers_list = json.loads(tickers)["tickers"]
        tikers = [yf.Ticker(ticker) for ticker in tickers_list]
        results = []
        for ticker_obj, symbol in zip(tikers, tickers_list):
            print(json.loads(tickers)["interval"], "intervalintervalinterval")
            hist = ticker_obj.history(
                period=json.loads(tickers)["period"],
                interval=json.loads(tickers)["interval"],
            )
            info = ticker_obj.info
            price = [
                {"date": str(hist.index[i].date()), "close": hist["Close"].iloc[i]}
                for i in range(len(hist))
            ]
            company_name = info.get("longName", "N/A")
            revenue = info.get("totalRevenue", "N/A")

            results.append(
                {
                    "ticker": symbol,
                    "price": price,
                    "company_name": company_name,
                    "revenue": revenue,
                }
            )
        index = len(config.get("configurable").get("tool_logs")["items"]) - 1
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "replace",
                        "path": f"/items/{index}/status",
                        "value": "completed",
                    }
                ],
            )
        )
        await asyncio.sleep(0)
        return json.dumps({"results": results})
    except Exception as e:
        print(e)
        return f"Error: {e}"


async def get_revenue_data_tool(tickers: list[str], config: RunnableConfig) -> str:
    try:
        config.get("configurable").get("tool_logs")["items"].append(
            {"toolName": "GET_REVENUE_DATA", "status": "inProgress"}
        )
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "add",
                        "path": "/items/-",
                        "value": {
                            "toolName": "GET_REVENUE_DATA",
                            "status": "inProgress",
                        },
                    }
                ],
            )
        )
        await asyncio.sleep(2)
        tickers_list = json.loads(tickers)["tickers"]
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
                revenue_dict = {
                    str(year.year): (
                        int(revenue_row[year])
                        if not pd.isna(revenue_row[year])
                        else None
                    )
                    for year in revenue_row.index[:5]
                }
            else:
                revenue_dict = {}
            results.append(
                {
                    "ticker": symbol,
                    "company_name": company_name,
                    "revenue_by_year": revenue_dict,
                }
            )
        index = len(config.get("configurable").get("tool_logs")["items"]) - 1
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "replace",
                        "path": f"/items/{index}/status",
                        "value": "completed",
                    }
                ],
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
                    "description": "A stock ticker symbol, e.g. 'AAPL', 'GOOGL'.",
                },
                "description": "A list of stock ticker symbols, e.g. ['AAPL', 'GOOGL'].",
            },
            "period": {
                "type": "string",
                "description": "The period of time to get the stock prices for, e.g. '1d', '5d', '1mo', '3mo', '6mo', '1y'1d', '5d', '7d', '1mo', '3mo', '6mo', '1y', '2y', '3y', '4y', '5y'.",
            },
            "interval": {
                "type": "string",
                "description": "The interval of time to get the stock prices for, e.g. '1m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'. You itself choose the interval based on the period of time you want to get the stock prices for. If the period is small like 1d, then choose the interval as '1m' or '5m' or '15m' or '30m' or '60m' or '90m' or '1h'. If the period is large like 1y, then choose the interval as '1mo' or '3mo'. If it like more than 1y, then choose the interval as '6mo'.",
            },
        },
        "required": ["tickers", "period", "interval"],
    },
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
                    "description": "A stock ticker symbol, e.g. 'AAPL', 'GOOGL'.",
                },
                "description": "A list of stock ticker symbols, e.g. ['AAPL', 'GOOGL'].",
            }
        },
        "required": ["tickers"],
    },
}

extract_relevant_data_from_user_prompt = {
    "name": "extract_relevant_data_from_user_prompt",
    "description": "Gets the data like ticker symbols, amount of dollars to be invested, interval of investment",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker_symbols": {
                "type": "array",
                "items": {
                    "type": "string",
                    "description": "A stock ticker symbol, e.g. 'AAPL', 'GOOGL'.",
                },
                "description": "A list of stock ticker symbols, e.g. ['AAPL', 'GOOGL'].",
            },
            "investment_date": {
                "type": "string",
                "description": "The date of investment, e.g. '2023-01-01'.",
            },
            "amount_of_dollars_to_be_invested": {
                "type": "array",
                "items": {
                    "type": "number",
                    "description": "The amount of dollars to be invested, e.g. 10000.",
                },
                "description": "The amount of dollars to be invested, e.g. [10000, 20000, 30000].",
            },
            "interval_of_investment": {
                "type": "string",
                "description": "The interval of investment, e.g. '1d', '5d', '1mo', '3mo', '6mo', '1y'1d', '5d', '7d', '1mo', '3mo', '6mo', '1y', '2y', '3y', '4y', '5y'. If the user did not specify the interval, then assume it as 'single_shot'",
            },
        },
        "required": [
            "ticker_symbols",
            "investment_date",
            "amount_of_dollars_to_be_invested",
        ],
    },
}


generate_insights = {
    "name": "generate_insights",
    "description": "Generate positive (bull) and negative (bear) insights for a stock or portfolio.",
    "parameters": {
        "type": "object",
        "properties": {
            "bullInsights": {
                "type": "array",
                "description": "A list of positive insights (bull case) for the stock or portfolio.",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short title for the positive insight.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the positive insight.",
                        },
                        "emoji": {
                            "type": "string",
                            "description": "Emoji representing the positive insight.",
                        },
                    },
                    "required": ["title", "description", "emoji"],
                },
            },
            "bearInsights": {
                "type": "array",
                "description": "A list of negative insights (bear case) for the stock or portfolio.",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short title for the negative insight.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the negative insight.",
                        },
                        "emoji": {
                            "type": "string",
                            "description": "Emoji representing the negative insight.",
                        },
                    },
                    "required": ["title", "description", "emoji"],
                },
            },
        },
        "required": ["bullInsights", "bearInsights"],
    },
}


async def chat_node(state: AgentState, config: RunnableConfig):
    try:

        model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
        tools = [t.dict() for t in state["tools"]]
        messages = []
        for message in state["messages"]:
            match message.role:
                case "user":
                    messages.append(
                        HumanMessage(content="New request: " + message.content)
                    )
                case "system":
                    messages.append(SystemMessage(content=system_prompt))
                case "assistant" | "ai":
                    tool_calls_converted = [
                        convert_tool_call_for_model(tc)
                        for tc in message.tool_calls or []
                    ]
                    messages.append(
                        AIMessage(
                            invalid_tool_calls=[],
                            tool_calls=tool_calls_converted,
                            type="ai",
                            content=message.content or "",
                        )
                    )
                case "tool":
                    # ToolMessage may require additional fields, adjust as needed
                    messages.append(
                        ToolMessage(
                            tool_call_id=message.tool_call_id, content=message.content
                        )
                    )
                case _:
                    raise ValueError(f"Unsupported message role: {message.role}")

        response = await model.bind_tools(
            [extract_relevant_data_from_user_prompt]
        ).ainvoke(messages, config=config)
        if response.tool_calls:
            tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
            a_message = AssistantMessage(
                role="assistant", tool_calls=tool_calls, id=response.id
            )
            state["messages"].append(a_message)
            return
        else:
            a_message = AssistantMessage(
                id=response.id, content=response.content, role="assistant"
            )
            state["messages"].append(a_message)
        print("hello")
    except Exception as e:
        print(e)
        return Command(
            goto="end",
        )
    return


async def stock_analysis_node(state: AgentState, config: RunnableConfig):

    print("inside stock analysis node")
    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    tools = [t.dict() for t in state["tools"]]

    if state["messages"][-1].tool_calls:
        tool_res = []
        for i in range(len(state["messages"][-1].tool_calls)):

            if state["messages"][-1].tool_calls[i].function.name == "get_stock_price":
                tool_res.append(
                    await get_stock_price_tool(
                        state["messages"][-1].tool_calls[i].function.arguments, config
                    )
                )
            elif (
                state["messages"][-1].tool_calls[i].function.name == "get_revenue_data"
            ):
                tool_res.append(
                    await get_revenue_data_tool(
                        state["messages"][-1].tool_calls[i].function.arguments, config
                    )
                )

        messages = []
        for message in state["messages"]:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(SystemMessage(content=system_prompt))
                case "assistant" | "ai":
                    tool_calls_converted = [
                        convert_tool_call_for_model(tc)
                        for tc in message.tool_calls or []
                    ]
                    messages.append(
                        AIMessage(
                            invalid_tool_calls=[],
                            tool_calls=tool_calls_converted,
                            type="ai",
                            content=message.content or "",
                        )
                    )
                case "tool":
                    # ToolMessage may require additional fields, adjust as needed
                    messages.append(
                        ToolMessage(
                            tool_call_id=message.tool_call_id, content=message.content
                        )
                    )
                case _:
                    raise ValueError(f"Unsupported message role: {message.role}")
        for i in range(len(tool_res)):
            messages.append(
                ToolMessage(
                    content=tool_res[i],
                    tool_call_id=state["messages"][-1].tool_calls[i].id,
                )
            )

        response = await model.bind_tools(tools).ainvoke(messages, config=config)
        if response.tool_calls:
            tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
            a_message = AssistantMessage(
                role="assistant", tool_calls=tool_calls, id=response.id
            )
            state["messages"].append(a_message)
        else:
            if response.content == "" and response.tool_calls == []:
                response.content = "Something went wrong! Please try again."
            a_message = AssistantMessage(
                id=response.id, content=response.content, role="assistant"
            )
            state["messages"].append(a_message)

    return Command(
        goto="end",
    )


async def end_node(state: AgentState, config: RunnableConfig):
    print("inside end node")


async def simulation_node(state: AgentState, config: RunnableConfig):
    print("inside simulation node")
    arguments = json.loads(state["messages"][-1].tool_calls[0].function.arguments)
    tickers = arguments["ticker_symbols"]
    investment_date = arguments["investment_date"]
    current_year = datetime.now().year
    if current_year - int(investment_date[:4]) == 0:
        history_period = "1y"
    else:
        history_period = f"{current_year - int(investment_date[:4])}y"

    data = yf.download(
        tickers,
        period=history_period,
        interval="3mo",
        start=investment_date,
        end=datetime.today().strftime("%Y-%m-%d"),
    )
    state["be_stock_data"] = data["Close"]
    state["be_arguments"] = arguments
    print(state["be_stock_data"])
    return Command(goto="cash_allocation", update=state)


async def cash_allocation_node(state: AgentState, config: RunnableConfig):
    print("inside cash allocation node")
    import numpy as np
    import pandas as pd

    # from ag_ui.core.types import AssistantMessage,ToolMessage

    stock_data = state["be_stock_data"]  # DataFrame: index=date, columns=tickers
    args = state["be_arguments"]
    tickers = args["ticker_symbols"]
    investment_date = args["investment_date"]
    amounts = args["amount_of_dollars_to_be_invested"]  # list, one per ticker
    interval = args.get("interval_of_investment", "single_shot")

    # Use state['available_cash'] as a single integer (total wallet cash)
    if "available_cash" in state and state["available_cash"] is not None:
        total_cash = state["available_cash"]
    else:
        total_cash = sum(amounts)
    holdings = {ticker: 0.0 for ticker in tickers}
    investment_log = []
    add_funds_needed = False
    add_funds_dates = []

    # Ensure DataFrame is sorted by date
    stock_data = stock_data.sort_index()

    if interval == "single_shot":
        # Buy all shares at the first available date using allocated money for each ticker
        first_date = stock_data.index[0]
        row = stock_data.loc[first_date]
        for idx, ticker in enumerate(tickers):
            price = row[ticker]
            if np.isnan(price):
                investment_log.append(
                    f"{first_date.date()}: No price data for {ticker}, could not invest."
                )
                add_funds_needed = True
                add_funds_dates.append(
                    (str(first_date.date()), ticker, price, amounts[idx])
                )
                continue
            allocated = amounts[idx]
            if total_cash >= allocated and allocated >= price:
                shares_to_buy = allocated // price
                if shares_to_buy > 0:
                    cost = shares_to_buy * price
                    holdings[ticker] += shares_to_buy
                    total_cash -= cost
                    investment_log.append(
                        f"{first_date.date()}: Bought {shares_to_buy:.2f} shares of {ticker} at ${price:.2f} (cost: ${cost:.2f})"
                    )
                else:
                    investment_log.append(
                        f"{first_date.date()}: Not enough allocated cash to buy {ticker} at ${price:.2f}. Allocated: ${allocated:.2f}"
                    )
                    add_funds_needed = True
                    add_funds_dates.append(
                        (str(first_date.date()), ticker, price, allocated)
                    )
            else:
                investment_log.append(
                    f"{first_date.date()}: Not enough total cash to buy {ticker} at ${price:.2f}. Allocated: ${allocated:.2f}, Available: ${total_cash:.2f}"
                )
                add_funds_needed = True
                add_funds_dates.append(
                    (str(first_date.date()), ticker, price, total_cash)
                )
        # No further purchases on subsequent dates
    else:
        # DCA or other interval logic (previous logic)
        for date, row in stock_data.iterrows():
            for i, ticker in enumerate(tickers):
                price = row[ticker]
                if np.isnan(price):
                    continue  # skip if price is NaN
                # Invest as much as possible for this ticker at this date
                if total_cash >= price:
                    shares_to_buy = total_cash // price
                    if shares_to_buy > 0:
                        cost = shares_to_buy * price
                        holdings[ticker] += shares_to_buy
                        total_cash -= cost
                        investment_log.append(
                            f"{date.date()}: Bought {shares_to_buy:.2f} shares of {ticker} at ${price:.2f} (cost: ${cost:.2f})"
                        )
                else:
                    add_funds_needed = True
                    add_funds_dates.append(
                        (str(date.date()), ticker, price, total_cash)
                    )
                    investment_log.append(
                        f"{date.date()}: Not enough cash to buy {ticker} at ${price:.2f}. Available: ${total_cash:.2f}. Please add more funds."
                    )

    # Calculate final value and new summary fields
    final_prices = stock_data.iloc[-1]
    total_value = 0.0
    returns = {}
    total_invested_per_stock = {}
    percent_allocation_per_stock = {}
    percent_return_per_stock = {}
    total_invested = 0.0
    for idx, ticker in enumerate(tickers):
        # Calculate how much was actually invested in this stock
        if interval == "single_shot":
            # Only one purchase at first date
            first_date = stock_data.index[0]
            price = stock_data.loc[first_date][ticker]
            shares_bought = holdings[ticker]
            invested = shares_bought * price
        else:
            # Sum all purchases from the log
            invested = 0.0
            for log in investment_log:
                if f"shares of {ticker}" in log and "Bought" in log:
                    # Extract cost from log string
                    try:
                        cost_str = log.split("(cost: $")[-1].split(")")[0]
                        invested += float(cost_str)
                    except Exception:
                        pass
        total_invested_per_stock[ticker] = invested
        total_invested += invested
    # Now calculate percent allocation and percent return
    for ticker in tickers:
        invested = total_invested_per_stock[ticker]
        holding_value = holdings[ticker] * final_prices[ticker]
        returns[ticker] = holding_value - invested
        total_value += holding_value
        percent_allocation_per_stock[ticker] = (
            (invested / total_invested * 100) if total_invested > 0 else 0.0
        )
        percent_return_per_stock[ticker] = (
            ((holding_value - invested) / invested * 100) if invested > 0 else 0.0
        )
    total_value += total_cash  # Add remaining cash to total value

    # Store results in state
    state["investment_summary"] = {
        "holdings": holdings,
        "final_prices": final_prices.to_dict(),
        "cash": total_cash,
        "returns": returns,
        "total_value": total_value,
        "investment_log": investment_log,
        "add_funds_needed": add_funds_needed,
        "add_funds_dates": add_funds_dates,
        "total_invested_per_stock": total_invested_per_stock,
        "percent_allocation_per_stock": percent_allocation_per_stock,
        "percent_return_per_stock": percent_return_per_stock,
    }
    state["available_cash"] = total_cash  # Update available cash in state

    # --- Portfolio vs SPY performanceData logic ---
    # Get SPY prices for the same dates
    spy_ticker = "SPY"
    spy_prices = None
    try:
        spy_prices = yf.download(
            spy_ticker,
            period=f"{len(stock_data)//4}y" if len(stock_data) > 4 else "1y",
            interval="3mo",
            start=stock_data.index[0],
            end=stock_data.index[-1],
        )["Close"]
        # Align SPY prices to stock_data dates
        spy_prices = spy_prices.reindex(stock_data.index, method="ffill")
    except Exception as e:
        print("Error fetching SPY data:", e)
        spy_prices = pd.Series([None] * len(stock_data), index=stock_data.index)

    # Simulate investing the same total_invested in SPY
    spy_shares = 0.0
    spy_cash = total_invested
    spy_invested = 0.0
    spy_investment_log = []
    if interval == "single_shot":
        first_date = stock_data.index[0]
        spy_price = spy_prices.loc[first_date]
        if isinstance(spy_price, pd.Series):
            spy_price = spy_price.iloc[0]
        if not pd.isna(spy_price):
            spy_shares = spy_cash // spy_price
            spy_invested = spy_shares * spy_price
            spy_cash -= spy_invested
            spy_investment_log.append(
                f"{first_date.date()}: Bought {spy_shares:.2f} shares of SPY at ${spy_price:.2f} (cost: ${spy_invested:.2f})"
            )
    else:
        # DCA: invest equal portions at each date
        dca_amount = total_invested / len(stock_data)
        for date in stock_data.index:
            spy_price = spy_prices.loc[date]
            if isinstance(spy_price, pd.Series):
                spy_price = spy_price.iloc[0]
            if not pd.isna(spy_price):
                shares = dca_amount // spy_price
                cost = shares * spy_price
                spy_shares += shares
                spy_cash -= cost
                spy_invested += cost
                spy_investment_log.append(
                    f"{date.date()}: Bought {shares:.2f} shares of SPY at ${spy_price:.2f} (cost: ${cost:.2f})"
                )

    # Build performanceData array
    performanceData = []
    running_holdings = holdings.copy()
    running_cash = total_cash
    for date in stock_data.index:
        # Portfolio value: sum of shares * price at this date + cash
        port_value = (
            sum(
                running_holdings[t] * stock_data.loc[date][t]
                for t in tickers
                if not pd.isna(stock_data.loc[date][t])
            )
            + running_cash
        )
        # SPY value: shares * price + cash
        spy_price = spy_prices.loc[date]
        if isinstance(spy_price, pd.Series):
            spy_price = spy_price.iloc[0]
        spy_val = spy_shares * spy_price + spy_cash if not pd.isna(spy_price) else None
        performanceData.append(
            {
                "date": str(date.date()),
                "portfolio": float(port_value) if port_value is not None else None,
                "spy": float(spy_val) if spy_val is not None else None,
            }
        )

    state["investment_summary"]["performanceData"] = performanceData
    # --- End performanceData logic ---

    # Compose summary message
    if add_funds_needed:
        msg = "Some investments could not be made due to insufficient funds. Please add more funds to your wallet.\n"
        for d, t, p, c in add_funds_dates:
            msg += (
                f"On {d}, not enough cash for {t}: price ${p:.2f}, available ${c:.2f}\n"
            )
    else:
        msg = "All investments were made successfully.\n"
    msg += f"\nFinal portfolio value: ${total_value:.2f}\n"
    msg += "Returns by ticker (percent and $):\n"
    for ticker in tickers:
        percent = percent_return_per_stock[ticker]
        abs_return = returns[ticker]
        msg += f"{ticker}: {percent:.2f}% (${abs_return:.2f})\n"

    state["messages"].append(
        ToolMessageAGUI(
            role="tool",
            id=str(uuid.uuid4()),
            content="The relevant details had been extracted",
            tool_call_id=state["messages"][-1].tool_calls[0].id,
        )
    )
    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    # response = await model.ainvoke(
    #     [
    #         {
    #             "role": "developer",
    #             "content": mod_prompt,
    #         },
    #         {
    #             "role": "user",
    #             "content": msg,
    #         },
    #     ],
    #     config=config,
    # )
    # state["messages"].append(
    #     AssistantMessage(role="assistant", content=response.content, id=str(uuid.uuid4()))
    # )

    state["messages"].append(
        AssistantMessage(
            role="assistant",
            tool_calls=[
                {
                    "id": str(uuid.uuid4()),
                    "type": "function",
                    "function": {
                        "name": "render_standard_charts_and_table",
                        "arguments": json.dumps(
                            {"investment_summary": state["investment_summary"]}
                        ),
                    },
                }
            ],
            id=str(uuid.uuid4()),
        )
    )
    # config.get("configurable").get("emit_event")(
    #     StateDeltaEvent(
    #         type=EventType.STATE_DELTA,
    #         delta=[
    #             {
    #                 "op": "replace",
    #                 "path": "/available_cash",
    #                 "value": total_cash,
    #             },
    #             {
    #                 "op": "replace",
    #                 "path": "/investment_summary",
    #                 "value": state["investment_summary"],
    #             },
    #         ],
    #     )
    # )
    # await asyncio.sleep(0)

    return Command(goto="ui_decision", update=state)


async def ui_decision_node(state: AgentState, config: RunnableConfig):
    print("inside ui decision node")
    return Command(goto="insights", update=state)


async def insights_node(state: AgentState, config: RunnableConfig):
    print("inside insights node")
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        print("TAVILY_API_KEY not set in environment.")
        return Command(goto="end", update=state)
    tavily_client = TavilyClient(api_key=tavily_api_key)
    args = state.get("be_arguments") or state.get("arguments")
    tickers = args.get("ticker_symbols", [])
    news_summary = {}
    for ticker in tickers:
        try:
            pos_results = tavily_client.search(
                f"good news about {ticker} stock", topic="news", max_results=2
            )
            neg_results = tavily_client.search(
                f"bad news about {ticker} stock", topic="news", max_results=2
            )
            news_summary[ticker] = {
                "positive": [
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "content": item.get("content", ""),
                    }
                    for item in pos_results.get("results", [])
                ],
                "negative": [
                    {
                        "title": item["title"],
                        "url": item["url"],
                        "content": item.get("content", ""),
                    }
                    for item in neg_results.get("results", [])
                ],
            }
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            news_summary[ticker] = {"positive": [], "negative": []}
    # Compose a summary string for the AI model
    summary_str = "Stock News Insights:\n"
    for ticker, news in news_summary.items():
        summary_str += f"\nTicker: {ticker}\n"
        summary_str += "  Positive News:\n"
        for n in news["positive"]:
            summary_str += f"    - {n['title']} ({n['url']})\n"
        summary_str += "  Negative News:\n"
        for n in news["negative"]:
            summary_str += f"    - {n['title']} ({n['url']})\n"
    # Present to AI model
    model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
    response = await model.bind_tools(generate_insights).ainvoke(
        [
            {"role": "system", "content": insights_prompt},
            {"role": "user", "content": summary_str},
        ],
        config=config,
    )
    if response.tool_calls:
        args_dict = json.loads(state['messages'][-1].tool_calls[0].function.arguments)

# Step 2: Add the insights key
        args_dict['insights'] = response.tool_calls[0]['args']

        # Step 3: Convert back to string
        state['messages'][-1].tool_calls[0].function.arguments = json.dumps(args_dict)
    else:
        state["insights"] = {}

    return Command(goto="end", update=state)


def your_router_function(state: AgentState, config: RunnableConfig):
    if (
        state["messages"][-1].tool_calls == []
        or state["messages"][-1].tool_calls is None
    ):
        return "end"
    else:
        return "simulation"


async def agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("chat", chat_node)
    workflow.add_node("simulation", simulation_node)
    workflow.add_node("cash_allocation", cash_allocation_node)
    workflow.add_node("ui_decision", ui_decision_node)
    workflow.add_node("insights", insights_node)
    workflow.add_node("end", end_node)
    workflow.set_entry_point("chat")
    workflow.set_finish_point("end")

    workflow.add_edge(START, "chat")
    workflow.add_conditional_edges("chat", your_router_function)
    workflow.add_edge("simulation", "cash_allocation")
    workflow.add_edge("cash_allocation", "ui_decision")
    workflow.add_edge("ui_decision", "insights")
    workflow.add_edge("insights", "end")
    workflow.add_edge("end", END)
    # from langgraph.checkpoint.memory import MemorySaver
    # graph = workflow.compile(MemorySaver())
    graph = workflow.compile()
    return graph
