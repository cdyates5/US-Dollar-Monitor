"""Lead Index — 5 exogenous components -> DXY YoY at k=6 months.

REFERENCE IMPLEMENTATION (fully wired). The other models follow this shape.
Validated target from the original build: r_is ~0.48. This reconstruction uses
public series; where a component needs the exact original definition (e.g. a
TIPS-based real curve, a specific CLI vintage) it is marked TODO so you can
restore full fidelity.
"""
import numpy as np, pandas as pd
from .common import fred, dxy_monthly, zscore
from .base import ModelResult

TAB = "lead"
VAR = "DATA"
META = ("Lead Index", "direction",
        "6-month directional forecast for DXY YoY from five exogenous macro pressures.",
        "us_dollar_lead_index")
K = 6
START = pd.Period("1995-01", "M")


def build() -> ModelResult:
    dxy = dxy_monthly()
    y = (dxy / dxy.shift(12) - 1) * 100

    us10 = fred("GS10"); de10 = fred("IRLTLT01DEM156N"); jp10 = fred("IRLTLT01JPM156N")
    rd10_d12 = (us10 - (0.7 * de10 + 0.3 * jp10)).diff(12)

    # foreign CLI, 6m change, inverted  (TODO: match original CLI vintage for full fidelity)
    cli = fred("OECDLOLITONOSTSAM")
    fcli_d6_inv = -cli.diff(6)

    wti = fred("MCOILWTICO"); wti_yoy = (wti / wti.shift(12) - 1) * 100

    mts = fred("MTSDS133FMS"); sur12 = mts.rolling(12).sum()
    gdp = fred("GDP", "Q").resample("M").ffill()
    fis_d12 = (sur12 / gdp).diff(12)

    tb3 = fred("TB3MS"); rdcurve_d12 = (us10 - tb3).diff(12)   # TODO: original uses real (TIPS) curve

    comps = {"rd10_d12": rd10_d12, "fcli_d6_inv": fcli_d6_inv,
             "wti_yoy": wti_yoy, "fis_d12": fis_d12, "rdcurve_d12": rdcurve_d12}
    Z = pd.DataFrame({k: zscore(v) for k, v in comps.items()})
    comp = Z.mean(axis=1).dropna()

    d = pd.concat([comp, y.shift(-K)], axis=1, keys=["c", "f"]).dropna()
    d = d[d.index >= START]
    b, a = np.polyfit(d["c"], d["f"], 1)
    r = float(np.corrcoef(d["c"], d["f"])[0, 1])

    months = pd.period_range(START, comp.index[-1] + K, freq="M")
    def ser(s, nd=1):
        return [None if (p not in s.index or pd.isna(s.get(p))) else round(float(s[p]), nd) for p in months]
    implied = (a + b * comp); implied.index = implied.index + K
    rec = fred("USREC").reindex(months).fillna(0)

    prof = {}
    for k in range(0, 8):
        dd = pd.concat([comp.shift(k), y], axis=1).dropna()
        dd = dd[dd.index >= START]
        prof[str(k)] = round(float(dd.corr().iloc[0, 1]), 3) if len(dd) > 40 else None

    comp_now = float(comp.iloc[-1]); implied_now = a + b * comp_now
    # extended stats to match the validated template schema
    ex = pd.concat([comp, y.shift(-K)], axis=1, keys=["c","f"]).dropna()
    ex = ex[(ex.index >= START) & (~ex.index.to_timestamp().to_series().dt.year.isin([2008,2009,2020]).values)]
    r_ex = float(np.corrcoef(ex["c"], ex["f"])[0,1]) if len(ex) > 40 else r
    d04 = pd.concat([comp.shift(4), y], axis=1).dropna(); d04 = d04[d04.index >= START]
    r_04 = float(d04.corr().iloc[0,1])
    # expanding-window pseudo-OOS
    preds={}
    cy2 = pd.concat([comp, y.shift(-K)], axis=1, keys=["c","f"]).dropna()
    for t in comp.index:
        tr = cy2[cy2.index <= t - K]
        if len(tr) < 60 or t < START: continue
        bb, aa = np.polyfit(tr["c"], tr["f"], 1); preds[t+K] = aa + bb*comp[t]
    pr = pd.Series(preds); ya = y.copy()
    both = pd.concat([pr, ya], axis=1, keys=["p","a"]).dropna()
    r_oos = float(both.corr().iloc[0,1]) if len(both) > 30 else float("nan")
    hit = float((np.sign(both["p"])==np.sign(both["a"])).mean()) if len(both) > 30 else float("nan")
    ylast = float(y.dropna().iloc[-1]); ylast_m = str(y.dropna().index[-1])
    payload = {
        "months": [str(p) for p in months],
        "y": ser(y), "implied": ser(implied), "comp": ser(comp, 2),
        "components": {k: ser(zscore(v), 2) for k, v in comps.items()},
        "rec": [int(v) for v in rec],
        "profile": prof,
        "scatter": [[round(float(c), 2), round(float(f), 2), str(i)]
                    for i, (c, f) in d.iterrows()],
        "stats": {"K": K, "a": round(float(a), 2), "b": round(float(b), 2),
                  "r_is": round(r, 2), "r_ex": round(r_ex, 2), "r_04": round(r_04, 2),
                  "r_oos": round(r_oos, 2), "hit": round(hit, 2),
                  "n_is": int(len(d)), "n_oos": int(len(both)),
                  "comp_now": round(comp_now, 2),
                  "comp_z_now": {k: (None if pd.isna(zscore(v).iloc[-1]) else round(float(zscore(v).iloc[-1]),2)) for k,v in comps.items()},
                  "implied_now": round(float(implied_now), 1),
                  "asof": str(comp.index[-1]), "latest": str(comp.index[-1]),
                  "target": str(comp.index[-1] + K), "target_month": str(comp.index[-1] + K),
                  "y_last": round(ylast, 1), "y_last_m": ylast_m,
                  "dxy_last": round(float(dxy.iloc[-1]), 2), "dxy_last_m": str(dxy.index[-1])},
    }
    current = {"reading": f"{comp_now:+.2f}\u03c3", "stance": "USD+" if implied_now > 0 else "USD-",
               "implied": f"{implied_now:+.1f}% DXY YoY by {comp.index[-1]+K}", "r": r}
    note = f"Lead Index asof {comp.index[-1]}, r={r:.2f} (target 0.48; restore TIPS curve + CLI vintage for full fidelity)"
    return ModelResult(payload=payload, current=current, ok=True, note=note)
