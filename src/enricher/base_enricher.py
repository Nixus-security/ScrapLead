from abc import ABC, abstractmethod
from typing import Dict, Optional

class BaseEnricher(ABC):
    @abstractmethod
    async def enrich(self, lead: dict) -> Optional[dict]:
        pass
    
    def parse_name(self, full_name: str) -> tuple[str, str]:
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[-1]