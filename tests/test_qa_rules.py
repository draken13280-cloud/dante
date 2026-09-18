from fcf.domain.enums import Severity
from fcf.qa.rules_text import check_copy


def test_banned_phrase_is_blocker(brand, product):
    pol = brand.channels.__iter__().__next__() if False else list(brand.channels.values())[0]
    # shopify policy
    pol = brand.channels[[c for c in brand.channels if c.value == "shopify"][0]]
    checks = check_copy(
        {
            "title": "must-have denim",
            "body": "cotton indigo jean",
            "hashtags": [],
            "cta": "",
            "alt_text": "indigo cotton denim straight fit photographed in studio",
            "script": "",
        },
        product,
        brand,
        pol,
    )
    banned = next(c for c in checks if c.rule == "banned_phrases")
    assert not banned.passed
    assert banned.severity is Severity.BLOCKER


def test_health_claim_blocker(brand, product):
    pol = brand.channels[[c for c in brand.channels if c.value == "shopify"][0]]
    checks = check_copy(
        {
            "title": "indigo cotton jean",
            "body": "slimming silhouette that is anti-cellulite",
            "hashtags": [],
            "cta": "",
            "alt_text": "indigo cotton denim photographed in studio lighting",
            "script": "",
        },
        product,
        brand,
        pol,
    )
    health = next(c for c in checks if c.rule == "no_health_claims")
    assert not health.passed


def test_silk_on_cotton_fails_fibre(brand, product):
    pol = brand.channels[[c for c in brand.channels if c.value == "shopify"][0]]
    checks = check_copy(
        {
            "title": "silk indigo jean",
            "body": "cut from silk",
            "hashtags": [],
            "cta": "",
            "alt_text": "silk looking garment which is wrong",
            "script": "",
        },
        product,
        brand,
        pol,
    )
    fibre = next(c for c in checks if c.rule == "fibre_consistency")
    assert not fibre.passed
