"""Real Curve — uploaded dashboard; data not freely re-pullable (S&P Global PMI / Bloomberg /
digitized sources). Kept as last-good baked payload; refreshes when a public data
route is wired. See MODEL_STATUS.md."""
from .base import ModelResult

TAB="curve"
VAR="RC"
META=("Real Curve", "rates", "Real yield-curve shape as a lead on the dollar via the rate-expectations channel.", "dxy_real_curve")

def build()->ModelResult:
    # No free live source; signal the assembler to keep the committed baked payload.
    return ModelResult(payload={}, current={}, ok=False,
                       note="curve: uploaded dashboard — baked payload retained (no free live source)")
