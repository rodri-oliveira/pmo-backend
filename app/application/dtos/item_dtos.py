from pydantic import BaseModel

class ItemDTO(BaseModel):
    # campos...
    model_config = {'from_attributes': True}

class ItemCreateDTO(BaseModel):
    description: str

class ItemUpdateDTO(BaseModel):
    description: str

