from abc import ABC, abstractmethod
from .entities import Decision

class IDecisionRepository(ABC):
    @abstractmethod
    async def fetch_decision(self) -> Decision:
        pass