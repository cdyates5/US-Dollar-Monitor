"""Ordered list of models = tab order in the monitor. Scorecard is synthesised
separately by build/scorecard.py and placed first."""
from . import (lead_index, fair_value, real_curve, twin_deficit, fiscal_cycle,
               external_position, treasury_premium, real_money, pmi_diff, ppp,
               hedging, forex_risk)

MODELS = [lead_index, fair_value, real_curve, twin_deficit, fiscal_cycle,
          external_position, treasury_premium, real_money, pmi_diff, ppp,
          hedging, forex_risk]
