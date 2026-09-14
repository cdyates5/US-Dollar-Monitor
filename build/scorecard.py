"""Synthesise the scorecard tab from this run's current readings, emitting the
exact row schema the template renders (tab,name,ch,rd,sb,chip,hz,ev,note,group).
Models that were stubs/failed fall back to their last-verified static row."""
import re, json, datetime

# last hand-verified rows (full template schema)
FALLBACK = {
 "lead":{"tab":1,"name":"Lead Index","ch":"direction","rd":"+0.42\u03c3","sb":"composite","chip":["USD+","pos"],"hz":"6m","ev":"r 0.48 IS \u00b7 0.46 OOS \u00b7 65% hit","note":"Implied DXY YoY +3.8%.","group":"live"},
 "fv":{"tab":2,"name":"Fair Value","ch":"valuation","rd":"+7.8% rich","sb":"+1.2\u03c3 \u00b7 87th pctile","chip":["RICH","rich"],"hz":"spot","ev":"R\u00b2 0.32 \u00b7 gap\u2192fwd r 0.00","note":"Attribution, not timing.","group":"lens"},
 "curve":{"tab":3,"name":"Real Curve","ch":"rates","rd":"255bp","sb":"real 10s\u20133m","chip":["USD+","pos"],"hz":"6\u20139m","ev":"r +0.34 at peak","note":"Implied ~+1.3% at ~8m.","group":"live"},
 "twin":{"tab":4,"name":"Twin Deficit","ch":"flow","rd":"\u22128.8% GDP","sb":"4Q avg \u00b7 pushed 7Q","chip":["USD- backdrop","neg"],"hz":"7Q","ev":"external-financing","note":"Structurally wide headwind.","group":"lens"},
 "jiang":{"tab":5,"name":"Fiscal Cycle","ch":"fiscal","rd":"\u22124.2%","sb":"surplus / debt","chip":["DEAD SINCE 2017","dead"],"hz":"\u2014","ev":"in-window t 1.9 \u00b7 2018+ inverts","note":"Impulse leads; level does not.","group":"dead"},
 "nxa":{"tab":6,"name":"External Position","ch":"external","rd":"+0.53\u03c3","sb":"Gourinchas\u2013Rey nxa","chip":["DECAYED","dead"],"hz":"\u2014","ev":"era 0.70\u21920.22 \u00b7 OOS 0.03","note":"Overridden by reserve demand.","group":"dead"},
 "cy":{"tab":7,"name":"Treasury Premium","ch":"reserve demand","rd":"+5bp","sb":"matched-3m proxy","chip":["NOT REPLICABLE","dead"],"hz":"\u2014","ev":"needs FX fwds \u00b7 r \u22120.05","note":"Crisis flight-to-bills gauge.","group":"dead"},
 "ward":{"tab":8,"name":"Real Money","ch":"liquidity","rd":"+13.4pp","sb":"Ward gap","chip":["NO LEAD","dead"],"hz":"\u2014","ev":"3rd spec \u00b7 t 0.9 \u00b7 flips","note":"Foreign side faintly leads.","group":"dead"},
 "pmi":{"tab":9,"name":"PMI Differential","ch":"growth","rd":"+0.57","sb":"US \u2212 partners \u00b7 adv 4m","chip":["USD+ mild","pos"],"hz":"~4m","ev":"peak corr at 4m","note":"US mfg above partners.","group":"live"},
 "ppp":{"tab":10,"name":"PPP Overvaluation","ch":"long-run","rd":"+29.6%","sb":"real DXY vs CPI","chip":["USD- secular","neg"],"hz":"10y","ev":"R\u00b2 0.52 \u00b7 t \u22126.7","note":"~ \u22123.7%/yr over the decade.","group":"live"},
 "hedge":{"tab":11,"name":"Hedging Pressure","ch":"flows","rd":"\u22120.52","sb":"SPX\u2013DXY 60d corr","chip":["PRESSURE OFF","calm"],"hz":"dial","ev":"2025 wave captured","note":"Natural hedge restored.","group":"lens"},
 "risk":{"tab":12,"name":"Forex Risk","ch":"positioning","rd":"7.0/100","sb":"low risk \u00b7 loose liq","chip":["USD+ low conv.","pos"],"hz":"12m","ev":"R\u00b2 \u2248 0.12","note":"Implied +3.7% firmer.","group":"live"},
}
ORDER=["lead","fv","curve","twin","jiang","nxa","cy","ward","pmi","ppp","hedge","risk"]

def build_scorecard(currents: dict, template_path) -> str:
    rows=[]
    for t in ORDER:
        row=dict(FALLBACK[t]); cur=currents.get(t)
        if cur:
            if cur.get("reading"): row["rd"]=cur["reading"]
            if cur.get("stance"):
                cls="pos" if cur["stance"].startswith("USD+") else ("neg" if cur["stance"].startswith("USD-") else row["chip"][1])
                row["chip"]=[cur["stance"],cls]
            if cur.get("implied"): row["note"]=cur["implied"]
        rows.append(row)
    html=template_path.read_text()
    repl="const ROWS_DATA = "+json.dumps(rows,separators=(",",":"))+";"
    html=re.sub(r"const ROWS_DATA\s*=\s*(\{.*?\}|\[.*?\]);", lambda m: repl, html, count=1, flags=re.S)
    html=html.replace("__BUILDSTAMP__", datetime.date.today().isoformat())
    return html
