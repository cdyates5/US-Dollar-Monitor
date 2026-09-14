# Model port status

**8 of 12 models recompute live from public data on each scheduled run.**
The other 4 are uploaded dashboards whose original data came from sources that
are not freely re-pullable (S&P Global PMI, Bloomberg, digitized chart data);
they retain their last-good baked payload, clearly, until a public data route is
wired. Nothing breaks — every tab renders on every build.

| Tab | Model | Status | Source / note |
|-----|-------|--------|---------------|
| lead  | Lead Index        | ✅ live | FRED + Yahoo. r≈0.39 vs orig 0.48 — restore TIPS real-curve term + OECD CLI vintage (TODOs in module) for full fidelity |
| fv    | Fair Value        | ✅ live | FRED + Yahoo. gap +7.8% (matches orig +7.76%), R²≈0.47. Relative-equity driver uses SP500 level; swap in a US-vs-world ratio to match orig exactly |
| twin  | Twin Deficit      | ✅ live | FRED (MTS balance + net exports, % GDP, 4Q avg, pushed 7Q) |
| jiang | Fiscal Cycle      | ✅ live | FRED. In-window t=1.2, 2018+ inverts (t=−1.2) — reproduces the original finding |
| nxa   | External Position | ✅ live | FRED (NIIP annual/quarterly splice + net exports). Era decay 0.70→0.22, OOS 0.03 — exact match |
| cy    | Treasury Premium  | ✅ live | FRED + ECB + BoC. cC≈−0.05 (non-replicability result intact). JP leg omitted (MOF not wired); EUR+CAD proxies carry it |
| ward  | Real Money        | ✅ live | FRED + ECB + BOJ + IMF/DBnomics. t9=0.9 (no-lead result intact) |
| hedge | Hedging Pressure  | ✅ live | Yahoo (SPX + DXY 60d corr). Refreshes fully every run |
| curve | Real Curve        | ⚠️ static | Uploaded dashboard. Needs real (TIPS) 10s–3m — buildable from FRED DFII10/DGS3+CPI; port next |
| pmi   | PMI Differential  | ⚠️ static | Uploaded. OECD BCI on FRED is frozen at Jan-2024; needs S&P Global PMI (paid) or a live BCI mirror |
| ppp   | PPP Overvaluation | ⚠️ static | Uploaded. Digitized Yardeni/LSEG PPP path; needs a public real-effective-exchange-rate source (e.g. BIS REER) to rebuild |
| risk  | Forex Risk        | ⚠️ static | Uploaded. CrossBorder-style composite; components (credit spreads, vol, equity/commodity momentum, real fed funds) are FRED-buildable — largest but feasible port |

## Highest-value next ports (all FRED-buildable)
1. **Real Curve** — DFII10 (10y TIPS) minus real 3m (DGS3 − trailing CPI), advanced 12m. Straightforward.
2. **Forex Risk** — rebuild the 5 z-scored components from FRED (BAMLH0A0HYM2 credit spread, VIXCLS, SP500 momentum, commodity momentum, real fed funds). Feasible, ~1 session.
3. **PPP** — swap the digitized path for BIS/FRED real effective exchange rate (RBUSBIS) as the overvaluation base.
4. **PMI** — only one needing a paid feed; leave static or wire a PMI provider.
