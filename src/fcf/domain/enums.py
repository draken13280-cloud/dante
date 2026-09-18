from enum import IntEnum, StrEnum


class Channel(StrEnum):
    SHOPIFY = "shopify"
    TIKTOK = "tiktok"
    IG_REEL = "instagram_reel"
    IG_POST = "instagram_post"
    EMAIL = "email"


class AssetKind(StrEnum):
    COPY = "copy"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    SUBTITLE = "subtitle"


class Stage(IntEnum):
    CONTEXT = 0
    TEXT = 1
    MEDIA = 2
    VIDEO = 3
    POSTPROD = 4


STAGE_BY_KIND = {
    AssetKind.COPY: Stage.TEXT,
    AssetKind.IMAGE: Stage.MEDIA,
    AssetKind.AUDIO: Stage.MEDIA,
    AssetKind.VIDEO: Stage.VIDEO,
    AssetKind.SUBTITLE: Stage.POSTPROD,
}


class Severity(StrEnum):
    BLOCKER = "blocker"
    MAJOR = "major"
    MINOR = "minor"
