"""Twin Deficit — federal budget + current account (% GDP), 4Q avg, pushed 7Q."""
import numpy as np, pandas as pd
from .common import fred, dxy_monthly
from .base import ModelResult
TAB="twin"; VAR="DATA"
META=("Twin Deficit","flow","Fiscal + current-account balances against DXY — the external-financing channel.","twin_deficit_dxy")
LEAD=7

def _yq(p): return p.year+(p.quarter-1)/4.0
def _ym(p): return p.year+(p.month-1)/12.0

def build()->ModelResult:
    gdp=fred("GDP","Q")
    # federal budget balance, 4Q sum / 4Q GDP
    bal=fred("MTSDS133FMS").rolling(12).sum(); bal_q=bal.copy(); bal_q.index=bal_q.index.asfreq("Q"); bal_q=bal_q.groupby(level=0).last()
    budget=(bal_q/1000)/gdp*100
    # current account (% GDP): BOPBCA (older) spliced with IEABC/GDP
    ca=fred("NETEXP","Q")/gdp*100   # net exports as CA proxy (long, continuous)
    twin=(budget+ca).rolling(4).mean().dropna()
    dxy=dxy_monthly()
    twin_push=twin.copy(); twin_push.index=[_yq(p)+LEAD/4.0 for p in twin.index]
    now=float(twin.iloc[-1])
    payload={
     "twin":[[round(_yq(p)+LEAD/4.0,4),round(float(v),3)] for p,v in twin.items()],
     "dxy":[[round(_ym(p),4),round(float(v),2)] for p,v in dxy.items()],
     "rec":[[round(_ym(p),4),int(v)] for p,v in fred("USREC").items() if p>=pd.Period("1972-01","M")],
     "meta":{"built":pd.Timestamp.today().strftime("%d %b %Y"),"x_max":float(int(_yq(twin.index[-1]))+LEAD/4.0+1),
       "proj_x":round(_yq(twin.index[-1]),2),"lead":LEAD,"twin_last_actual_q":str(twin.index[-1]),
       "twin_last_val":round(now,1),"twin_last_actualY":round(_yq(twin.index[-1]),2),
       "twin_last_projY":round(_yq(twin.index[-1])+LEAD/4.0,2),
       "dxy_last_val":round(float(dxy.iloc[-1]),1),"dxy_last_m":str(dxy.index[-1]),
       "twin_now":round(now,1),"budget_now":round(float(budget.iloc[-1]),1),"ca_now":round(float(ca.rolling(4).mean().iloc[-1]),1)}}
    current={"reading":f"{now:.1f}% GDP","stance":"USD- backdrop","implied":"Structurally wide headwind."}
    return ModelResult(payload=payload,current=current,ok=True,note=f"Twin asof {twin.index[-1]}, {now:.1f}% GDP")
