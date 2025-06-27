from .const import MAX_RETRY_COUNT

MAX_RETRY_ERROR = Exception(f"Max retry reached after {MAX_RETRY_COUNT} attempts")
