from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from fcf.domain.brand import BrandKit
from fcf.domain.product import Product, ProductAttrs
from fcf.providers.mock.llm import MockLLM
from fcf.providers.register_all import register_defaults


@pytest.fixture(autouse=True)
def _providers():
    register_defaults()
    MockLLM.fault_injection = {}
    yield
    MockLLM.fault_injection = {}


@pytest.fixture
def brand() -> BrandKit:
    data = yaml.safe_load(Path("brandkits/acme_denim.yaml").read_text())
    return BrandKit.model_validate(data)


@pytest.fixture
def product(brand) -> Product:
    return Product(
        id="p1",
        brand_slug=brand.slug,
        sku="ACME-DNM-001",
        title="ACME Selvedge Straight",
        attrs=ProductAttrs(
            color="indigo",
            color_hex="#1B2A41",
            material="100% cotton",
            material_tokens=["cotton", "denim"],
        ),
    )
