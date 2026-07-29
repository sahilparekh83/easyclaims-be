from datetime import datetime, timezone
from typing import Callable


def generate_unique_code(prefix: str, exists_fn: Callable[[str], bool], digits: int = 6) -> str:
    """Generate a unique '{PREFIX}-{year}-{sequence}' code, e.g. 'POL-2026-000042'.

    The sequence resets to 1 each new year. exists_fn(code) should return True
    if that exact code string is already taken, so the loop can skip ahead
    past any collision.
    """
    year = datetime.now(timezone.utc).year
    n = 1
    while True:
        code = f"{prefix}-{year}-{n:0{digits}d}"
        if not exists_fn(code):
            return code
        n += 1
