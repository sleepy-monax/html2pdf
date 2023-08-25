from typing import Optional

def mmtoinch(mm: Optional[float]) -> Optional[float]:
    if mm is None:
        return None
    return mm / 25.4
