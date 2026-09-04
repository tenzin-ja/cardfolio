from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.card_variant import CardVariant
from app.models.catalog_card import CatalogCard
from app.models.price_snapshot import PriceSnapshot
from app.schemas.catalog import CatalogCardSearchResult

PRICE_SOURCE = "tcgplayer"

