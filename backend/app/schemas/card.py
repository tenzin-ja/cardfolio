from pydantic import BaseModel, ConfigDict,Field

'''
The new Field rules mean:

name must contain at least 1 character
name cannot exceed 100 characters
rarity and condition cannot exceed 50 characters
price cannot be negative'''

class CardBase(BaseModel):
    #Newly created card must have a name
    name:str = Field(min_length = 1, max_length = 100)
    rarity: str | None = Field(default = None, max_length = 50)
    condition: str | None = Field(default = None, max_length = 50)
    price: float | None = Field(default = None, ge = 0)

    '''User sends a Json -> Cardcreate checks the incoming data-> Card Model turns it into a dataBase Object
       SQLAlchemy saves it to SQLite - > CardResponse controls what gets sent back.
    '''
class CardCreate(CardBase):
    pass

class CardUpdate(CardBase):
    #Everything is optional, since user can update any value
    name: str | None = Field(default=None, min_length=1, max_length=100)
    rarity: str | None = Field(default=None, max_length=50)
    condition: str | None = Field(default=None, max_length=50)
    price: float | None = Field(default=None, ge=0)


class CardResponse(CardBase):
    id: int

    model_config = ConfigDict(from_attributes=True)