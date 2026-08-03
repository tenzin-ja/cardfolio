from sqlalchemy import(
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)

from app.db.database import Base

class CatalogCard(Base):
    __tablename__ = "catalog_cards"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_card_id",
            name = "uq_catalog_cards_provider_card_id",
        ),
    )

    id = Column(Integer, primary_key = True)

    provider = Column(String(50), nullable=False)
    provider_card_id = Column(String(100), nullable=False)

    name = Column(String(100), nullable=False, index=True)
    set_id = Column(String(100), nullable=False)
    set_name = Column(String(100), nullable=False)
    card_number = Column(String(50), nullable=False)
    rarity = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)

    reference_price = Column(Numeric(10, 2), nullable=True)
    reference_price_condition = Column(String(50), nullable=True)
    reference_price_variant = Column(String(50), nullable=True)
    reference_price_source = Column(String(50), nullable=True)
    reference_price_updated_at = Column(DateTime(timezone=True), nullable=True)
    currency = Column(String(3), nullable=False, default="USD")    