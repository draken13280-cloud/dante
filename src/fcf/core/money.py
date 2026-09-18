from fcf.core.errors import BudgetExceeded


class Budget:
    def __init__(self, limit_cents: int, spent_cents: int = 0):
        self.limit = limit_cents
        self.spent = spent_cents
        self.reserved = 0

    @property
    def available(self) -> int:
        return self.limit - self.spent - self.reserved

    def reserve(self, cents: int) -> None:
        if cents > self.available:
            raise BudgetExceeded(f"need {cents}c, available {self.available}c")
        self.reserved += cents

    def commit(self, actual: int, reserved: int) -> None:
        self.reserved -= reserved
        self.spent += actual

    def release(self, reserved: int) -> None:
        self.reserved -= reserved
