"""Forex Risk — uploaded dashboard; data not freely re-pullable (S&P Global PMI / Bloomberg /
digitized sources). Kept as last-good baked payload; refreshes when a public data
route is wired. See MODEL_STATUS.md."""
from .base import ModelResult

TAB="risk"
VAR="FR"
META=("Forex Risk", "positioning", "Risk-appetite / positioning composite behind dollar swings.", "us_forex_risk_index")

def build()->ModelResult:
    # No free live source; signal the assembler to keep the committed baked payload.
    return ModelResult(payload={}, current={}, ok=False,
                       note="risk: uploaded dashboard — baked payload retained (no free live source)")
