from sqlalchemy import(
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    Date,
    Text,
    CheckConstraint
)
from sqlalchemy.orm import relationship

from app.db.database import Base

class CollectionItem(Base):
    __tablename__ = "collection_items"

    __table_args__ = (
        CheckConstraint(
            "condition IN ('near_mint', 'lightly_played', "
            "'moderately_played', 'heavily_played', "
            "'damaged', 'unknown')",
            name="ck_collection_items_condition_allowed",
        ),
    CheckConstraint(
    "quantity > 0",
    name="ck_collection_items_quantity_positive",
    ),
    CheckConstraint(
        "purchase_price_per_card >= 0",
        name="ck_collection_items_purchase_price_nonnegative",
    ),
    )

    id = Column(Integer, primary_key = True)
    card_variant_id = Column(Integer, ForeignKey("card_variants.id"), index = True, nullable = False)

    condition = Column(String(30), nullable = False)
    quantity = Column(Integer,  default = 1, nullable = False)
    purchase_price_per_card = Column(Numeric(10,2), nullable = True)
    purchase_currency = Column(String(3), default = "USD", nullable=False)
    purchase_date = Column(Date(), nullable = True)
    notes = Column(Text(), nullable = True)

    card_variant = relationship(
        "CardVariant",
        back_populates="collection_items",
    )