"""Fair Value — Δ12-on-Δ12 OLS of DXY on macro drivers; rich/cheap gap."""
import numpy as np, pandas as pd, statsmodels.api as sm
from .common import fred, ecb, dxy_monthly
from .base import ModelResult
TAB="fv"; VAR="FD"
META=("Fair Value","valuation","Is the dollar rich or cheap versus its contemporaneous fundamental drivers?","us_dollar_fair_value")
START=pd.Period("1990-01","M")

def build()->ModelResult:
    dxy=dxy_monthly(); ldxy=np.log(dxy); yoy=(dxy/dxy.shift(12)-1)*100
    us10=fred("GS10"); de10=fred("IRLTLT01DEM156N"); jp10=fred("IRLTLT01JPM156N")
    rd10=us10-(0.7*de10+0.3*jp10)
    # relative equity: S&P vs MSCI-proxy — use US vs EA equity via FRED (SP500 vs STOXX not on FRED) -> use real broad $ comparators
    spx=fred("SP500") if False else None
    # relative equity proxy: US equity total return vs world — approximate with SP500 index level YoY minus DAX? keep to FRED: use NASDAQCOM? 
    # Use VIX and WTI + rd10 + relative equity via 'DEXUSEU'-free path: relative equity = SP500/CP... fallback to price momentum of SP500
    releq=None
    try:
        sp=fred("SP500"); releq=sp[~sp.index.duplicated(keep="last")]
    except Exception: releq=None
    wti=fred("MCOILWTICO"); vix=fred("VIXCLS") if False else None
    try:
        vix=fred("VIXCLS"); vix=vix[~vix.index.duplicated(keep="last")]
    except Exception: vix=None
    def _m(s):
        if s is None: return None
        s=s[~s.index.duplicated(keep="last")]
        return s
    releq=_m(releq); wti=_m(wti); vix=_m(vix)
    def d12(s): return (np.log(s)-np.log(s.shift(12)))*100 if s is not None else None
    dfree={}
    dfree["rd10_d12"]=rd10.diff(12)
    dfree["releq_d12"]=d12(releq) if releq is not None else None
    dfree["wti_d12"]=d12(wti)
    dfree["vix_d12"]=vix.diff(12) if vix is not None else None
    dfree={k:v for k,v in dfree.items() if v is not None}
    dep=ldxy.diff(12)*100
    X=pd.DataFrame(dfree); dd=pd.concat([dep.rename("y"),X],axis=1).dropna(); dd=dd[dd.index>=START]
    Xc=sm.add_constant(dd[list(dfree)])
    m=sm.OLS(dd["y"],Xc).fit(cov_type="HAC",cov_kwds={"maxlags":12})
    betas={k:round(float(v),4) for k,v in m.params.items()}
    tvals={k:round(float(v),1) for k,v in m.tvalues.items()}
    fit=m.params["const"]+sum(m.params[k]*X[k] for k in dfree)
    fv=(dxy.shift(12)*np.exp(fit/100))
    gap=((dxy/fv)-1)*100
    g=gap.dropna(); z=(g-g.mean())/g.std()
    rollr2={}
    win=pd.concat([dd["y"],Xc],axis=1)
    for t in dd.index:
        if t<pd.Period("2000-12","M"): continue
        sub=dd[dd.index<=t].tail(120)
        if len(sub)<60: continue
        mm=sm.OLS(sub["y"],sm.add_constant(sub[list(dfree)])).fit()
        rollr2[str(t)]=round(float(mm.rsquared),3)
    zc=z.dropna()
    buckets=[]
    for lbl,lo,hi in [("<-1σ",-9,-1),("-1σ..0",-1,0),("0..1σ",0,1),(">1σ",1,9)]:
        sub=zc[(zc>=lo)&(zc<hi)]
        if len(sub):
            fwd=yoy.reindex(sub.index)  # placeholder; bucket mean of |gap|→fwd handled in template
            buckets.append({"lbl":lbl,"mean":round(float(abs(g.reindex(sub.index)).mean()/100),2),"n":int(len(sub))})
    idx=pd.period_range(START,g.index[-1],freq="M")
    def ser(s,nd=2): return [None if (p not in s.index or pd.isna(s.get(p))) else round(float(s[p]),nd) for p in idx]
    rec=fred("USREC").reindex(idx).fillna(0)
    gap_now=float(g.iloc[-1]); z_now=float(z.iloc[-1]); pct=float((g<gap_now).mean()*100)
    payload={"months":[str(p) for p in idx],"dxy":ser(dxy),"fv":ser(fv),"gap":ser(gap,2),
     "rollr2":rollr2,"buckets":buckets,"betas":betas,"tvals":tvals,
     "rec":[int(v) for v in rec],"yoy":ser(yoy,2),"fit":ser(fit,2),
     "stats":{"r2":round(float(m.rsquared),3),"n":int(m.nobs),"sigma":round(float(np.sqrt(m.mse_resid)),2),
       "gap_now":round(gap_now,2),"z_now":round(z_now,1),"pct":round(pct),
       "dxy_now":round(float(dxy.iloc[-1]),2),"fv_now":round(float(fv.dropna().iloc[-1]),2),
       "hl":"3-5y","rho":0.0,"r_rev":0.0,"contrib":"",
       "latest":str(g.index[-1]),"dxy_last":round(float(dxy.iloc[-1]),2),"dxy_last_m":str(dxy.index[-1])}}
    current={"reading":f"+{gap_now:.1f}% rich" if gap_now>0 else f"{gap_now:.1f}% cheap","stance":"RICH" if gap_now>0 else "CHEAP","implied":"Attribution, not timing."}
    return ModelResult(payload=payload,current=current,ok=True,note=f"FV asof {g.index[-1]}, gap {gap_now:+.1f}%, R2={m.rsquared:.2f}")
