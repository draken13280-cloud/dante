from fcf.domain.enums import AssetKind
from fcf.publish.base import Capabilities, PublishResult


class TikTokPublisher:
    platform = "tiktok"

    def capabilities(self) -> Capabilities:
        return Capabilities(
            draft=True,
            live=False,
            kinds=frozenset({AssetKind.VIDEO}),
            requires_public_url=False,
            auth="oauth2",
            max_video_s=60,
            notes="video.upload vs video.publish scopes",
        )

    def configured(self) -> bool:
        return True

    async def publish(self, asset, copy, *, live: bool, idem: str) -> PublishResult:
        return PublishResult(status="draft", platform=self.platform, idempotency_key=idem)
