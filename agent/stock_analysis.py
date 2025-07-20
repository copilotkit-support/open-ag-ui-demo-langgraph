from langchain_core.runnables import RunnableConfig
from ag_ui.core import StateDeltaEvent, EventType
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage, HumanMessage
from ag_ui.core.types import AssistantMessage, ToolMessage as ToolMessageAGUI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
import yfinance as yf
from copilotkit import CopilotKitState
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import json
import pandas as pd
import asyncio
from prompts import system_prompt, insights_prompt
from datetime import datetime
from typing import Any
import uuid

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
    investment_portfolio: list
    tool_logs: list


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


extract_relevant_data_from_user_prompt = {
    "name": "extract_relevant_data_from_user_prompt",
    "description": "Gets the data like ticker symbols, amount of dollars to be invested, interval of investment.",
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
            "to_be_added_in_portfolio": {
                "type": "boolean",
                "description": "If user wants to add it in the current portfolio, then set it to true. If user wants to add it in the sandbox portfolio, then set it to false.",
            },
        },
        "required": [
            "ticker_symbols",
            "investment_date",
            "amount_of_dollars_to_be_invested",
            "to_be_added_in_portfolio",
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
        tool_log_id = str(uuid.uuid4())
        state["tool_logs"].append(
            {
                "id": tool_log_id,
                "message": "Analyzing user query",
                "status": "processing",
            }
        )
        config.get("configurable").get("emit_event")(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "add",
                        "path": "/tool_logs/-",
                        "value": {
                            "message": "Analyzing user query",
                            "status": "processing",
                            "id": tool_log_id,
                        },
                    }
                ],
            )
        )
        await asyncio.sleep(0)
        model = init_chat_model("gemini-2.5-pro", model_provider="google_genai")
        # tools = [t.dict() for t in state["tools"]]
        messages = []
        for message in state["messages"]:
            match message.role:
                case "user":
                    messages.append(HumanMessage(content=message.content))
                case "system":
                    messages.append(
                        SystemMessage(
                            content=system_prompt.replace(
                                "{PORTFOLIO_DATA_PLACEHOLDER}",
                                json.dumps(state["investment_portfolio"]),
                            )
                        )
                    )
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

        retry_counter = 0
        while True:
            if retry_counter > 3:
                print("retry_counter", retry_counter)
                break

            if messages[-1].type == "human":
                response = await model.bind_tools(
                    [extract_relevant_data_from_user_prompt]
                ).ainvoke(messages, config=config)
            else:
                response = await model.ainvoke(messages, config=config)

            # async for chunk in response:
            #     print(chunk)
            if response.tool_calls:
                tool_calls = [convert_tool_call(tc) for tc in response.tool_calls]
                a_message = AssistantMessage(
                    role="assistant", tool_calls=tool_calls, id=response.id
                )
                state["messages"].append(a_message)
                index = len(state["tool_logs"]) - 1
                config.get("configurable").get("emit_event")(
                    StateDeltaEvent(
                        type=EventType.STATE_DELTA,
                        delta=[
                            {
                                "op": "replace",
                                "path": f"/tool_logs/{index}/status",
                                "value": "completed",
                            }
                        ],
                    )
                )
                await asyncio.sleep(0)
                return
            elif response.content == "" and response.tool_calls == []:
                retry_counter += 1
            else:
                a_message = AssistantMessage(
                    id=response.id, content=response.content, role="assistant"
                )
                state["messages"].append(a_message)
                index = len(state["tool_logs"]) - 1
                config.get("configurable").get("emit_event")(
                    StateDeltaEvent(
                        type=EventType.STATE_DELTA,
                        delta=[
                            {
                                "op": "replace",
                                "path": f"/tool_logs/{index}/status",
                                "value": "completed",
                            }
                        ],
                    )
                )
                await asyncio.sleep(0)
                return
        print("hello")
        a_message = AssistantMessage(
            id=response.id, content=response.content, role="assistant"
        )
        state["messages"].append(a_message)
    except Exception as e:
        print(e)
        a_message = AssistantMessage(id=response.id, content="", role="assistant")
        state["messages"].append(a_message)
        return Command(
            goto="end",
        )
    index = len(state["tool_logs"]) - 1
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "replace",
                    "path": f"/tool_logs/{index}/status",
                    "value": "completed",
                }
            ],
        )
    )
    await asyncio.sleep(0)
    return


async def end_node(state: AgentState, config: RunnableConfig):
    print("inside end node")


