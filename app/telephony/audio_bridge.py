"""
WebSocket bridge between a live Telnyx call and the OpenAI Realtime
session. Telnyx sends/receives PCMU (G.711 mu-law) audio frames as JSON
"media" events; OpenAI Realtime accepts/returns the same codec directly
(audio_format={"type": "audio/pcmu"}), so this is a thin relay — no
resampling needed, just reshaping the message envelopes.
"""

import asyncio
import base64
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.session import run_session

router = APIRouter()

TELEPHONY_AUDIO_FORMAT = {"type": "audio/pcmu"}


@router.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    await websocket.accept()

    audio_in_queue = asyncio.Queue()   # caller audio -> Realtime
    audio_out_queue = asyncio.Queue()  # Realtime audio -> caller

    telnyx_stream_id = None

    async def receive_from_telnyx():
        nonlocal telnyx_stream_id
        try:
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data.get("event") == "start":
                    telnyx_stream_id = data["stream_id"]

                elif data.get("event") == "media":
                    payload_b64 = data["media"]["payload"]
                    audio_bytes = base64.b64decode(payload_b64)
                    await audio_in_queue.put(audio_bytes)

                elif data.get("event") == "stop":
                    break
        except WebSocketDisconnect:
            pass

    async def send_to_telnyx():
        while True:
            chunk = await audio_out_queue.get()
            if telnyx_stream_id is None:
                continue  # haven't received Telnyx's start event yet
            await websocket.send_text(json.dumps({
                "event": "media",
                "stream_id": telnyx_stream_id,
                "media": {"payload": base64.b64encode(chunk).decode("utf-8")},
            }))

    await asyncio.gather(
        receive_from_telnyx(),
        send_to_telnyx(),
        run_session(audio_in_queue, audio_out_queue, audio_format=TELEPHONY_AUDIO_FORMAT),
    )