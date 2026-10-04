"""
OpenAI Realtime API session — GA interface (not the deprecated beta shape).

Beta was fully removed by OpenAI on 2026-05-07. Key GA differences this
file accounts for, confirmed against OpenAI's current docs:
  - No "OpenAI-Beta" header
  - session.update requires session.type = "realtime"
  - Audio format is a nested object: {"type": "audio/pcm", "rate": 24000},
    not a flat string like the old "pcm16"
  - Voice lives at session.audio.output.voice (not top-level session.voice)
  - turn_detection lives under session.audio.input.turn_detection
  - "modalities" renamed to "output_modalities"
  - response.audio.delta renamed to response.output_audio.delta
"""

import asyncio
import base64
import json

import websockets

from app.config import OPENAI_API_KEY
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.tools import TOOL_SCHEMAS, TOOL_FUNCTIONS

REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-realtime"


async def run_session(audio_in_queue: asyncio.Queue, audio_out_queue: asyncio.Queue):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    async with websockets.connect(REALTIME_URL, additional_headers=headers) as ws:
        await ws.send(json.dumps({
            "type": "session.update",
            "session": {
                "type": "realtime",
                "model": "gpt-realtime",
                "output_modalities": ["audio"],
                "instructions": SYSTEM_PROMPT,
                "audio": {
                    "input": {
                        "format": {"type": "audio/pcm", "rate": 24000},
                        "turn_detection": {"type": "server_vad"},
                    },
                    "output": {
                        "format": {"type": "audio/pcm", "rate": 24000},
                        "voice": "marin",
                    },
                },
                "tools": TOOL_SCHEMAS,
                "tool_choice": "auto",
            },
        }))

        async def send_mic_audio():
            while True:
                chunk = await audio_in_queue.get()
                await ws.send(json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": base64.b64encode(chunk).decode("utf-8"),
                }))

        async def handle_events():
            async for raw_message in ws:
                event = json.loads(raw_message)
                event_type = event.get("type")

                if event_type == "response.output_audio.delta":
                    audio_bytes = base64.b64decode(event["delta"])
                    await audio_out_queue.put(audio_bytes)

                elif event_type == "response.function_call_arguments.done":
                    tool_name = event["name"]
                    call_id = event["call_id"]
                    try:
                        args = json.loads(event["arguments"])
                    except (json.JSONDecodeError, TypeError):
                        args = {}

                    func = TOOL_FUNCTIONS.get(tool_name)
                    if func is None:
                        result = {"error": f"Unknown tool '{tool_name}'"}
                    else:
                        try:
                            result = func(**args)
                        except Exception as e:
                            result = {"error": str(e)}

                    await ws.send(json.dumps({
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": json.dumps(result),
                        },
                    }))
                    await ws.send(json.dumps({"type": "response.create"}))

                elif event_type == "error":
                    print(f"Realtime API error: {event}")

                else:
                    # Catch-all so we can see any other event names live —
                    # useful since GA renamed several events and there may
                    # be more we haven't accounted for yet.
                    print(f"[event] {event_type}")

        await asyncio.gather(send_mic_audio(), handle_events())