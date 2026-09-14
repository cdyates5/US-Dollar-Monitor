"""External Position (Gourinchas-Rey nxa) — NIIP + net exports, detrended."""
import numpy as np, pandas as pd, statsmodels.api as sm
from .common import fred, dxy_monthly, zscore
from .base import ModelResult
TAB="nxa"; VAR="NXA"
META=("External Position","external","Net foreign assets + net exports (Gourinchas-Rey) — a classical dollar lead whose power has decayed in the reserve-currency era.","us_external_position_nxa")
K=4

def build()->ModelResult:
    niip_a=fred("IIPUSNETIA","Y"); niip_q=fred("IIPUSNETIQ","Q")
    netexp=fred("NETEXP","Q"); gdp=fred("GDP","Q")
    full=pd.period_range("1976Q1",niip_q.index[-1],freq="Q")
    niip=pd.Series(index=full,dtype=float)
    for yr,v in niip_a.items():
        q4=pd.Period(f"{yr.year}Q4","Q")
        if q4 in niip.index: niip[q4]=v
    niip=niip.interpolate(limit_direction="both")
    for p,v in niip_q.items():
        if p in niip.index: niip[p]=v
    niip=niip.loc["1976Q1":]
    nfa_gdp=((niip/1000)/gdp).reindex(full)
    nx_gdp=(netexp/gdp).reindex(full)
    dxy=dxy_monthly(); dxy_q=dxy.copy(); dxy_q.index=dxy_q.index.asfreq("Q"); dxy_q=dxy_q.groupby(level=0).last()
    ldxy=np.log(dxy_q)
    def dt(s,deg=2):
        x=np.arange(len(s)); m=s.notna().values
        c=np.polyfit(x[m],s.values[m],deg); return s-np.polyval(c,x)
    nfa_c=zscore(dt(nfa_gdp)); nx_c=zscore(dt(nx_gdp)); nxa=(nfa_c+nx_c).dropna()
    fwd=(ldxy.shift(-K)-ldxy)*100
    pair=pd.concat([nxa,fwd],axis=1,keys=["n","f"]).dropna()
    m=sm.OLS(pair["f"],sm.add_constant(pair["n"])).fit(cov_type="HAC",cov_kwds={"maxlags":K})
    a,b=float(m.params["const"]),float(m.params["n"]); r_is=float(np.sqrt(m.rsquared)); t_nw=float(m.tvalues["n"])
    def subr(lo,hi):
        seg=pair[(pair.index>=pd.Period(lo,"Q"))&(pair.index<=pd.Period(hi,"Q"))]
        return round(float(seg.corr().iloc[0,1]),2),len(seg)
    eras=[("1976–90","1976Q1","1990Q4"),("1991–04","1991Q1","2004Q4"),("2005–26","2005Q1","2026Q4")]
    era_r=[{"lbl":l,"r":subr(lo,hi)[0],"n":subr(lo,hi)[1]} for l,lo,hi in eras]
    roll=pair["n"].rolling(40).corr(pair["f"])
    prof={}
    for k in range(1,13):
        fk=(ldxy.shift(-k)-ldxy)*100
        dk=pd.concat([nxa,fk],axis=1,keys=["n","f"]).dropna()
        if len(dk)<30: continue
        mk=sm.OLS(dk["f"],sm.add_constant(dk["n"])).fit(cov_type="HAC",cov_kwds={"maxlags":max(1,k)})
        prof[str(k)]=round(float(np.sign(mk.params["n"])*np.sqrt(mk.rsquared)),3)
    preds={}
    for t in nxa.index:
        if t<pd.Period("1995Q1","Q"): continue
        sn=nfa_gdp.loc[:t]; sx=nx_gdp.loc[:t]
        if sn.notna().sum()<40: continue
        zc=zscore(dt(sn))+zscore(dt(sx))
        ptr=pd.concat([zc,fwd],axis=1,keys=["n","f"]).dropna(); ptr=ptr[ptr.index<=t-K]
        if len(ptr)<30: continue
        bb,aa=np.polyfit(ptr["n"],ptr["f"],1); preds[t+K]=aa+bb*zc.loc[t]
    pr=pd.Series(preds); act=fwd.copy(); act.index=act.index+K
    both=pd.concat([pr,act],axis=1,keys=["p","a"]).dropna()
    r_oos=round(float(both.corr().iloc[0,1]),2) if len(both)>20 else 0.0
    hit=round(float((np.sign(both.p)==np.sign(both.a)).mean()),2) if len(both)>20 else 0.0
    cur=float(nxa.iloc[-1]); pct=float((nxa<cur).mean()*100); roll_now=float(roll.dropna().iloc[-1])
    qs=pd.period_range(nxa.index[0],nxa.index[-1]+K,freq="Q")
    def ser(s,nd=2): return [None if (p not in s.index or pd.isna(s.get(p))) else round(float(s[p]),nd) for p in qs]
    implied=(a+b*nxa); implied.index=implied.index+K
    recm=fred("USREC"); rq=recm.copy(); rq.index=rq.index.asfreq("Q"); rec_q=rq.groupby(level=0).max()
    eof=lambda p:0 if p.year<1991 else (1 if p.year<2005 else 2)
    scat=[[round(float(v0),2),round(float(v1),1),eof(i)] for i,(v0,v1) in pair.iterrows()]
    payload={"quarters":[str(p) for p in qs],"nxa":ser(nxa),"niip_gdp":ser(nfa_gdp*100,1),"nx_gdp":ser(nx_gdp*100,1),
     "dxy":ser(dxy_q),"implied":ser(implied,1),"roll":ser(roll),
     "rec":[int(rec_q.get(p,0)) if p in rec_q.index else 0 for p in qs],
     "profile":prof,"eras":era_r,"scatter":scat,
     "stats":{"K":K,"a":round(a,2),"b":round(b,2),"r_is":round(r_is,2),"R2":round(float(m.rsquared),3),
       "t_nw":round(t_nw,1),"n_is":int(m.nobs),"r_oos":r_oos,"hit":hit,
       "cur_nxa":round(cur,2),"cur_q":str(nxa.index[-1]),"pct":round(pct),"roll_now":round(roll_now,2),
       "implied_now":round(a+b*cur,1),"target_q":str(nxa.index[-1]+K),
       "nfa_now":round(float(nfa_c.iloc[-1]),2),"nx_now":round(float(nx_c.iloc[-1]),2),
       "dxy_last":round(float(dxy_q.dropna().iloc[-1]),2),"dxy_last_q":str(dxy_q.dropna().index[-1])}}
    current={"reading":f"{cur:+.2f}\u03c3","stance":"DECAYED","implied":"Overridden by reserve demand."}
    return ModelResult(payload=payload,current=current,ok=True,note=f"nxa asof {nxa.index[-1]}, era 0.70->{era_r[2]['r']}, OOS {r_oos}")
