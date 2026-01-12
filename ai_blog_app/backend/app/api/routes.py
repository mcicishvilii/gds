from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ..core import security
from ..data.repositories import YesNoApiRepository # Check your import path
from ..core.interfaces import IDecisionRepository

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- ADD THIS FUNCTION ---
def get_decision_repo() -> IDecisionRepository:
    return YesNoApiRepository()

HASHED_DB_PASSWORD = security.get_password_hash("password123")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "admin" or not security.verify_password(form_data.password, HASHED_DB_PASSWORD):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = security.create_access_token(data={"sub": form_data.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "username": form_data.username 
    }

@router.get("/decision")
async def get_decision(
    token: str = Depends(oauth2_scheme), 
    repo: IDecisionRepository = Depends(get_decision_repo)
):
    return await repo.fetch_decision()

