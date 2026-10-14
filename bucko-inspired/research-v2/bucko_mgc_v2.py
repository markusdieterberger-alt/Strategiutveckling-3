#!/usr/bin/env python3
"""BUCKO INSPIRED V2: preregistered MGC 5m mechanism study.
Independent hypotheses, not Bucko code. No fitted parameters.
Run: python bucko_mgc_v2.py /path/to/MGC_CANONICAL_1M_V1_0_2026-10-05.csv.gz --out results
Requires pandas/numpy. Outputs trades.csv and summary.csv.
Signals on 5m CLOSED bar, market entry at NEXT 5m open, stop-first on OHLC ties.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

POINT_VALUE=10.0  # MGC: $10 per $1 gold price move
TICK=0.1
SLIP_TICKS_EACH_SIDE=1
FEE_PER_SIDE=1.0
RR_CHOICES=(1.,2.,3.)
START_VALIDATION=pd.Timestamp("2024-01-01",tz="UTC")
START_RECENT=pd.Timestamp("2026-05-01",tz="UTC")
MAX_GAP=pd.Timedelta(minutes=5)

def load(path):
    data=pd.read_csv(path,compression="infer",low_memory=False)
    cols={str(c).lower().strip():c for c in data.columns}
    def pick(*candidates):
        for c in candidates:
            if c in cols:return cols[c]
        raise ValueError(f"Missing {candidates}; available columns={list(data.columns)}")
    t=pick("ts_event","timestamp","datetime","time","ts","date")
    op,hi,lo,cl,vo=[pick(s) for s in ("open","high","low","close","volume")]
    sym=None
    for s in ("symbol","contract","raw_symbol","instrument_id","active_contract"):
        if s in cols:sym=cols[s];break
    if sym is None:
        raise ValueError("Canonical CSV requires contract identifier to disallow mixed-roll candles.")
    ts=pd.to_datetime(data[t],utc=True)
    if ts.isna().any():raise ValueError("Invalid timestamps")
    d=pd.DataFrame({"ts":ts,"open":pd.to_numeric(data[op]),"high":pd.to_numeric(data[hi]),
                    "low":pd.to_numeric(data[lo]),"close":pd.to_numeric(data[cl]),
                    "volume":pd.to_numeric(data[vo]),"contract":data[sym].astype(str)})
    d=d.sort_values("ts",kind="stable")
    if d.ts.duplicated().any():raise ValueError("Duplicate 1m timestamps")
    # Canonical MGC has missing no-trade minutes. Strict test only accepts full 5 minute candles.
    d=d.set_index("ts")
    rule={"open":"first","high":"max","low":"min","close":"last","volume":"sum",
          "contract":["first","nunique"]}
    b=d.resample("5min",label="left",closed="left").agg(rule)
    b.columns=["open","high","low","close","volume","contract","ncontract"]
    b["nmin"]=d["close"].resample("5min").count()
    b=b.loc[(b.nmin==5)&(b.ncontract==1)].copy()
    b=b.drop(columns="ncontract")
    return b

def atr14(b):
    prev=b.close.shift(1)
    tr=pd.concat([(b.high-b.low).abs(),(b.high-prev).abs(),(b.low-prev).abs()],axis=1).max(axis=1)
    # Wilder RMA, same alpha as Pine ta.rma
    return tr.ewm(alpha=1/14,adjust=False,min_periods=14).mean()

def signals(b):
    b=b.copy()
    b["atr"]=atr14(b)
    b["ema21"]=b.close.ewm(span=21,adjust=False,min_periods=21).mean()
    b["ema50"]=b.close.ewm(span=50,adjust=False,min_periods=50).mean()
    b["ema200"]=b.close.ewm(span=200,adjust=False,min_periods=200).mean()
    up=(b.ema21>b.ema50)&(b.close>b.ema200)
    down=(b.ema21<b.ema50)&(b.close<b.ema200)
    # Sweep/reclaim: break prior 20 COMPLETE bar extrema, close back within prior range.
    priorhi=b.high.shift(1).rolling(20,min_periods=20).max()
    priorlo=b.low.shift(1).rolling(20,min_periods=20).min()
    b["sweep_long"]=(b.low<priorlo)&(b.close>priorlo)&(b.close>b.open)&up
    b["sweep_short"]=(b.high>priorhi)&(b.close<priorhi)&(b.close<b.open)&down
    # FVG zones causally created at prior bar (3-candle imbalance).
    # Bullish if low[i-1] > high[i-3], bearish if high[i-1] < low[i-3].
    # Latest zone eligible only after confirmation; signal first later touch + reclaim.
    fh=b.high.to_numpy();fl=b.low.to_numpy();fc=b.close.to_numpy();fo=b.open.to_numpy()
    u=up.fillna(False).to_numpy();dn=down.fillna(False).to_numpy()
    al=b.atr.to_numpy()
    n=len(b)
    fvl=np.zeros(n,dtype=bool);fvs=np.zeros(n,dtype=bool)
    sdl=np.zeros(n,dtype=bool);sds=np.zeros(n,dtype=bool)
    # Only zone most recently identified, expires after 30 bars; one trigger per zone.
    bull=None;bear=None
    # Supply/demand: pivot confirmed 3 bars to right, zone centered at prior pivot,
    # half width 0.25 ATR at pivot, eligibility on subsequent candles, max age 60 bars.
    demand=None;supply=None
    for i in range(206,n):
        if i>=3:
            k=i-3
            # At close of i, pivot at k is confirmed only with i's high/low.
            if k>=3 and fl[k]==min(fl[k-3:i+1]) and np.isfinite(al[k]):
                demand=(fl[k],.25*al[k],i)
            if k>=3 and fh[k]==max(fh[k-3:i+1]) and np.isfinite(al[k]):
                supply=(fh[k],.25*al[k],i)
        if bull is not None:
            lowzone,highzone,born=bull
            if i-born>30:bull=None
            elif i>born and fl[i]<=highzone:
                if fc[i]>highzone and fc[i]>fo[i] and u[i] and fl[i]>=lowzone-al[i]*.1:
                    fvl[i]=True
                bull=None # once touched (even without a confirming bounce), consumed
        if bear is not None:
            lowzone,highzone,born=bear
            if i-born>30:bear=None
            elif i>born and fh[i]>=lowzone:
                if fc[i]<lowzone and fc[i]<fo[i] and dn[i] and fh[i]<=highzone+al[i]*.1:
                    fvs[i]=True
                bear=None
        # New three-bar FVG forms at close[i]. Its first eligible retest is i+1.
        if fl[i]>fh[i-2] and (fl[i]-fh[i-2])>=.1*al[i]:bull=(fh[i-2],fl[i],i)
        if fh[i]<fl[i-2] and (fl[i-2]-fh[i])>=.1*al[i]:bear=(fh[i],fl[i-2],i)
        if demand is not None:
            level,width,born=demand
            if i-born>60:demand=None
            elif i>born and fl[i]<=level+width:
                if fl[i]>=level-width and fc[i]>level+width and fc[i]>fo[i] and u[i]:
                    sdl[i]=True
                demand=None
        if supply is not None:
            level,width,born=supply
            if i-born>60:supply=None
            elif i>born and fh[i]>=level-width:
                if fh[i]<=level+width and fc[i]<level-width and fc[i]<fo[i] and dn[i]:
                    sds[i]=True
                supply=None
    b["fvg_long"]=fvl;b["fvg_short"]=fvs
    b["zone_long"]=sdl;b["zone_short"]=sds
    return b

def simulate(b,model,rr):
    times=b.index.to_numpy()
    o=b.open.to_numpy();h=b.high.to_numpy();l=b.low.to_numpy();c=b.close.to_numpy()
    a=b.atr.to_numpy();contract=b.contract.to_numpy()
    long=b[f"{model}_long"].fillna(False).to_numpy()
    short=b[f"{model}_short"].fillna(False).to_numpy()
    rows=[]
    i=205
    # One position per model at a time; entries only at next bar open.
    while i<len(b)-1:
        if not(long[i] or short[i]) or not np.isfinite(a[i]):
            i+=1;continue
        side=1 if long[i] else -1
        j=i+1
        # Don't enter after a discontinuity / roll.
        if pd.Timestamp(times[j])-pd.Timestamp(times[i])!=MAX_GAP or contract[i]!=contract[j]:
            i=j;continue
        risk=1.5*a[i]
        if risk<=TICK or not np.isfinite(risk):i=j;continue
        entry=o[j]+side*SLIP_TICKS_EACH_SIDE*TICK
        stop=entry-side*risk
        target=entry+side*risk*rr
        k=j
        while k<len(b):
            if k>j and (pd.Timestamp(times[k])-pd.Timestamp(times[k-1])!=MAX_GAP or contract[k]!=contract[k-1]):
                # Force exit at first observed open after interrupted series / contract change.
                raw=o[k];reason="gap_or_roll"
                break
            if side==1:
                hitstop=l[k]<=stop;hittarget=h[k]>=target
            else:
                hitstop=h[k]>=stop;hittarget=l[k]<=target
            if hitstop:
                raw=stop;reason="stop_or_samebar_stop_first";break
            if hittarget:
                raw=target;reason="target";break
            k+=1
        if k>=len(b):
            k=len(b)-1;raw=c[k];reason="end_of_data"
        exitpx=raw-side*SLIP_TICKS_EACH_SIDE*TICK
        pnl=(exitpx-entry)*side*POINT_VALUE-2*FEE_PER_SIDE
        rows.append((model,rr,str(times[i]),str(times[j]),str(times[k]),
                     side,contract[j],entry,stop,target,exitpx,round(pnl,5),reason))
        i=k+1
    return pd.DataFrame(rows,columns=["model","rr","signal_utc","entry_utc","exit_utc",
                                       "side","contract","entry","stop","target","exit",
                                       "net_usd","exit_reason"])

def stats(trades,period):
    if period=="development":
        subset=trades[pd.to_datetime(trades.entry_utc,utc=True)<START_VALIDATION]
    elif period=="validation":
        dt=pd.to_datetime(trades.entry_utc,utc=True)
        subset=trades[(dt>=START_VALIDATION)&(dt<START_RECENT)]
    elif period=="recent":
        subset=trades[pd.to_datetime(trades.entry_utc,utc=True)>=START_RECENT]
    else:subset=trades
    p=subset.net_usd
    wins=float(p[p>0].sum());losses=float(-p[p<0].sum())
    eq=p.cumsum()
    dd=(eq-eq.cummax().clip(lower=0)).min() if len(eq) else 0.
    return {"n":len(p),"net":round(float(p.sum()),2),
            "pf":round(wins/losses,3) if losses else None,
            "win_rate":round(float((p>0).mean()),4) if len(p) else None,
            "max_closed_dd":round(float(-dd),2),"avg_net":round(float(p.mean()),2) if len(p) else None}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("csv_gz");ap.add_argument("--out",default="bucko_v2_results")
    args=ap.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    b=signals(load(args.csv_gz))
    records=[];alltrades=[]
    for model in ("sweep","fvg","zone"):
        for rr in RR_CHOICES:
            t=simulate(b,model,rr);alltrades.append(t)
            for period in ("development","validation","recent","all"):
                records.append(dict(model=model,rr=rr,period=period,**stats(t,period)))
    pd.concat(alltrades,ignore_index=True).to_csv(out/"trades.csv",index=False)
    pd.DataFrame(records).to_csv(out/"summary.csv",index=False)
    print(pd.DataFrame(records).to_string(index=False))
    print(f"5m bars: {len(b)}; {b.index.min()} – {b.index.max()}")
if __name__=="__main__":main()
