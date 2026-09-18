from pydantic import BaseModel, Field

from fcf.domain.enums import Channel


class ToneSpec(BaseModel):
    voice: str
    person: str = "second"
    reading_level_max: float = 9.0
    banned_phrases: list[str] = Field(default_factory=list)
    preferred_phrases: list[str] = Field(default_factory=list)
    emoji_allowed: bool = True


class ClaimsPolicy(BaseModel):
    forbid_absolute: bool = True
    forbid_health_claims: bool = True
    sustainability_requires_cert: bool = True
    allowed_certifications: list[str] = Field(default_factory=lambda: ["GOTS", "OEKO-TEX", "GRS"])
    forbid_competitor_mentions: list[str] = Field(default_factory=list)


class ChannelPolicy(BaseModel):
    title_max: int = 70
    body_max: int = 2000
    hashtags_min: int = 0
    hashtags_max: int = 0
    emoji_max: int = 0
    cta_required: bool = False
    aspect: str | None = None
    min_width: int = 1080
    duration_s: tuple[int, int] | None = None
    subtitles: str | None = None
    watermark: bool = True
    loudness_lufs: float = -14.0
    alt_text_required: bool = False


class BrandKit(BaseModel):
    slug: str
    name: str
    tone: ToneSpec
    palette_hex: list[str]
    palette_tolerance_de: float = 18.0
    logo_uri: str | None = None
    font_uri: str | None = None
    claims: ClaimsPolicy = Field(default_factory=ClaimsPolicy)
    channels: dict[Channel, ChannelPolicy]
    locales: list[str] = Field(default_factory=lambda: ["en"])
    music_uri: str | None = None
