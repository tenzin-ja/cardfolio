from pydantic import BaseModel, ConfigDict

class CardBase(BaseModel):
    name:str | None = None
    rarity: str | None = None
    condition: str | None = None
    price: float | None = None

    '''User sends a Json -> Cardcreate checks the incoming data-> Card Model turns it into a dataBase Object
       SQLAlchemy saves it to SQLite - > CardResponse controls what gets sent back.
    '''
class CardCreate(CardBase):
    pass

class CardResponse(CardBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
   