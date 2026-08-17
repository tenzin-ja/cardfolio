
from sqlalchemy.orm import relationship

from app.db.database import Base
#This imports Python’s timestamp tools, used to create a value
from datetime import datetime, timezone
#Datetime here imports SQLAlchemy’s database column type
from sqlalchemy import(
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)

class PriceSnapshot(Base):
    """
    Stores one historical market-price observation for one card variant.
    
    CardVariant keeps the latest cached price for fast display.
    PriceSnapshot keeps the historical observations needed to draw a price chart.
    """
    __tablename__ = "price_snapshots"

    __table_args__ = (
        # Protects against negative prices even when data is inserted outside 
        # the API's Pydantic validation.
        CheckConstraint(
            "market_price >= 0",
            name = "ck_price_snapshots_market_price_nonnegative", 
        ),

        # Created a combined database index on the columns, card_variant_id and observed_at
        # Optimizes the query that price chart will use.
        Index(
            "ix_price_snapshots_card_variant_id_observed_at",
            "card_variant_id",
            "observed_at"
        ),
    )

    id = Column(Integer, primary_key = True)

    # Every obseration belongs to one specific finish, such as holofoil. 
    # If that shared variant is deleted, its now unusable history is deleted too.

    card_variant_id = Column(
        Integer, 
        ForeignKey("card_variants.id", ondelete = "CASCADE"),
        nullable = False,
    )

    #Numeric is used instead of Float so monetary values remain exact. 
    market_price = Column(Numeric(10,2), nullable = False)
    currency = Column(String(3), nullable = False, default = "USD")

    # Records where the observation originated, such as "tcgplayer"
    source = Column(String(50), nullable = False)

    # The lambda is evaluated for every new row. Calling datetime.now() directly 
    # here would evaluate it only once when Python imports this files.
    observed_at = Column(
        DateTime(timezone = True),
        nullable = False,
        default = lambda: datetime.now(timezone.utc),
    )

    #Allows snapshot.card_variant to get the associated CardVariant. 
    card_variant = relationship(
    "CardVariant",
    back_populates="price_snapshots",
    )