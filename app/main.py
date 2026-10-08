"""
FastAPI entrypoint.
"""

from fastapi import FastAPI

from app.telephony.router import router as telephony_router
from app.telephony.audio_bridge import router as audio_bridge_router

app = FastAPI(title="Voice Receptionist")

app.include_router(telephony_router)
app.include_router(audio_bridge_router)


@app.get("/health")
def health():
    return {"status": "ok"}