# Creating a database table that will store the fields of a card

from sqlalchemy import Column, Integer, String, Float
from app.db.database import Base


# Creating a Card class that inherits properties from Base
# Card model is how a card will be stored in SQLite
class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True, index=True)
    rarity = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    price = Column(Float, nullable=True)