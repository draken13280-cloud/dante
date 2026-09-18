from __future__ import annotations

import re

from fcf.domain.enums import Severity
from fcf.qa.engine import QACheck

ABSOLUTE = re.compile(r"\b(best|#1|number one|guaranteed|perfect|flawless|unbeatable)\b", re.I)
HEALTH = re.compile(
    r"\b(slimming|slim you|anti-?cellulite|posture[- ]correct\w*|detox\w*|therapeutic|medical(?:ly)?)\b",
    re.I,
)
ECO = re.compile(
    r"\b(eco[- ]?friendly|sustainable|carbon[- ]neutral|planet[- ]positive|zero[- ]waste|100% green|biodegradable)\b",
    re.I,
)
PRICE = re.compile(r"(\$|€|£|\bsale\b|\b\d{1,2}% off\b|\bdiscount\b|\bcheap\b)", re.I)
FIBRES = [
    "cotton",
    "wool",
    "silk",
    "linen",
    "cashmere",
    "leather",
    "denim",
    "polyester",
    "viscose",
    "modal",
    "nylon",
    "elastane",
    "lyocell",
    "tencel",
]
EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF]")
COLOURS = re.compile(
    r"\b(red|blue|green|black|white|navy|indigo|cherry|pink|yellow|orange|purple|beige|grey|gray)\b",
    re.I,
)


def check_copy(content: dict, product, brand, policy) -> list[QACheck]:
    out: list[QACheck] = []
    title, body = content.get("title", ""), content.get("body", "")
    tags = content.get("hashtags") or []
    full = " ".join([title, body, content.get("cta", ""), " ".join(tags)])

    def add(rule, ok, sev, detail, hint=None, score=None):
        out.append(
            QACheck(rule, ok, sev, score if score is not None else float(ok), detail, None if ok else hint)
        )

    add(
        "title_length",
        len(title) <= policy.title_max,
        Severity.BLOCKER,
        f"{len(title)}/{policy.title_max}",
        f"Shorten the title to at most {policy.title_max} characters.",
    )
    add(
        "body_length",
        len(body) <= policy.body_max,
        Severity.MAJOR,
        f"{len(body)}/{policy.body_max}",
        f"Shorten the body to at most {policy.body_max} characters.",
    )
    n = len(tags)
    add(
        "hashtag_count",
        policy.hashtags_min <= n <= policy.hashtags_max,
        Severity.MAJOR,
        f"{n} tags, expected {policy.hashtags_min}-{policy.hashtags_max}",
        f"Return exactly {policy.hashtags_min}-{policy.hashtags_max} hashtags.",
    )
    add(
        "hashtag_format",
        all(re.fullmatch(r"#[A-Za-z0-9_]{2,30}", t) for t in tags) if tags else True,
        Severity.MINOR,
        "malformed hashtags",
        "Hashtags must be single words, no spaces or punctuation.",
    )
    e = len(EMOJI.findall(full))
    add("emoji_budget", e <= policy.emoji_max, Severity.MINOR, f"{e}/{policy.emoji_max}", f"Use at most {policy.emoji_max} emoji.")
    add(
        "cta_present",
        (not policy.cta_required) or bool(content.get("cta", "").strip()),
        Severity.MAJOR,
        "missing CTA",
        "Add a short, concrete call to action.",
    )
    add(
        "alt_text",
        (not policy.alt_text_required) or len(content.get("alt_text", "")) >= 20,
        Severity.MAJOR,
        "alt text missing/too short",
        "Write alt text of 20-125 chars describing the garment for screen readers.",
    )
    hits = [p for p in brand.tone.banned_phrases if p.lower() in full.lower()]
    add(
        "banned_phrases",
        not hits,
        Severity.BLOCKER,
        f"found {hits}",
        f"Remove these phrases entirely: {', '.join(hits)}.",
    )
    comp = [c for c in brand.claims.forbid_competitor_mentions if c.lower() in full.lower()]
    add(
        "no_competitors",
        not comp,
        Severity.BLOCKER,
        f"found {comp}",
        f"Never mention competitor brands: {', '.join(comp)}.",
    )
    try:
        import textstat

        grade = textstat.flesch_kincaid_grade(body) if len(body) > 40 else 0
    except Exception:
        grade = 0
    add(
        "reading_level",
        grade <= brand.tone.reading_level_max,
        Severity.MINOR,
        f"grade {grade:.1f} > {brand.tone.reading_level_max}",
        "Use shorter sentences and simpler words.",
        score=max(0.0, 1 - (grade - brand.tone.reading_level_max) / 6),
    )
    mentioned = {f for f in FIBRES if re.search(rf"\b{f}\b", full, re.I)}
    allowed = {t.lower() for t in (product.attrs.material_tokens or [])} | {
        w.lower() for w in re.findall(r"[a-z]+", product.attrs.material.lower())
    }
    # denim is cotton-based; allow denim if cotton present
    if "cotton" in allowed:
        allowed.add("denim")
    if "denim" in allowed:
        allowed.add("cotton")
    wrong = mentioned - allowed
    add(
        "fibre_consistency",
        not wrong,
        Severity.BLOCKER,
        f"copy mentions {wrong}, product is '{product.attrs.material}'",
        f"The garment is {product.attrs.material}. Never mention {', '.join(wrong)}.",
    )
    colour_ok = product.attrs.color.lower() in full.lower() or not COLOURS.search(full)
    add(
        "colour_consistency",
        colour_ok,
        Severity.MAJOR,
        f"product colour is {product.attrs.color}",
        f"The colour is {product.attrs.color}. Do not name any other colour.",
    )
    if brand.claims.forbid_absolute:
        m = ABSOLUTE.findall(full)
        add("no_absolute_claims", not m, Severity.MAJOR, f"found {m}", "Remove superlative/absolute claims.")
    if brand.claims.forbid_health_claims:
        m = HEALTH.findall(full)
        add("no_health_claims", not m, Severity.BLOCKER, f"found {m}", "Remove all body/health claims.")
    if brand.claims.sustainability_requires_cert:
        eco = bool(ECO.search(full))
        certified = bool(set(product.attrs.certifications) & set(brand.claims.allowed_certifications))
        add(
            "eco_claim_backed",
            (not eco) or certified,
            Severity.BLOCKER,
            "eco claim without certification",
            "Remove sustainability claims — this product has no supporting certification.",
        )
    if not product.attrs.on_promo:
        m = PRICE.search(full)
        add(
            "no_unauthorised_price",
            not m,
            Severity.MAJOR,
            f"found '{m.group(0) if m else ''}'",
            "Do not mention price, discounts or sales.",
        )
    script = content.get("script", "")
    if script:
        add(
            "script_speakable",
            not EMOJI.search(script) and "#" not in script and "http" not in script,
            Severity.MAJOR,
            "script contains unspeakable tokens",
            "The script is read aloud: no hashtags, emoji or URLs.",
        )
        words = len(script.split())
        add(
            "script_duration_fit",
            12 <= words <= 90,
            Severity.MAJOR,
            f"{words} words",
            "Keep the voiceover script between 15 and 80 words (~6-30s).",
        )
    return out
