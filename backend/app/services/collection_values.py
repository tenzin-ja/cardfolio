from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.card_variant import CardVariant
from app.models.collection_item import CollectionItem
from app.models.collection_value_snapshot import CollectionValueSnapshot
from app.models.user import User


def get_collection_totals(db: Session, user_id: int):
    """Calculate copy counts and exact reference-value subtotals per currency."""
    return (
        db.query(
            CardVariant.currency,
            func.sum(CollectionItem.quantity).label("total_quantity"),
            # Zero is a known price; only NULL means unavailable.
            func.sum(case(
                (CardVariant.market_price.is_not(None), CollectionItem.quantity),
                else_=0,
            )).label("priced_quantity"),
            func.coalesce(
                func.sum(CollectionItem.quantity * CardVariant.market_price),
                Decimal("0.00"),
            ).label("estimated_value"),
        )
        .join(CardVariant, CollectionItem.card_variant_id == CardVariant.id)
        .filter(CollectionItem.user_id == user_id)
        .group_by(CardVariant.currency)
        .order_by(CardVariant.currency)
        .all()
    )


def record_collection_value_snapshots(
    db: Session, user_id: int, *, previous_currencies: tuple[str, ...] = (),
) -> None:
    """Stage today's snapshots. The caller commits them with its collection change."""
    # API changes already hold this lock. Future scheduled captures use it too.
    db.query(User).filter(User.id == user_id).with_for_update().one()
    # Sessions disable autoflush: the totals must see pending adds/edits/deletes.
    db.flush()
    observed_at = datetime.now(timezone.utc)
    snapshot_date = observed_at.date()
    totals = {row.currency: row for row in get_collection_totals(db, user_id)}
    previous = (
        db.query(CollectionValueSnapshot.currency)
        .filter(CollectionValueSnapshot.user_id == user_id)
        .distinct()
        .all()
    )
    # Carry removed currencies forward as zero, including a legacy entry's first deletion.
    currencies = set(totals) | {row.currency for row in previous} | set(previous_currencies)
    existing = {
        row.currency: row
        for row in db.query(CollectionValueSnapshot).filter(
            CollectionValueSnapshot.user_id == user_id,
            CollectionValueSnapshot.snapshot_date == snapshot_date,
        ).all()
    }
    for currency in sorted(currencies):
        total = totals.get(currency)
        total_quantity = total.total_quantity if total else 0
        priced_quantity = total.priced_quantity if total else 0
        value = total.estimated_value if total else Decimal("0.00")
        if total_quantity > 0 and priced_quantity == 0:
            value = None

        snapshot = existing.get(currency)
        if snapshot is None:
            snapshot = CollectionValueSnapshot(
                user_id=user_id, snapshot_date=snapshot_date, currency=currency,
            )
            db.add(snapshot)
        snapshot.observed_at = observed_at
        snapshot.total_quantity = total_quantity
        snapshot.priced_quantity = priced_quantity
        snapshot.unpriced_quantity = total_quantity - priced_quantity
        snapshot.estimated_value = value
