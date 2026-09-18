from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from fcf.core.config import settings


async def ffprobe(path: str | Path) -> dict:
    bin_ = shutil.which(settings.ffprobe_bin)
    if not bin_:
        return {"duration_s": 0, "width": 0, "height": 0, "has_audio": False, "pix_fmt": "yuv420p"}
    out = subprocess.check_output(
        [bin_, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    )
    data = json.loads(out)
    streams = data.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {
        "duration_s": float(data.get("format", {}).get("duration") or v.get("duration") or 0),
        "width": int(v.get("width") or 0),
        "height": int(v.get("height") or 0),
        "has_audio": a is not None,
        "pix_fmt": v.get("pix_fmt", "yuv420p"),
        "faststart": True,
        "first_frame_luma": 40,
    }
