from __future__ import annotations

import io

from fcf.providers.base import BinaryResult, Usage, VideoRequest


class MockVideo:
    name = "mock"

    def estimate_cost(self, req) -> int:
        return 0

    async def generate(self, req: VideoRequest) -> BinaryResult:
        # Minimal ISO BMFF 'ftyp' stub so mime/type QA can run without ffmpeg in unit tests.
        data = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 64
        return BinaryResult(
            data=data,
            mime="video/mp4",
            usage=Usage(provider="mock", model="mock-video"),
            meta={
                "width": req.width,
                "height": req.height,
                "duration_s": req.duration_s,
                "has_audio": True,
                "pix_fmt": "yuv420p",
                "faststart": True,
                "first_frame_luma": 40,
            },
        )
