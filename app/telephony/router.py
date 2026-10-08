"""
Telnyx Call Control webhook — handles inbound call events.

Flow: inbound call arrives -> call.initiated webhook fires -> we tell
Telnyx to answer the call AND start bidirectional media streaming to our
own WebSocket (/media-stream), where the actual audio bridging happens.
"""

import httpx
from fastapi import APIRouter, Request

from app.config import TELNYX_API_KEY, PUBLIC_WS_URL

router = APIRouter()

TELNYX_API_BASE = "https://api.telnyx.com/v2"


@router.post("/voice/inbound")
async def telnyx_webhook(request: Request):
    payload = await request.json()
    event = payload.get("data", {})
    event_type = event.get("event_type")

    if event_type == "call.initiated":
        call_control_id = event["payload"]["call_control_id"]

        headers = {
            "Authorization": f"Bearer {TELNYX_API_KEY}",
            "Content-Type": "application/json",
        }
        body = {
            "stream_url": f"{PUBLIC_WS_URL}/media-stream",
            "stream_track": "both_tracks",
            "stream_bidirectional_mode": "rtp",
            "stream_bidirectional_codec": "PCMU",
        }

        async with httpx.AsyncClient() as client:
            await client.post(
                f"{TELNYX_API_BASE}/calls/{call_control_id}/actions/answer",
                headers=headers,
                json=body,
                timeout=10,
            )

    # Always 200 quickly — Telnyx expects a fast ack, same discipline as
    # Meta's webhook SLA in the WhatsApp project.
    return {"status": "ok"}