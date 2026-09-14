"""Treasury Premium (JKL convenience-yield) — two CIP-hedged proxies, stress-test."""
import numpy as np, pandas as pd, statsmodels.api as sm
from .common import fred, ecb, boc_valet, dxy_monthly
from .base import ModelResult
TAB="cy"; VAR="CY"
META=("Treasury Premium","reserve demand","JKL convenience-yield reconstruction stress-test — not replicable from public data; crisis flight-to-bills gauge survives.","treasury_premium_proxy")

def _wmean(cols,w):
    df=pd.DataFrame(cols); w=pd.Series(w)
    return df.apply(lambda r:(r.dropna()*w[r.dropna().index]).sum()/w[r.dropna().index].sum() if r.dropna().size else np.nan,axis=1)

def build()->ModelResult:
    dxy=dxy_monthly(); y=(dxy/dxy.shift(12)-1)*100; ldxy=np.log(dxy)
    us1=fred("GS1")
    ea1=ecb("YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y","D")
    ea1=ea1.to_timestamp().resample("ME").mean().to_period("M") if hasattr(ea1.index,'to_timestamp') else ea1
    ca1=boc_valet("TB.CDN.1Y.MID","M")
    i3={"US":fred("IR3TIB01USM156N"),"EA":fred("IR3TIB01DEM156N"),"JP":fred("IR3TIB01JPM156N"),"CA":fred("IR3TIB01CAM156N")}
    us_spr=us1-i3["US"]
    # JGB 1y via MOF is heavy; approximate JP leg with JGB from DBnomics-less path skipped -> EUR+CAD only for proxy A
    prem={"EUR":((ea1-i3["EA"])-us_spr)*100,"CAD":((ca1-i3["CA"])-us_spr)*100}
    prem1=_wmean(prem,{"EUR":.576,"CAD":.091}).dropna()
    # proxy B: matched 3m bill premium
    ea3=ecb("YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_3M","D")
    ea3=ea3.to_timestamp().resample("ME").mean().to_period("M") if hasattr(ea3.index,'to_timestamp') else ea3
    ca3=boc_valet("TB.CDN.90D.MID","M"); tb3=fred("TB3MS")
    us_bp=i3["US"]-tb3; eur_bp=i3["EA"]-ea3; cad_bp=i3["CA"]-ca3
    premC=_wmean({"EUR":(us_bp-eur_bp)*100,"CAD":(us_bp-cad_bp)*100},{"EUR":.576,"CAD":.091}).dropna()
    def prof(x):
        o={}
        for k in range(0,19):
            d=pd.concat([x.shift(k),y],axis=1).dropna()
            o[str(k)]=round(float(d.corr().iloc[0,1]),3) if len(d)>60 else None
        return o
    def cont(x):
        d=pd.concat([x.diff(12),y],axis=1).dropna(); return round(float(d.corr().iloc[0,1]),2)
    def fwdtab(x):
        rows=[]
        for h in [3,6,12,24]:
            fwd=(ldxy.shift(-h)-ldxy)*100
            d=pd.concat([x,fwd],axis=1,keys=["p","f"]).dropna()
            m=sm.OLS(d["f"],sm.add_constant(d["p"])).fit(cov_type="HAC",cov_kwds={"maxlags":h})
            rows.append({"h":h,"b":round(float(m.params["p"]*100),2),"t":round(float(m.tvalues["p"]),1)})
        return rows
    idx=pd.period_range(pd.Period("2001-01","M"),max(prem1.index[-1],premC.index[-1]),freq="M")
    def ser(s,nd=1): return [None if (p not in s.index or pd.isna(s.get(p))) else round(float(s[p]),nd) for p in idx]
    rec=fred("USREC").reindex(idx).fillna(0)
    events=[["2008-10","GFC: flight to bills"],["2011-11","euro crisis: bund bid"],["2020-03","COVID dash for cash"],["2022-04","Fed front-loading"]]
    payload={"months":[str(p) for p in idx],"prem1":ser(prem1),"premC":ser(premC),
     "legs":{"EUR_1y":ser(prem["EUR"]),"JPY_1y":[None]*len(idx),"CAD_1y":ser(prem["CAD"]),
             "EUR_3m":ser((us_bp-eur_bp)*100),"CAD_3m":ser((us_bp-cad_bp)*100)},
     "yoy":ser(y),"rec":[int(v) for v in rec],
     "prof1":prof(prem1),"profC":prof(premC),"fwd1":fwdtab(prem1),"fwdC":fwdtab(premC),
     "events":[{"m":m,"lbl":l,"v1":None,"vC":(round(float(premC[pd.Period(m,'M')]),1) if pd.Period(m,'M') in premC.index else None)} for m,l in events],
     "stats":{"c1":cont(prem1),"cC":cont(premC),
       "now1":round(float(prem1.dropna().iloc[-1]),1),"nowC":round(float(premC.dropna().iloc[-1]),1),
       "latest":str(premC.dropna().index[-1]),"meanC":round(float(premC.mean()),1),"sdC":round(float(premC.std()),1),
       "maxC":round(float(premC.max()),1),"maxC_m":str(premC.idxmax()),"n":int(len(premC.dropna())),
       "dxy_last":round(float(dxy.dropna().iloc[-1]),2),"dxy_last_m":str(dxy.dropna().index[-1])}}
    current={"reading":f"+{premC.dropna().iloc[-1]:.0f}bp","stance":"NOT REPLICABLE","implied":"Crisis flight-to-bills gauge only."}
    return ModelResult(payload=payload,current=current,ok=True,note=f"CY asof {premC.dropna().index[-1]}, cC={payload['stats']['cC']}")
