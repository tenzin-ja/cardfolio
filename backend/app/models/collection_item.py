from sqlalchemy import(
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    Date,
    Text
)

from app.db.database import Base

class CollectionItem(Base):
    __tablename__ = "collection_items"

    id = Column(Integer, primary_key = True)
    card_variant_id = Column(Integer, ForeignKey("card_variants.id"), index = True, nullable = False)

    condition = Column(String(30), nullable = False)
    quantity = Column(Integer,  default = 1, nullable = False)
    purchase_price_per_card = Column(Numeric(10,2), nullable = True)
    purchase_currency = Column(String(3), default = "USD", nullable=False)
    purchase_date = Column(Date(), nullable = True)
    notes = Column(Text(), nullable = True)