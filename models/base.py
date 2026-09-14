"""Model contract. Every model is a module exposing build() -> dict payload.

The payload is baked verbatim into the tab HTML by build/assemble.py, replacing
the `const <VAR> = {};` placeholder. Each model also declares:
  TAB   = filename stem of its HTML template in site/tabs/
  VAR   = the JS payload variable name in that template
  META  = (label, category, description, csv_slug) for the monitor shell
"""
from dataclasses import dataclass


@dataclass
class ModelResult:
    payload: dict          # JSON-serialisable, matches the template's schema
    current: dict          # small dict of headline readings for the scorecard
    ok: bool = True        # False -> assemble.py keeps last-good payload
    note: str = ""         # freshness / drift note surfaced in logs
