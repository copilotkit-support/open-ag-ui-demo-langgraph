from fastapi import FastAPI
from fastapi.responses import StreamingResponse  # For streaming responses
import uuid
from typing import Any
import os
import uvicorn
import asyncio
from ag_ui.core import (
    RunAgentInput,
    StateSnapshotEvent,
    EventType,
    RunStartedEvent,
    RunFinishedEvent,
    TextMessageStartEvent,
    TextMessageEndEvent,
    TextMessageContentEvent,
    ToolCallStartEvent,
    ToolCallEndEvent,
    ToolCallArgsEvent,
    StateDeltaEvent
)
from ag_ui.encoder import EventEncoder
from stock_analysis import agent_graph
from copilotkit import CopilotKitState

app = FastAPI()


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
    investment_summary : dict
    tool_logs : list

@app.post("/langgraph-agent")
async def langgraph_agent(input_data: RunAgentInput):
    try:

        async def event_generator():
            encoder = EventEncoder()
            event_queue = asyncio.Queue()

            def emit_event(event):
                event_queue.put_nowait(event)

            message_id = str(uuid.uuid4())

            yield encoder.encode(
                RunStartedEvent(
                    type=EventType.RUN_STARTED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id,
                )
            )

            yield encoder.encode(
                StateSnapshotEvent(
                    type=EventType.STATE_SNAPSHOT, 
                    snapshot={
                        "available_cash": input_data.state["available_cash"],
                        "investment_summary" : input_data.state["investment_summary"],
                        "investment_portfolio" : input_data.state["investment_portfolio"],
                        "tool_logs" : []
                    }
                )
            )
            state = AgentState(
                tools=input_data.tools,
                messages=input_data.messages,
                be_stock_data=None,
                be_arguments=None,
                available_cash=input_data.state["available_cash"],
                investment_portfolio=input_data.state["investment_portfolio"],
                tool_logs=[]
            )
            agent = await agent_graph()

            agent_task = asyncio.create_task(
                agent.ainvoke(
                    state, config={"emit_event": emit_event, "message_id": message_id}
                )
            )
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield encoder.encode(event)
                except asyncio.TimeoutError:
                    # Check if the agent is done
                    if agent_task.done():
                        break

            yield encoder.encode(
            StateDeltaEvent(
                type=EventType.STATE_DELTA,
                delta=[
                    {
                        "op": "replace",
                        "path": "/tool_logs",
                        "value": []
                    }
                ]
            )
            )
            if state["messages"][-1].role == "assistant":
                if state["messages"][-1].tool_calls:
                    # for tool_call in state['messages'][-1].tool_calls:
                    yield encoder.encode(
                        ToolCallStartEvent(
                            type=EventType.TOOL_CALL_START,
                            tool_call_id=state["messages"][-1].tool_calls[0].id,
                            toolCallName=state["messages"][-1]
                            .tool_calls[0]
                            .function.name,
                        )
                    )

                    yield encoder.encode(
                        ToolCallArgsEvent(
                            type=EventType.TOOL_CALL_ARGS,
                            tool_call_id=state["messages"][-1].tool_calls[0].id,
                            delta=state["messages"][-1]
                            .tool_calls[0]
                            .function.arguments,
                        )
                    )

                    yield encoder.encode(
                        ToolCallEndEvent(
                            type=EventType.TOOL_CALL_END,
                            tool_call_id=state["messages"][-1].tool_calls[0].id,
                        )
                    )
                else:
                    yield encoder.encode(
                        TextMessageStartEvent(
                            type=EventType.TEXT_MESSAGE_START,
                            message_id=message_id,
                            role="assistant",
                        )
                    )

                    # Only send content event if content is not empty
                    if state["messages"][-1].content:
                        content = state["messages"][-1].content
                        # Split content into 100 parts
                        n_parts = 100
                        part_length = max(1, len(content) // n_parts)
                        parts = [content[i:i+part_length] for i in range(0, len(content), part_length)]
                        # If splitting results in more than 5 due to rounding, merge last parts
                        if len(parts) > n_parts:
                            parts = parts[:n_parts-1] + [''.join(parts[n_parts-1:])]
                        for part in parts:
                            yield encoder.encode(
                                TextMessageContentEvent(
                                    type=EventType.TEXT_MESSAGE_CONTENT,
                                    message_id=message_id,
                                    delta=part,
                                )
                            )
                            await asyncio.sleep(0.05)
                    else:
                        yield encoder.encode(
                            TextMessageContentEvent(
                                type=EventType.TEXT_MESSAGE_CONTENT,
                                message_id=message_id,
                                delta="Something went wrong! Please try again.",
                            )
                        )
                    
                    yield encoder.encode(
                        TextMessageEndEvent(
                            type=EventType.TEXT_MESSAGE_END,
                            message_id=message_id,
                        )
                    )

            yield encoder.encode(
                RunFinishedEvent(
                    type=EventType.RUN_FINISHED,
                    thread_id=input_data.thread_id,
                    run_id=input_data.run_id,
                )
            )

    except Exception as e:
        print(e)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def main():
    """Run the uvicorn server."""
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )


if __name__ == "__main__":
    main()
