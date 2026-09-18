from pydantic import BaseModel, HttpUrl


class ProductAttrs(BaseModel):
    color: str
    color_hex: str | None = None
    material: str
    material_tokens: list[str] = []
    fit: str | None = None
    care: str | None = None
    sizes: list[str] = []
    gender: str | None = None
    season: str | None = None
    price_cents: int | None = None
    currency: str = "USD"
    on_promo: bool = False
    certifications: list[str] = []


class Product(BaseModel):
    id: str
    brand_slug: str
    sku: str
    title: str
    attrs: ProductAttrs
    source_images: list[HttpUrl | str] = []
    notes: str | None = None
