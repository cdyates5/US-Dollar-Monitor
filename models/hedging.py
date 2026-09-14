"""FX Hedging Pressure — 60d SPX-DXY rolling correlation regime gauge."""
import numpy as np, pandas as pd
from .common import yahoo_daily, fred
from .base import ModelResult

TAB="hedge"; VAR="HG"
META=("Hedging Pressure","flows","SPX-DXY correlation regime — the natural-hedge gauge behind the 2025 hedging wave; a monitoring dial, not a lead.","fx_hedging_pressure")
START=pd.Period("1990-01","M")

def build()->ModelResult:
    spx=yahoo_daily("^GSPC").to_timestamp(); dxy=yahoo_daily("DX-Y.NYB").to_timestamp()
    df=pd.concat([spx.pct_change(),dxy.pct_change()],axis=1,keys=["s","d"]).dropna()
    corr=df["s"].rolling(60).corr(df["d"]).dropna()
    corr_m=corr.resample("ME").last().to_period("M")
    dxy_m=dxy.resample("ME").last().to_period("M")
    yoy=(dxy_m/dxy_m.shift(12)-1)*100
    ldm=np.log(dxy_m)
    import statsmodels.api as sm
    res={}
    for h in [3,6]:
        fwd=(ldm.shift(-h)-ldm)*100
        d=pd.concat([corr_m,fwd],axis=1,keys=["x","f"]).dropna(); d=d[d.index>=START]
        m=sm.OLS(d["f"],sm.add_constant(d["x"])).fit(cov_type="HAC",cov_kwds={"maxlags":h})
        res[h]={"t":round(float(m.tvalues["x"]),1)}
    idx=pd.period_range(START,corr_m.index[-1],freq="M")
    def ser(s,nd=2): return [None if (p not in s.index or pd.isna(s.get(p))) else round(float(s[p]),nd) for p in idx]
    rec=fred("USREC").reindex(idx).fillna(0)
    cm=corr_m[corr_m.index>=START]
    ep=cm[(cm.index>=pd.Period("2025-01","M"))&(cm.index<=pd.Period("2026-06","M"))]
    now=float(cm.iloc[-1])
    payload={"months":[str(p) for p in idx],"corr":ser(corr_m),"yoy":ser(yoy,1),
     "rec":[int(v) for v in rec],
     "events":[["2025-04","BIS: hedging wave drives April slide"],["2026-01","natural hedge fragile again"]],
     "stats":{"now":round(now,2),"latest":str(cm.index[-1]),
       "share_pos":round(float((cm>0).mean()*100)),"ep_months":int((ep>0).sum()),
       "t3":res[3]["t"],"t6":res[6]["t"],"n":int(len(cm.dropna())),
       "dxy_last":round(float(dxy_m.dropna().iloc[-1]),2),"dxy_last_m":str(dxy_m.dropna().index[-1])}}
    current={"reading":f"{now:+.2f}","stance":"PRESSURE OFF" if now<0 else "PRESSURE ON",
             "implied":"Natural hedge "+("restored" if now<-0.2 else "fragile")}
    return ModelResult(payload=payload,current=current,ok=True,note=f"Hedging asof {cm.index[-1]}, corr={now:+.2f}")
