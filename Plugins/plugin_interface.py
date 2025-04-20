from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IPlugin(ABC):
    name: str = None

    priority: int = 0

    dependencies: List[str] = []

    enabled_by_default: bool = True

    @classmethod
    @abstractmethod
    async def create(cls, **kwargs) -> Any:
        pass

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {}

    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> bool:
        return True