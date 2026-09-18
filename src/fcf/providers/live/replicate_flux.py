from fcf.core.errors import ProviderError, TransientProviderError
from fcf.providers.base import BinaryResult, ImageRequest, Usage


class FluxAdapter:
    name = "replicate_flux"
    MODEL = "black-forest-labs/flux-1.1-pro"
    COST_PER_IMAGE_CENTS = 4

    def estimate_cost(self, req: ImageRequest) -> int:
        return self.COST_PER_IMAGE_CENTS

    async def generate(self, req: ImageRequest) -> BinaryResult:
        raise ProviderError(self.name, "live adapter not invoked in mock mode")
