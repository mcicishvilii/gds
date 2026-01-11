from fastapi import APIRouter, Depends
from ..core.interfaces import IDecisionRepository
from ..data.repositories import YesNoApiRepository

router = APIRouter()

def get_decision_repo() -> IDecisionRepository:
    return YesNoApiRepository()

@router.get("/decision")
async def get_decision(repo: IDecisionRepository = Depends(get_decision_repo)):
    return await repo.fetch_decision()