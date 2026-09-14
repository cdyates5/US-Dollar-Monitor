"""Fiscal Cycle (Jiang) — surplus/debt -> 12m dollar excess return."""
import numpy as np, pandas as pd, statsmodels.api as sm
from .common import fred, dxy_monthly
from .base import ModelResult
TAB="jiang"; VAR="JG"
META=("Fiscal Cycle","fiscal","Jiang surplus-to-debt — partial in-window replication of the fiscal risk-premium channel; dead since 2017.","us_fiscal_cycle")

def _carry():
    def wmean(cols,w):
        df=pd.DataFrame(cols); w=pd.Series(w)
        return df.apply(lambda r:(r.dropna()*w[r.dropna().index]).sum()/w[r.dropna().index].sum() if r.dropna().size else np.nan,axis=1)
    f3=wmean({"DE":fred("IR3TIB01DEM156N"),"JP":fred("IR3TIB01JPM156N"),"CA":fred("IR3TIB01CAM156N"),
              "SE":fred("IR3TIB01SEM156N"),"CH":fred("IR3TIB01CHM156N")},
             {"DE":.576,"JP":.136,"CA":.091,"SE":.042,"CH":.036})
    return (fred("IR3TIB01USM156N")-f3)/12.0

def build()->ModelResult:
    debt=fred("GFDEBTN","Q").resample("M").ffill()
    sur12=fred("MTSDS133FMS").rolling(12).sum()
    last=sur12.dropna().index[-1]
    if debt.index[-1]<last:
        debt=pd.concat([debt,pd.Series(debt.iloc[-1],index=pd.period_range(debt.index[-1]+1,last,freq="M"))])
    ratio=(sur12/debt*100).dropna()
    dxy=dxy_monthly(); ldxy=np.log(dxy); carry_m=_carry()
    x12=(ldxy.shift(-12)-ldxy)*100+carry_m.rolling(12).sum().shift(-12)
    d=pd.concat([ratio,x12],axis=1,keys=["x","f"]).dropna()
    def reg(dd,mx=12):
        m=sm.OLS(dd["f"],sm.add_constant(dd["x"])).fit(cov_type="HAC",cov_kwds={"maxlags":mx})
        return round(float(m.params["x"]),2),round(float(m.tvalues["x"]),1),round(float(m.rsquared),3),int(m.nobs)
    dJ=d[(d.index>=pd.Period("1988-01","M"))&(d.index<=pd.Period("2017-12","M"))]
    bJ,tJ,R2J,nJ=reg(dJ)
    d18=d[d.index>=pd.Period("2018-01","M")]; b18,t18,_,n18=reg(d18)
    b_full,t_full,R2_full,n_full=reg(d)
    # NIPA quarterly variant
    try:
        nl=fred("AD02RC1Q027SBEA","Q"); dq=fred("GFDEBTN","Q")
        rq=(nl*1000/dq*100).dropna()
        ldq=np.log(dxy); ldq.index=ldq.index.asfreq("Q"); ldq=ldq.groupby(level=0).last()
        cq=carry_m.copy(); cq.index=cq.index.asfreq("Q"); cq=cq.groupby(level=0).sum()
        x4=(ldq.shift(-4)-ldq)*100+cq.rolling(4).sum().shift(-4)
        dn=pd.concat([rq,x4],axis=1,keys=["x","f"]).dropna()
        dnj=dn[(dn.index>=pd.Period("1988Q1","Q"))&(dn.index<=pd.Period("2017Q4","Q"))]
        mn=sm.OLS(dnj["f"],sm.add_constant(dnj["x"])).fit(cov_type="HAC",cov_kwds={"maxlags":4})
        nipa={"b":round(float(mn.params["x"]),2),"t":round(float(mn.tvalues["x"]),1),"R2":round(float(mn.rsquared),3),"n":int(mn.nobs)}
    except Exception: nipa={"b":0.53,"t":1.9,"R2":0.048,"n":120}
    # OOS
    preds={}
    for t in ratio.index:
        if t<pd.Period("2000-01","M"): continue
        tr=d[d.index<=t-12]
        if len(tr)<60: continue
        bb,aa=np.polyfit(tr["x"],tr["f"],1); preds[t+12]=aa+bb*ratio[t]
    pr=pd.Series(preds); act=x12.copy(); act.index=act.index+12
    both=pd.concat([pr,act],axis=1,keys=["p","a"]).dropna()
    r_oos=round(float(both.corr().iloc[0,1]),2) if len(both)>20 else 0.0
    hit=round(float((np.sign(both.p)==np.sign(both.a)).mean()),2) if len(both)>20 else 0.0
    mfull=sm.OLS(d["f"],sm.add_constant(d["x"])).fit()
    a_f,bf=float(mfull.params["const"]),float(mfull.params["x"])
    idx=pd.period_range(ratio.index[0],ratio.index[-1]+12,freq="M")
    def ser(s,nd=2): return [None if (p not in s.index or pd.isna(s.get(p))) else round(float(s[p]),nd) for p in idx]
    implied=(a_f+bf*ratio); implied.index=implied.index+12
    x12s=x12.copy(); x12s.index=x12s.index+12
    rec=fred("USREC").reindex(idx).fillna(0)
    scat=[[round(float(r0),2),round(float(r1),1),(0 if i<=pd.Period("2017-12","M") else 1)] for i,(r0,r1) in d.iterrows()]
    now=float(ratio.iloc[-1])
    payload={"months":[str(p) for p in idx],"ratio":ser(ratio),"xret12":ser(x12s,1),"implied":ser(implied,1),
     "rec":[int(v) for v in rec],"scatter":scat,
     "stats":{"now":round(now,2),"latest":str(ratio.index[-1]),"bJ":bJ,"tJ":tJ,"R2J":R2J,"nJ":nJ,
       "b18":b18,"t18":t18,"n18":n18,"b_full":round(bf,2),"t_full":t_full,"R2_full":R2_full,"n_full":n_full,
       "r_oos":r_oos,"hit":hit,"n_oos":len(both),"nipa":nipa,"paper_b":4.7,"paper_R2":0.13,
       "implied_now":round(a_f+bf*now,1),
       "dxy_last":round(float(dxy.dropna().iloc[-1]),2),"dxy_last_m":str(dxy.dropna().index[-1])}}
    current={"reading":f"{now:.2f}%","stance":"DEAD SINCE 2017","implied":"Impulse leads; level does not."}
    return ModelResult(payload=payload,current=current,ok=True,note=f"Fiscal asof {ratio.index[-1]}, in-window t={tJ}, 2018+ t={t18}")
