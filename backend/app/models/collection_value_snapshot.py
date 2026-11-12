from sqlalchemy import (
    BigInteger, CheckConstraint, Column, Date, DateTime, ForeignKey,
    Integer, Numeric, String, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class CollectionValueSnapshot(Base):
    """The latest recorded collection estimate for one user, UTC day and currency."""

    __tablename__ = "collection_value_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date", "currency",
                         name="uq_collection_value_snapshots_user_day_currency"),
        CheckConstraint("total_quantity >= 0 AND priced_quantity >= 0 AND unpriced_quantity >= 0",
                        name="ck_collection_value_snapshots_nonnegative_quantities"),
        CheckConstraint("total_quantity = priced_quantity + unpriced_quantity",
                        name="ck_collection_value_snapshots_quantity_coverage"),
        CheckConstraint("estimated_value >= 0", name="ck_collection_value_snapshots_nonnegative_value"),
        CheckConstraint(
            "((total_quantity = 0 OR priced_quantity > 0) AND estimated_value IS NOT NULL) "
            "OR (total_quantity > 0 AND priced_quantity = 0 AND estimated_value IS NULL)",
            name="ck_collection_value_snapshots_value_presence",
        ),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    currency = Column(String(3), nullable=False)

    # Aggregates can exceed the limits of a single entry's quantity or price.
    total_quantity = Column(BigInteger, nullable=False)
    priced_quantity = Column(BigInteger, nullable=False)
    unpriced_quantity = Column(BigInteger, nullable=False)
    # NULL means every owned copy in this currency has an unknown price.
    estimated_value = Column(Numeric(30, 2), nullable=True)

    user = relationship("User", back_populates="collection_value_snapshots")
