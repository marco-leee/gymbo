from .const import MAX_RETRY_COUNT


class MaxRetryError(Exception):
    def __init__(
        self, message: str = f"Max retry reached after {MAX_RETRY_COUNT} attempts"
    ):
        self.message = message
        super().__init__(self.message)
