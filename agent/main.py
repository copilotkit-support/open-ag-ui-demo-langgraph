
from fastapi import FastAPI
from fastapi.responses import StreamingResponse  # For streaming responses
from pydantic import BaseModel
import uuid
from typing import Dict, List, Any, Optional
import os
import uvicorn
import asyncio
from ag_ui.core import (RunAgentInput, Message, EventType, RunStartedEvent, RunFinishedEvent, TextMessageStartEvent, TextMessageEndEvent, TextMessageContentEvent)
from ag_ui.encoder import EventEncoder

app = FastAPI()


@app.post("/langgraph-agent")
async def langgraph_agent(input_data : RunAgentInput):
    async def event_generator():
        
        encoder = EventEncoder()
        event_queue = asyncio.Queue()

        def emit_event(event):
            event_queue.put_nowait(event)
            
        query = input_data.messages[-1].content
        message_id = str(uuid.uuid4()) 
        
        yield encoder.encode(
          RunStartedEvent(
            type=EventType.RUN_STARTED,
            thread_id=input_data.thread_id,
            run_id=input_data.run_id
          )
        )
            
        yield TextMessageStartEvent(
            run_id=input_data.run_id,
            message_id=str(uuid.uuid4()),
            content="Hello, how can I help you today?"
        )
        yield TextMessageContentEvent(
            run_id=input_data.run_id,
            message_id=str(uuid.uuid4()),
            content="I'm here to help you with your questions."
        )
        yield TextMessageEndEvent(
            run_id=input_data.run_id,
            message_id=str(uuid.uuid4()),
            content="Thank you for your question. I'm here to help you with your questions."
        )
        yield RunFinishedEvent(
            run_id=input_data.run_id,
            status="completed"
        )
        
        
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )