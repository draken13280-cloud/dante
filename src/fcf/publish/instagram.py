from fcf.domain.enums import AssetKind
from fcf.publish.base import Capabilities, PublishResult


class InstagramPublisher:
    platform = "instagram"

    def capabilities(self) -> Capabilities:
        return Capabilities(
            draft=True,
            live=False,
            kinds=frozenset({AssetKind.IMAGE, AssetKind.VIDEO}),
            requires_public_url=True,
            auth="oauth2",
            notes="Graph API requires a public URL",
        )

    def configured(self) -> bool:
        return True

    async def publish(self, asset, copy, *, live: bool, idem: str) -> PublishResult:
        return PublishResult(status="draft", platform=self.platform, idempotency_key=idem)
