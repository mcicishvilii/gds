import httpx
from ..core.entities import Decision
from ..core.interfaces import IDecisionRepository

class YesNoApiRepository(IDecisionRepository):
    def __init__(self):
        self.url = "https://yesno.wtf/api"

    async def fetch_decision(self) -> Decision:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(self.url)
            data = response.json()
            return Decision(
                answer=data["answer"],
                image=data["image"]
            )