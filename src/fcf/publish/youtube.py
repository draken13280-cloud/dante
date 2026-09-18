from fcf.domain.enums import AssetKind
from fcf.publish.base import Capabilities, PublishResult


class YouTubePublisher:
    platform = "youtube_shorts"

    def capabilities(self) -> Capabilities:
        return Capabilities(
            draft=False,
            live=False,
            kinds=frozenset({AssetKind.VIDEO}),
            requires_public_url=False,
            auth="oauth2",
            max_video_s=60,
            notes=(
                "YouTube Data API requires OAuth2 user consent with youtube.upload scope. "
                "API-key auth cannot upload video. Not wired up."
            ),
        )

    def configured(self) -> bool:
        return False

    async def publish(self, *a, **kw) -> PublishResult:
        return PublishResult(status="unsupported", platform=self.platform, error=self.capabilities().notes)
