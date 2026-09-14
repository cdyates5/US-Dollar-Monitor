"""Real Money (Ward/NS Partners) — relative real narrow money, US minus foreign."""
import numpy as np, pandas as pd, statsmodels.api as sm
from .common import fred, ecb, dxy_monthly, zscore, dbnomics, boj_m1_yoy
from .base import ModelResult
TAB="ward"; VAR="WD"
META=("Real Money","liquidity","Ward-spec relative real narrow money — the third money differential tested; the gap fails, the foreign side faintly leads.","relative_real_narrow_money")
START=pd.Period("1997-06","M")

def build()->ModelResult:
    us_m1a=fred("CURRSL")+fred("DEMDEPSL"); us_cpi=fred("CPIAUCSL")
    ea_m1=ecb("BSI/M.U2.Y.V.M10.X.1.U2.2300.Z01.E","M"); ea_cpi=fred("CP0000EZ19M086NEST")
    # Japan M1: OECD level base spliced forward via BOJ YoY
    base=fred("MANMM101JPM189S"); yoy=boj_m1_yoy()
    jp=base.copy()
    for p in pd.period_range(base.index[-1]+1,yoy.index[-1],freq="M"):
        if p in yoy.index and (p-12) in jp.index: jp[p]=jp[p-12]*(1+yoy[p]/100)
    jp=jp.sort_index()
    jp_cpi=dbnomics("IMF/CPI/M.JP.PCPI_IX","M")
    tgt=us_cpi.index[-1]
    if jp_cpi.index[-1]<tgt:
        yy=jp_cpi.iloc[-1]/jp_cpi.iloc[-13]-1; mr=(1+yy)**(1/12)
        ext=pd.period_range(jp_cpi.index[-1]+1,tgt,freq="M")
        jp_cpi=pd.concat([jp_cpi,pd.Series([jp_cpi.iloc[-1]*mr**(i+1) for i in range(len(ext))],index=ext)])
    def mom6(x): return 100*((x/x.shift(6))**2-1)
    mUS=mom6(us_m1a/us_cpi); mEA=mom6(ea_m1/ea_cpi); mJP=mom6(jp/jp_cpi)
    def wmean(cols,w):
        df=pd.DataFrame(cols); w=pd.Series(w)
        return df.apply(lambda r:(r.dropna()*w[r.dropna().index]).sum()/w[r.dropna().index].sum() if r.dropna().size else np.nan,axis=1)
    mF=wmean({"EA":mEA,"JP":mJP},{"EA":.576,"JP":.136})
    diff=(mUS-mF).dropna()
    dxy=dxy_monthly(); y=(dxy/dxy.shift(12)-1)*100
    d97=diff[diff.index>=START]; mF97=mF[mF.index>=START]; mUS97=mUS[mUS.index>=START]
    def prof(x):
        o={}
        for k in range(0,19):
            dd=pd.concat([x.shift(k),y],axis=1).dropna(); dd=dd[dd.index>=START]
            o[str(k)]=round(float(dd.corr().iloc[0,1]),3) if len(dd)>60 else None
        return o
    pd_,pf,pu=prof(d97),prof(-mF97),prof(mUS97)
    pk=max(range(0,19),key=lambda k:abs(pd_[str(k)] or 0))
    pkF=max(range(0,19),key=lambda k:(pf[str(k)] or 0))
    def nw(x,k):
        dd=pd.concat([x.shift(k),y],axis=1,keys=["x","y"]).dropna(); dd=dd[dd.index>=START]
        m=sm.OLS(dd["y"],sm.add_constant(dd["x"])).fit(cov_type="HAC",cov_kwds={"maxlags":12})
        return round(float(m.tvalues["x"]),1)
    def era(x,lo,hi,k=9):
        dd=pd.concat([x.shift(k),y],axis=1).dropna(); dd=dd[(dd.index>=pd.Period(lo,"M"))&(dd.index<=pd.Period(hi,"M"))]
        return round(float(dd.corr().iloc[0,1]),2)
    idx=pd.period_range(START,y.dropna().index[-1],freq="M")
    def ser(s,nd=1): return [None if (p not in s.index or pd.isna(s.get(p))) else round(float(s[p]),nd) for p in idx]
    rec=fred("USREC").reindex(idx).fillna(0)
    payload={"months":[str(p) for p in idx],"mUS":ser(mUS),"mF":ser(mF),"diff":ser(diff),"yoy":ser(y),
     "rec":[int(v) for v in rec],"prof_diff":pd_,"prof_finv":pf,"prof_us":pu,
     "stats":{"pk":pk,"r_pk":pd_[str(pk)],"t9":nw(d97,9),"n":int(len(pd.concat([d97.shift(9),y],axis=1).dropna())),
       "e1":era(d97,"1997-06","2011-12"),"e2":era(d97,"2012-01","2026-05"),
       "pkF":pkF,"rF":pf[str(pkF)],"tF":nw(-mF97,pkF),
       "now_diff":round(float(diff.dropna().iloc[-1]),1),"now_us":round(float(mUS.dropna().iloc[-1]),1),
       "now_f":round(float(mF.dropna().iloc[-1]),1),"latest":str(diff.dropna().index[-1]),
       "dxy_last":round(float(dxy.dropna().iloc[-1]),2),"dxy_last_m":str(dxy.dropna().index[-1])}}
    current={"reading":f"+{diff.dropna().iloc[-1]:.1f}pp","stance":"NO LEAD","implied":"Foreign side faintly leads."}
    return ModelResult(payload=payload,current=current,ok=True,note=f"Ward asof {diff.dropna().index[-1]}, t9={payload['stats']['t9']}")
