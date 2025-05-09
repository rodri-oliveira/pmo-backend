from pydantic import BaseModel

class ItemDTO(BaseModel):
    id: int
    description: str

class ItemCreateDTO(BaseModel):
    description: str

class ItemUpdateDTO(BaseModel):
    description: str

