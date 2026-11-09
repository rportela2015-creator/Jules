from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Any

getcontext().prec = 28
ZERO, ONE = Decimal("0"), Decimal("1")

def r2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def dec(v: Any) -> Decimal:
    if v is None or v == "":
        return ZERO
    return v if isinstance(v, Decimal) else Decimal(str(v))

def pc(v: Any) -> Decimal:
    return dec(v) / Decimal(100)

def fl(v: Decimal) -> float:
    return float(r2(v))
