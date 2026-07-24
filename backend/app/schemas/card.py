from pydantic import BaseModel, ConfigDict, Field, field_validator
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

    @field_validator("name")
    @classmethod
    def reject_null_name(cls, value: str | None) -> str:
        """
        PATCH may omit the name, but explicitly sending null would erase
        a value that every saved card is required to have.
        """
        if value is None:
            raise ValueError("Name cannot be null")

        return value

class CardResponse(CardBase):
    id: int

    model_config = ConfigDict(from_attributes=True)