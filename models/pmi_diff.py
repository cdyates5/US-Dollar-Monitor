"""PMI Differential — uploaded dashboard; data not freely re-pullable (S&P Global PMI / Bloomberg /
digitized sources). Kept as last-good baked payload; refreshes when a public data
route is wired. See MODEL_STATUS.md."""
from .base import ModelResult

TAB="pmi"
VAR="PD"
META=("PMI Differential", "growth", "US-minus-global manufacturing momentum as a growth-gap driver of the dollar.", "us_global_pmi_differential")

def build()->ModelResult:
    # No free live source; signal the assembler to keep the committed baked payload.
    return ModelResult(payload={}, current={}, ok=False,
                       note="pmi: uploaded dashboard — baked payload retained (no free live source)")
