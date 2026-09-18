from fcf.providers.base import Usage


class MockVision:
    name = "mock"

    def estimate_cost(self, req) -> int:
        return 0

    async def inspect(self, req) -> dict:
        return {
            "garment_match": 0.9,
            "artifacts": False,
            "text_in_image": False,
            "brand_safety": True,
            "usage": Usage(provider="mock").model_dump(),
        }
