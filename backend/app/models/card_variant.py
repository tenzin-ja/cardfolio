from sqlalchemy import(
    Column,
    Integer,
    String,
    UniqueConstraint,
    ForeignKey,
    DateTime,
    Numeric
)
from app.db.database import Base

from sqlalchemy.orm import relationship

class CardVariant(Base):
    __tablename__ = "card_variants"

    __table_args__ = (
        UniqueConstraint(
            "catalog_card_id",
            "variant_key",
            name = "uq_card_variants_catalog_card_id_variant_key"
        ),
    )

    id = Column(Integer, primary_key = True)
    catalog_card_id = Column(Integer, ForeignKey("catalog_cards.id"), nullable = False, index = True)
    variant_key = Column(String(50), nullable = False)
    market_price = Column(Numeric(10,2), nullable = True)
    market_price_source = Column(String(50), nullable = True)
    market_price_updated_at = Column(DateTime(timezone = True), nullable = True)
    currency = Column(String(3),nullable = False, default = "USD")

    catalog_card = relationship(
        "CatalogCard",
        back_populates="variants",
    )

    collection_items = relationship(
    "CollectionItem",
    back_populates="card_variant",
    )

    