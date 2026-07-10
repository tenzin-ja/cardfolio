from pydantic import BaseModel, ConfigDict


class CardBase(BaseModel):
    #Newly created card must have a name
    name:str
    rarity: str | None = None
    condition: str | None = None
    price: float | None = None

    '''User sends a Json -> Cardcreate checks the incoming data-> Card Model turns it into a dataBase Object
       SQLAlchemy saves it to SQLite - > CardResponse controls what gets sent back.
    '''
class CardCreate(CardBase):
    pass

class CardUpdate(CardBase):
    #Everything is optional, since user can update any value
    name: str | None= None
    rarity: str | None = None
    condition: str | None = None
    price: float | None = None

class CardResponse(CardBase):
    id: int

    model_config = ConfigDict(from_attributes=True)