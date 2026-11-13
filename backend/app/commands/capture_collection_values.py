"""Run with python -m app.commands.capture_collection_values from backend."""

import logging

from sqlalchemy import or_

from app.db.database import SessionLocal
from app.models.user import User
from app.services.collection_values import record_collection_value_snapshots

logger = logging.getLogger(__name__)


def main() -> int:
    try:
        with SessionLocal() as db:
            rows = (
                db.query(User.id)
                # Include emptied collections so their history continues at zero.
                .filter(or_(User.collection_items.any(), User.collection_value_snapshots.any()))
                .order_by(User.id)
                .all()
            )
            user_ids = [row.id for row in rows]
    except Exception:
        logger.exception("Could not load accounts for collection value capture.")
        return 1

    succeeded = 0
    failed = 0
    for user_id in user_ids:
        try:
            # This context commits one account or rolls it back on any failure.
            with SessionLocal.begin() as db:
                record_collection_value_snapshots(db, user_id)
            succeeded += 1
        except Exception:
            # A fresh session on the next iteration keeps other accounts usable.
            failed += 1
            logger.exception("Collection value capture failed for user_id=%s.", user_id)

    logger.info(
        "Collection value capture finished. Selected=%d succeeded=%d failed=%d.",
        len(user_ids), succeeded, failed,
    )
    # The scheduler can detect a partial failure and safely rerun the command.
    return 1 if failed else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise SystemExit(main())
