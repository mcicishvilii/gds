from pydantic import BaseModel

class Decision(BaseModel):
    answer: str
    image: str