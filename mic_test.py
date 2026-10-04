"""
Standalone mic test for the Realtime session — talk to the receptionist
through your laptop's microphone, no telephony involved yet.

Run with: python mic_test.py
(from project root, venv activated)

Requires: pip install sounddevice numpy websockets
"""

import asyncio
import numpy as np
import sounddevice as sd

from app.realtime.session import run_session

SAMPLE_RATE = 24000  # Realtime API expects 24kHz pcm16
BLOCK_SIZE = 2400     # 100ms chunks


async def main():
    audio_in_queue = asyncio.Queue()
    audio_out_queue = asyncio.Queue()

    loop = asyncio.get_event_loop()

    def mic_callback(indata, frames, time_info, status):
        pcm16 = (indata[:, 0] * 32767).astype(np.int16).tobytes()
        loop.call_soon_threadsafe(audio_in_queue.put_nowait, pcm16)

    async def play_audio():
        with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as out_stream:
            while True:
                chunk = await audio_out_queue.get()
                audio_array = np.frombuffer(chunk, dtype=np.int16)
                out_stream.write(audio_array)

    print("Listening... speak to your receptionist (Ctrl+C to stop)")

    with sd.InputStream(
        samplerate=SAMPLE_RATE, channels=1, dtype="float32",
        blocksize=BLOCK_SIZE, callback=mic_callback,
    ):
        await asyncio.gather(
            run_session(audio_in_queue, audio_out_queue),
            play_audio(),
        )


if __name__ == "__main__":
    asyncio.run(main())
