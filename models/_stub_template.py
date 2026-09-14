"""STUB — <MODEL NAME>.

Port the original build logic here. The contract: return ModelResult(payload=...),
where `payload` matches the schema the tab template <TAB>.html expects in its
`const <VAR> = {};` placeholder. Until ported, build() raises NotImplementedError,
which assemble.py catches and handles by keeping the last-good baked payload from
the committed template (so the tab still renders with its most recent data).

To port a model:
  1. Copy the fetch+transform from the original builder into build().
  2. Emit the exact keys the template reads (inspect the template's JS).
  3. Fill META and VAR to match the template.
  4. Run:  python -m build.run --only <TAB>   to test just this model.
"""
from .base import ModelResult

TAB = "REPLACE"
VAR = "REPLACE"
META = ("REPLACE", "category", "description", "csv_slug")


def build() -> ModelResult:
    raise NotImplementedError(f"{TAB} not yet ported")
