from fcf.domain.enums import AssetKind
from fcf.publish.base import Capabilities, PublishResult


class ShopifyPublisher:
    platform = "shopify"

    def capabilities(self) -> Capabilities:
        return Capabilities(
            draft=True,
            live=True,
            kinds=frozenset({AssetKind.COPY, AssetKind.IMAGE}),
            requires_public_url=False,
            auth="api_key",
            notes="Admin API token; idempotency by SKU",
        )

    def configured(self) -> bool:
        return True

    async def publish(self, asset, copy, *, live: bool, idem: str) -> PublishResult:
        return PublishResult(
            status="live" if live else "draft",
            platform=self.platform,
            external_id=idem,
            idempotency_key=idem,
        )
