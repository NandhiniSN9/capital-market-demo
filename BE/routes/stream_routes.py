"""SSE streaming endpoint — proxies agent response tokens to the frontend."""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import UUID4, BaseModel

from BE.models.enums import AnalystType, ScenarioType
from BE.services.dependencies import get_stream_service
from BE.services.stream_service import StreamService
from BE.utils.validators import validate_uuid

router = APIRouter(tags=["streaming"])


class StreamMessageRequest(BaseModel):
    """Request body for the streaming endpoint."""
    content: str
    analyst_type: AnalystType
    scenario_type: ScenarioType
    session_id: Optional[UUID4] = None
    session_title: Optional[str] = None


@router.post("/chats/{chat_id}/stream")
async def stream_message(
    chat_id: str,
    request: StreamMessageRequest,
    stream_service: StreamService = Depends(get_stream_service),
):
    """Stream agent response as Server-Sent Events with keepalive heartbeats."""
    validate_uuid(chat_id)

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()
        done_flag = asyncio.Event()

        async def _produce():
            """Run the agent stream and push events to the queue."""
            try:
                async for event in stream_service.stream_deal_response(
                    chat_id=chat_id,
                    content=request.content,
                    analyst_type=request.analyst_type.value,
                    scenario_type=request.scenario_type.value,
                    session_id=str(request.session_id) if request.session_id else None,
                    session_title=request.session_title,
                ):
                    await queue.put(event)
            except Exception as exc:
                await queue.put({"type": "error", "content": str(exc)[:500]})
            finally:
                done_flag.set()

        # Start the producer in the background
        producer = asyncio.create_task(_produce())

        # Consume events from the queue, sending heartbeats if idle
        while not done_flag.is_set() or not queue.empty():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=2.0)
                yield f"data: {json.dumps(event, default=str)}\n\n"
            except asyncio.TimeoutError:
                # Send a heartbeat comment to keep the connection alive
                yield ": heartbeat\n\n"

        # Drain any remaining events
        while not queue.empty():
            event = queue.get_nowait()
            yield f"data: {json.dumps(event, default=str)}\n\n"

        await producer

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
