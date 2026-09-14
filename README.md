# US Dollar Monitor — self-refreshing

A 13-tab systematic dashboard for the US dollar (ICE DXY). GitHub Actions rebuilds
it on a schedule, re-pulling every model's data from source and publishing to
GitHub Pages. No local machine required; the pipelines live in the repo, so an
environment reset can never wipe them.

**Live dashboard:** `https://<you>.github.io/<repo>/`  (after setup)

---

## How it works

```
models/         one module per model; each exposes build() -> ModelResult(payload)
  common.py     cached FRED / Yahoo / ECB fetchers with last-good fallback
  base.py       the ModelResult contract
  registry.py   model order = tab order
build/
  run.py        entry point:  python -m build.run [--only TAB ...]
  assemble.py   runs models, bakes payloads into templates, builds the iframe shell
  scorecard.py  synthesises the front-page scorecard from this run's readings
  exporter.js   universal Chart.js -> CSV exporter injected into every tab
  shell_template.html   the tabbed shell (mojibake-safe base64 + TextDecoder)
site/
  tabs/*.html   the 13 tab templates (payload placeholder: const VAR = {};)
  us-dollar-monitor.html   BUILT OUTPUT (committed each run; also copied to Pages)
data/cache/     raw fetch cache (committed, so a failed source falls back cleanly)
.github/workflows/
  refresh.yml           schedule + build + commit + deploy to Pages
  notify-on-failure.yml opens an issue if a refresh fails
```

Each tab is an isolated base64 `srcdoc` iframe — total JS/DOM isolation, so twelve
independently-authored dashboards coexist without collisions. The shell decodes with
`TextDecoder('utf-8')` (never bare `atob()`) to avoid mangling em-dash / · / σ.

## Setup

See **SETUP.md** for step-by-step instructions (create repo → add FRED key →
enable Actions write + Pages → run). Two decoupled workflows: `refresh.yml` builds
and commits the dashboard; `deploy-pages.yml` publishes it — so Pages can never wedge
the build.


## Model status

**8 of 12 models recompute live** from public data on each run: Lead Index, Fair
Value, Twin Deficit, Fiscal Cycle, External Position, Treasury Premium, Real Money,
Hedging Pressure. The other 4 (Real Curve, PMI Differential, PPP, Forex Risk) are
uploaded dashboards whose original data came from non-free sources; they retain
their last-good baked payload — clearly, and without breaking the build — until a
public data route is wired. See `MODEL_STATUS.md` for exactly what each needs and
the recommended port order (all but PMI are FRED-buildable).

> Note on the Lead Index reconstruction: this public-data version scores r≈0.39 vs
> the original's 0.48. Two components are approximated (marked `TODO` in
> `models/lead_index.py`): restore the TIPS-based real-curve term and the original
> OECD CLI vintage to recover full fidelity.

## Porting a model (repeatable recipe)

1. Open `models/<name>.py` (a stub) and `site/tabs/<tab>.html` (its template).
2. In the template, note the payload variable (`const VAR = {…}`) and every field
   its JS reads (`VAR.months`, `VAR.stats.r_is`, …). That's your output schema.
3. In the stub's `build()`, fetch with the `common.py` helpers, compute, and return
   `ModelResult(payload=<dict matching that schema>, current=<scorecard row>)`.
4. Test just that model:  `python -m build.run --only <tab>`  then open
   `site/us-dollar-monitor.html`. Fix until the tab renders with zero console errors.
5. Commit. The next scheduled run refreshes it live.

The full field schema for each template is discoverable with:
`grep -oE '<VAR>\.[a-zA-Z_]+' site/tabs/<tab>.html | sort -u`

## Local build

```bash
pip install -r requirements.txt
export FRED_API_KEY=...        # your key
python -m build.run           # writes site/us-dollar-monitor.html
```

## Data sources

FRED (rates, fiscal, CPI, NIIP, trade, recessions), Yahoo Finance (DXY, S&P 500),
ECB Data Portal (euro-area yields, M1, HICP), plus — for models yet to be ported —
Japan MOF (JGB), Bank of Canada Valet, IMF via DBnomics, OECD (CLI, M1). All cached
under `data/cache/` with graceful fallback.
