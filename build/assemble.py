"""Assemble the monitor: run each model, bake its payload into its tab template,
inject the height-reporter + CSV-exporter, and build the base64 iframe shell.

Design decisions carried over from the hand-built monitor:
  * Tabs are isolated base64 `srcdoc` iframes (total JS/DOM isolation).
  * Shell decodes with Uint8Array+TextDecoder('utf-8') — NOT bare atob() —
    to avoid UTF-8 mojibake on em-dash / middot / sigma.
  * Payload is swapped by replacing `const <VAR> = {};` (or an existing baked
    object) with the fresh JSON via a regex that matches the first {...}.
  * If a model's build() fails or is a stub, the template's existing baked
    payload is preserved, so the tab still renders with last-good data.
"""
import re, json, base64, importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABS = ROOT / "site" / "tabs"
OUT = ROOT / "site" / "us-dollar-monitor.html"

REPORTER = """<script>(function(){function r(){var h=Math.max(document.body.scrollHeight,document.documentElement.scrollHeight);parent.postMessage({__fh:h,id:window.frameElement?window.frameElement.id:null},"*");}window.addEventListener("load",function(){r();setTimeout(r,600);setTimeout(r,1600);});window.addEventListener("resize",r);if(window.ResizeObserver){new ResizeObserver(r).observe(document.documentElement);}})();</script>"""

EXPORTER = (ROOT / "build" / "exporter.js").read_text()


def bake_payload(html: str, var: str, payload: dict) -> str:
    """Replace `const VAR = <anything>;` with the fresh payload."""
    js = json.dumps(payload, separators=(",", ":"))
    pat = re.compile(r"const\s+" + re.escape(var) + r"\s*=\s*(\{.*?\}|\[.*?\])\s*;", re.S)
    new = f"const {var} = {js};"
    out, n = pat.subn(lambda m: new, html, count=1)
    if n == 0:
        raise RuntimeError(f"payload placeholder for {var} not found")
    return out


def inject_helpers(html: str) -> str:
    add = REPORTER + "\n" + EXPORTER
    return html.replace("</body>", add + "\n</body>", 1) if "</body>" in html else html + add


def run():
    from models.registry import MODELS
    from build.scorecard import build_scorecard

    import os
    only = set(filter(None, os.environ.get("MONITOR_ONLY","").split(",")))
    tabs = []            # (label, cat, desc, slug, html)
    currents = {}
    for mod in MODELS:
        if only and mod.TAB not in only:
            label, cat, desc, slug = mod.META
            tabs.append((label, cat, desc, slug, (TABS / f"{mod.TAB}.html").read_text()))
            print(f"  {mod.TAB}: skipped (not in --only) — baked payload")
            continue
        tpl_path = TABS / f"{mod.TAB}.html"
        html = tpl_path.read_text()
        label, cat, desc, slug = mod.META
        note = ""
        try:
            res = mod.build()
            if res.ok:
                html = bake_payload(html, mod.VAR, res.payload)
                currents[mod.TAB] = res.current
            note = res.note
        except NotImplementedError:
            note = f"{mod.TAB}: stub — keeping last-good baked payload"
        except Exception as e:                                   # noqa
            note = f"{mod.TAB}: build FAILED ({type(e).__name__}: {e}) — keeping last-good"
        print(" ", note)
        tabs.append((label, cat, desc, slug, html))

    # scorecard first, synthesised from whatever current readings we have
    sc_html = build_scorecard(currents, TABS / "scorecard.html")
    tabs.insert(0, ("Scorecard", "synthesis",
                    "One-page weight of evidence across all models; every row opens its tab.",
                    "usd_monitor_scorecard", sc_html))

    frames = [base64.b64encode(inject_helpers(h).encode("utf-8")).decode("ascii") for *_ , h in tabs]
    shell = build_shell(tabs, frames)
    OUT.write_text(shell)
    print(f"\nwrote {OUT}  ({len(shell)//1024} KB, {len(tabs)} tabs)")


def build_shell(tabs, frames):
    metas = [{"label": l, "cat": c, "desc": d} for l, c, d, s, h in tabs]
    btns = "".join(
        f'<button role="tab" aria-selected="{"true" if i==0 else "false"}" id="tab-{i}" data-i="{i}">'
        f'{m["label"]}<span class="cat">{m["cat"]}</span></button>' for i, m in enumerate(metas))
    slots = "".join(
        f'<div class="view{" active" if i==0 else ""}" id="view-{i}" role="tabpanel">'
        f'<div class="fbar"><div class="fdesc">{metas[i]["desc"]}</div>'
        f'<button class="dlbtn" data-i="{i}" data-slug="{tabs[i][3]}" disabled>Download data (CSV)</button></div>'
        f'<iframe id="if-{i}" title="{metas[i]["label"]}"></iframe></div>' for i in range(len(tabs)))
    frames_js = json.dumps(frames)
    tpl = (Path(__file__).resolve().parent / "shell_template.html").read_text()
    import datetime
    tpl = tpl.replace("__BUILDSTAMP__", datetime.date.today().isoformat())
    return (tpl.replace("/*__TABBTNS__*/", btns)
               .replace("/*__SLOTS__*/", slots)
               .replace("/*__FRAMES__*/", frames_js))


if __name__ == "__main__":
    run()
