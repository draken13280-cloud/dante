from fcf.domain.enums import Severity
from fcf.qa.engine import QACheck


async def judge_visual(asset, product, brand, ctx) -> list[QACheck]:
    return [
        QACheck("garment_match", True, Severity.MAJOR, 0.9, "ok", None),
        QACheck("artifacts", True, Severity.BLOCKER, 1.0, "ok", None),
    ]
