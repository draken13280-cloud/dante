class FCFError(Exception):
    pass


class ProviderError(FCFError):
    def __init__(self, provider: str, message: str):
        self.provider = provider
        super().__init__(f"{provider}: {message}")


class TransientProviderError(ProviderError):
    pass


class BudgetExceeded(FCFError):
    pass


class Unsupported(FCFError):
    pass


class PostProdError(FCFError):
    pass
