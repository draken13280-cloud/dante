from __future__ import annotations

import io
import math
import struct
import wave

from fcf.providers.base import BinaryResult, TTSRequest, Usage


class MockTTS:
    name = "mock"

    def estimate_cost(self, req) -> int:
        return 0

    async def generate(self, req: TTSRequest) -> BinaryResult:
        words = max(1, len(req.text.split()))
        duration = max(1.0, words / 2.6)
        sr, amp = 24000, 6000
        frames = bytearray()
        for n in range(int(sr * duration)):
            t = n / sr
            env = 0.5 + 0.5 * math.sin(2 * math.pi * 3.1 * t)
            s = int(amp * env * math.sin(2 * math.pi * 180 * t))
            frames += struct.pack("<h", s)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(bytes(frames))
        return BinaryResult(
            data=buf.getvalue(),
            mime="audio/wav",
            usage=Usage(provider="mock", model="mock-tts"),
            meta={"duration_s": duration, "lufs": -14.0, "true_peak": -1.2, "rms_db": -20, "lead_silence_s": 0.05},
        )
