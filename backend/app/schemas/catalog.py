from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict


class CatalogVariantSearchResult(BaseModel):
    """
    One purchasable version returned for a catalog card.
    """

    # Cardfolio will normalize provider keys such as reverseHolofoil into
    # stable values such as reverse_holofoil.
    variant_key: str

    # Prices are represented as Decimal to avoid floating-point rounding.
    market_price: Decimal | None = Field(default=None, ge=0)

    currency: str = Field(
        default="USD",
        min_length=3,
        max_length=3,
    )


class CatalogCardSearchResult(BaseModel):
    """
    Cardfolio's normalized representation of one external search result.
    """

    # Identifies where this catalog data originated.
    provider: str = "pokemon_tcg"

    # Maps from the Pokemon API card's unique `id`.
    provider_card_id: str

    name: str

    # The provider nests these values inside its `set` object.
    set_id: str
    set_name: str

    # Maps from the provider's `number` field.
    card_number: str

    rarity: str | None = None

    # We will use the provider's larger card image for the lookup interface.
    image_url: str | None = None

    # default_factory creates a fresh list for every result and also supports
    # cards for which the provider has no TCGplayer pricing data.
    variants: list[CatalogVariantSearchResult] = Field(
        default_factory=list
    )


class CatalogSearchResponse(BaseModel):
    """
    Complete paginated response returned from Cardfolio to the frontend.
    """

    # Cardfolio calls this `items` instead of exposing the provider's `data`
    # field directly.
    items: list[CatalogCardSearchResult]

    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    count: int = Field(ge=0)
    total_count: int = Field(ge=0)

class CatalogImportRequest(BaseModel):
    '''Identify the provider card to fetch and save in our catalog'''

    #"extra" part rejects any unexpected fields
    model_config = ConfigDict(extra = "forbid")

    # This id goes into the provider url, so reject path and query seperators
    provider_card_id: str = Field(
        min_length = 1,
        max_length = 100,
        #restrict id to letters,digits, etc
        pattern=r"^[A-Za-z0-9_-]+$"
    )

class CatalogImportVariantResponse(CatalogVariantSearchResult):
    """Return an imported variant with the ID collection items will reference."""

    id: int

    # The import service returns SQLAlchemy rows rather than dictionaries.
    model_config = ConfigDict(from_attributes=True)


class CatalogImportResponse(CatalogCardSearchResult):
    """Return the catalog card and variants created or reused by an import."""

    id: int

    # Imported variants include database IDs that search-only results do not have.
    variants: list[CatalogImportVariantResponse] = Field(
        default_factory=list
    )

    model_config = ConfigDict(from_attributes=True)