async def simulation_node(state: AgentState, config: RunnableConfig):
    print("inside simulation node")
    tool_log_id = str(uuid.uuid4())
    state["tool_logs"].append(
        {"id": tool_log_id, "message": "Gathering stock data", "status": "processing"}
    )
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "add",
                    "path": "/tool_logs/-",
                    "value": {
                        "message": "Gathering stock data",
                        "status": "processing",
                        "id": tool_log_id,
                    },
                }
            ],
        )
    )
    await asyncio.sleep(0)
    arguments = json.loads(state["messages"][-1].tool_calls[0].function.arguments)
    print("arguments", arguments)
    state["investment_portfolio"] = json.dumps(
        [
            {
                "ticker": ticker,
                "amount": arguments["amount_of_dollars_to_be_invested"][index],
            }
            for index, ticker in enumerate(arguments["ticker_symbols"])
        ]
    )
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "replace",
                    "path": f"/investment_portfolio",
                    "value": json.loads(state["investment_portfolio"]),
                }
            ],
        )
    )
    await asyncio.sleep(2)
    tickers = arguments["ticker_symbols"]
    investment_date = arguments["investment_date"]
    current_year = datetime.now().year
    if current_year - int(investment_date[:4]) > 4:
        print("investment date is more than 4 years ago")
        investment_date = f"{current_year - 4}-01-01"
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
    index = len(state["tool_logs"]) - 1
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "replace",
                    "path": f"/tool_logs/{index}/status",
                    "value": "completed",
                }
            ],
        )
    )
    await asyncio.sleep(0)
    return Command(goto="cash_allocation", update=state)


async def cash_allocation_node(state: AgentState, config: RunnableConfig):
    print("inside cash allocation node")
    tool_log_id = str(uuid.uuid4())
    state["tool_logs"].append(
        {"id": tool_log_id, "message": "Allocating cash", "status": "processing"}
    )
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "add",
                    "path": "/tool_logs/-",
                    "value": {
                        "message": "Allocating cash",
                        "status": "processing",
                        "id": tool_log_id,
                    },
                }
            ],
        )
    )
    await asyncio.sleep(2)
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
            # + running_cash
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
    index = len(state["tool_logs"]) - 1
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "replace",
                    "path": f"/tool_logs/{index}/status",
                    "value": "completed",
                }
            ],
        )
    )
    await asyncio.sleep(0)
    return Command(goto="ui_decision", update=state)


async def insights_node(state: AgentState, config: RunnableConfig):
    print("inside insights node")
    tool_log_id = str(uuid.uuid4())
    state["tool_logs"].append(
        {
            "id": tool_log_id,
            "message": "Extracting key insights",
            "status": "processing",
        }
    )
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "add",
                    "path": "/tool_logs/-",
                    "value": {
                        "message": "Extracting key insights",
                        "status": "processing",
                        "id": tool_log_id,
                    },
                }
            ],
        )
    )
    await asyncio.sleep(0)
    args = state.get("be_arguments") or state.get("arguments")
    tickers = args.get("ticker_symbols", [])

    model = init_chat_model("gemini-2.5-pro", model_provider="google_genai")
    response = await model.bind_tools(generate_insights).ainvoke(
        [
            {"role": "system", "content": insights_prompt},
            {"role": "user", "content": tickers},
        ],
        config=config,
    )
    if response.tool_calls:
        args_dict = json.loads(state["messages"][-1].tool_calls[0].function.arguments)

        # Step 2: Add the insights key
        args_dict["insights"] = response.tool_calls[0]["args"]

        # Step 3: Convert back to string
        state["messages"][-1].tool_calls[0].function.arguments = json.dumps(args_dict)
    else:
        state["insights"] = {}
    index = len(state["tool_logs"]) - 1
    config.get("configurable").get("emit_event")(
        StateDeltaEvent(
            type=EventType.STATE_DELTA,
            delta=[
                {
                    "op": "replace",
                    "path": f"/tool_logs/{index}/status",
                    "value": "completed",
                }
            ],
        )
    )
    await asyncio.sleep(0)
    return Command(goto="end", update=state)


def router_function1(state: AgentState, config: RunnableConfig):
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
    workflow.add_node("insights", insights_node)
    workflow.add_node("end", end_node)
    workflow.set_entry_point("chat")
    workflow.set_finish_point("end")

    workflow.add_edge(START, "chat")
    workflow.add_conditional_edges("chat", router_function1)
    workflow.add_edge("simulation", "cash_allocation")
    workflow.add_edge("cash_allocation", "insights")
    workflow.add_edge("insights", "end")
    workflow.add_edge("end", END)
    # from langgraph.checkpoint.memory import MemorySaver
    # graph = workflow.compile(MemorySaver())
    graph = workflow.compile()
    return graph
