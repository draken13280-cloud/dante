from pydantic import BaseModel

from fcf.domain.enums import Channel


class Recipe(BaseModel):
    width: int
    height: int
    fps: int = 30
    max_duration: int | None = None
    loudness_lufs: float = -14.0
    true_peak_db: float = -1.0
    music_db: float = -18.0
    subtitles: str | None = None
    watermark: bool = True
    container: str = "mp4"
    v_bitrate: str = "6M"


RECIPES = {
    Channel.TIKTOK: Recipe(width=1080, height=1920, max_duration=30, subtitles="burn"),
    Channel.IG_REEL: Recipe(width=1080, height=1920, max_duration=45, subtitles="burn"),
    Channel.IG_POST: Recipe(width=1080, height=1350, watermark=False, container="jpg"),
    Channel.SHOPIFY: Recipe(width=2048, height=2048, watermark=False, container="webp"),
    Channel.EMAIL: Recipe(width=1200, height=600, watermark=False, container="jpg"),
}
