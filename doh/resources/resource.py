from pydantic import BaseModel


class Resource(BaseModel):
    class Config:
        arbitrary_types_allowed = True
