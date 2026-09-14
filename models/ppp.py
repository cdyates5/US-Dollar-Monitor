"""PPP Overvaluation — uploaded dashboard; data not freely re-pullable (S&P Global PMI / Bloomberg /
digitized sources). Kept as last-good baked payload; refreshes when a public data
route is wired. See MODEL_STATUS.md."""
from .base import ModelResult

TAB="ppp"
VAR="PP"
META=("PPP Overvaluation", "long-run", "PPP mis-valuation as a decade-long lead on the dollar's secular direction.", "dollar_ppp_overvaluation")

def build()->ModelResult:
    # No free live source; signal the assembler to keep the committed baked payload.
    return ModelResult(payload={}, current={}, ok=False,
                       note="ppp: uploaded dashboard — baked payload retained (no free live source)")
