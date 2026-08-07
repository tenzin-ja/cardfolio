from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel,ConfigDict, Field

#Restricts API input to the same condtion values permitted by the database
CardCondition = Literal [
    "near_mint",
    "lightly_played",
    "moderately_played",
    "heavily_played",
    "damaged",
    "unknown",
]

#Defines and validates the JSON needed to create an owned collection item
class CollectionItemCreate(BaseModel):
    # A postive number is required here, but the route will still need to verify
    # that a CardVariant with this ID actually exists
    card_variant_id: int = Field(gt = 0)

    condition: CardCondition

    #These defaults match the SQLAlchemy model. Repeating the validatino here 
    #lets the API return a clear 422 response before reaching the database
    quantity: int = Field(default = 1, gt = 0)

    # Decimal is used for money because float can introduce rounding errors.
    # This field stores the price of one card, not the total lot price
    purchase_price_per_card: Decimal | None = Field(
        default = None, 
        ge=0,
        max_digits = 10,
        decimal_places = 2,
    )

    # V1 defaults to US dollars. Requiring three characters follows standard 
    # currency codes such as USD,CAD, and EUR
    purchase_currency: str = Field(
        default = "USD",
        min_length = 3, 
        max_length = 3,
    )

    # We only need the calender day of purchase, not an exact time
    purchase_date: date | None = None

    notes: str | None = None

#The response contains every creation field plus the database generated ID
class CollectionItemResponse(CollectionItemCreate):
    id: int

    # Allos the Pydantic to build this reponse by reading attributes from a 
    #SQLAlchemy CollectionItem object instead of requiring a dict
    model_config = ConfigDict(from_attributes = True)
