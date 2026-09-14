"""Shared data-access layer for all dollar-monitor models.

Every fetcher caches raw pulls under data/cache/ so a failed upstream (Yahoo
rate-limit, ECB downtime) falls back to the last good copy instead of breaking
the whole build. Set FRED_API_KEY in the environment (GitHub Actions secret).
"""
import os, json, time, io, hashlib
from pathlib import Path
import pandas as pd, numpy as np, requests

CACHE = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
FRED_KEY = os.environ.get("FRED_API_KEY", "")
UA = {"User-Agent": "Mozilla/5.0 (compatible; dollar-monitor/1.0) AppleWebKit/537.36"}
STALE_OK_DAYS = 20   # how old a cache file may be before we warn (not fail)


def _cache_path(tag: str) -> Path:
    return CACHE / (hashlib.md5(tag.encode()).hexdigest()[:16] + "__" + tag.replace("/", "_")[:60] + ".json")


def _read_cache(tag: str):
    p = _cache_path(tag)
    if p.exists():
        try:
            obj = json.loads(p.read_text())
            return pd.Series(obj["v"], index=pd.PeriodIndex(obj["i"], freq=obj["f"]))
        except Exception:
            return None
    return None


def _write_cache(tag: str, s: pd.Series, freq: str):
    p = _cache_path(tag)
    p.write_text(json.dumps({"i": [str(x) for x in s.index], "v": [None if pd.isna(x) else float(x) for x in s.values], "f": freq}))


def _retry(fn, tries=5, base=2.0):
    last = None
    for a in range(tries):
        try:
            return fn()
        except Exception as e:                       # noqa
            last = e
            time.sleep(base * (a + 1))
    raise last


def fred(series_id: str, freq: str = "M") -> pd.Series:
    """Fetch a FRED series, caching the result. Falls back to cache on failure."""
    tag = f"fred/{series_id}/{freq}"
    def _pull():
        r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                         params={"series_id": series_id, "api_key": FRED_KEY, "file_type": "json"},
                         timeout=45)
        r.raise_for_status()
        obs = [(o["date"], float(o["value"])) for o in r.json()["observations"] if o["value"] != "."]
        if not obs:
            raise RuntimeError("empty series")
        s = pd.Series(dict(obs))
        s.index = pd.PeriodIndex(pd.to_datetime(s.index), freq=freq)
        return s.sort_index()
    try:
        s = _retry(_pull)
        _write_cache(tag, s, freq)
        return s
    except Exception as e:
        cached = _read_cache(tag)
        if cached is not None:
            print(f"  [warn] FRED {series_id} failed ({type(e).__name__}); using cache")
            return cached
        raise


def yahoo_daily(symbol: str) -> pd.Series:
    """Daily close from Yahoo, cached, with fallback."""
    tag = f"yahoo/{symbol}/D"
    def _pull():
        r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                         params={"period1": 0, "period2": int(time.time()), "interval": "1d"},
                         headers=UA, timeout=45)
        r.raise_for_status()
        j = r.json()["chart"]["result"][0]
        s = pd.Series(j["indicators"]["quote"][0]["close"],
                      index=pd.to_datetime(j["timestamp"], unit="s").normalize()).dropna()
        s = s[~s.index.duplicated(keep="last")].sort_index()
        s.index = pd.PeriodIndex(s.index, freq="D")
        if len(s) < 100:
            raise RuntimeError("suspiciously short")
        return s
    try:
        s = _retry(_pull)
        _write_cache(tag, s, "D")
        return s
    except Exception as e:
        cached = _read_cache(tag)
        if cached is not None:
            print(f"  [warn] Yahoo {symbol} failed ({type(e).__name__}); using cache")
            return cached
        raise


def ecb(key: str, freq: str = "M") -> pd.Series:
    """ECB SDW/Data-API series (CSV), cached, with fallback. `key` is the full series key."""
    tag = f"ecb/{key}/{freq}"
    def _pull():
        r = requests.get(f"https://data-api.ecb.europa.eu/service/data/{key}",
                         params={"format": "csvdata"}, timeout=60)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        s = pd.Series(df["OBS_VALUE"].values, index=pd.PeriodIndex(df["TIME_PERIOD"], freq=freq))
        return s.sort_index()
    try:
        s = _retry(_pull)
        _write_cache(tag, s, freq)
        return s
    except Exception as e:
        cached = _read_cache(tag)
        if cached is not None:
            print(f"  [warn] ECB {key} failed ({type(e).__name__}); using cache")
            return cached
        raise


def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()


def dxy_monthly() -> pd.Series:
    return yahoo_daily("DX-Y.NYB").to_timestamp().resample("ME").last().to_period("M")


def boj_m1_yoy():
    """BOJ M1 YoY (%) from the MTS money-stock table, cached."""
    import requests, io, pandas as pd
    tag = "boj/m1yoy/M"
    def _pull():
        r = requests.get("https://www.stat-search.boj.or.jp/ssi/mtshtml/md02_m_1.html", headers=UA, timeout=45)
        r.encoding = "shift_jis"
        t = pd.read_html(io.StringIO(r.text))[0]
        rows = t.iloc[6:, [0, 3]].dropna()
        rows = rows[rows.iloc[:, 0].astype(str).str.match(r"\d{4}/\d{2}")]
        s = pd.Series(pd.to_numeric(rows.iloc[:, 1], errors="coerce").values,
                      index=pd.PeriodIndex(rows.iloc[:, 0].str.replace("/", "-"), freq="M")).dropna().sort_index()
        if len(s) < 100: raise RuntimeError("short")
        return s
    try:
        s = _retry(_pull); _write_cache(tag, s, "M"); return s
    except Exception as e:
        c = _read_cache(tag)
        if c is not None: print(f"  [warn] BOJ M1 failed ({type(e).__name__}); cache"); return c
        raise


def dbnomics(series: str, freq="M"):
    """A DBnomics series (e.g. IMF/CPI/M.JP.PCPI_IX), cached."""
    import requests, pandas as pd
    tag = f"dbn/{series}/{freq}"
    def _pull():
        r = requests.get(f"https://api.db.nomics.world/v22/series/{series}", params={"observations": "1"}, timeout=45)
        d = r.json()["series"]["docs"][0]
        s = pd.Series(pd.to_numeric(pd.Series(d["value"]), errors="coerce").values, index=pd.PeriodIndex(d["period"], freq=freq)).dropna().sort_index()
        return s
    try:
        s = _retry(_pull); _write_cache(tag, s, freq); return s
    except Exception as e:
        c = _read_cache(tag)
        if c is not None: print(f"  [warn] DBnomics {series} failed; cache"); return c
        raise


def boc_valet(code: str, freq="M"):
    """Bank of Canada Valet series -> monthly mean, cached."""
    import requests, pandas as pd
    tag = f"boc/{code}/{freq}"
    def _pull():
        r = requests.get(f"https://www.bankofcanada.ca/valet/observations/{code}/json",
                         params={"start_date": "1995-01-01"}, timeout=45)
        obs = r.json()["observations"]
        s = pd.Series({o["d"]: float(o[code]["v"]) for o in obs if o[code]["v"] is not None})
        s.index = pd.to_datetime(s.index)
        return s.sort_index().resample("ME").mean().to_period("M")
    try:
        s = _retry(_pull); _write_cache(tag, s, freq); return s
    except Exception as e:
        c = _read_cache(tag)
        if c is not None: print(f"  [warn] BoC {code} failed; cache"); return c
        raise
