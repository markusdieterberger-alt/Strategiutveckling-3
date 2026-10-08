#!/usr/bin/env python3
"""VP-DS180 Canonical v1.0

Frozen research-to-automation implementation for MNQ 1m.

Strategy:
- Chicago time, standard 1m bars.
- Rolling 180-minute volume profile, frozen at each 5-minute boundary.
- 60 bins, 70% value area.
- Balance filter: comp<=1.0, efficiency<=0.35, inside-value closes>=0.65.
- Signal session 07:00:00 through 14:29:59 CT.
- Continuation/acceptance: first 1m close crossing outside VAH/VAL.
- Rejection: wick outside value + directional close back inside.
- Entry: next 1m open.
- Automation gate: signal-close-to-stop distance >= 4.0 index points.
- Continuation stop: 10% VA width back inside edge.
- Rejection stop: 1 MNQ tick (0.25) beyond signal wick.
- Trail: 0.35R, stop-first, updated after bar survives and active next minute.
- Shared cooldown: 30 minutes after exit.
- Max hold: 60 minutes. Flat no later than 14:59 CT.
- Benchmark friction: subtract 0.5 index point total adverse round-trip price friction.
- No commissions (funded research convention).

The signal-close min-risk gate is deliberate: it makes the decision fully causal and
portable to TradingView/Pine before the next-open fill is known.
"""
from __future__ import annotations
import argparse, json, math, os
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit, prange

TZ = "America/Chicago"
TICK = 0.25
LOOKBACK = 180
NBINS = 60
VA_PCT = 0.70
TRAIL_R = 0.35
COOLDOWN_MIN = 30
MAX_HOLD = 60
MIN_SIGNAL_RISK_PTS = 4.0
FRICTION_PTS = 0.5
START_MIN = 7 * 60
LAST_SIGNAL_MIN = 14 * 60 + 29
LAST_ENTRY_MIN = 14 * 60 + 30
FLAT_MIN = 14 * 60 + 59


def load_csv_to_daygrid(path: str, condition_path: str | None = None,
                        min_date: str | None = None) -> dict:
    head = pd.read_csv(path, nrows=3)
    tcol = "ts_event" if "ts_event" in head.columns else "time"
    need = [tcol, "open", "high", "low", "close", "volume"]
    dtypes = {k: "float32" for k in ["open","high","low","close","volume"]}
    df = pd.read_csv(path, usecols=need, dtype=dtypes)
    ts = pd.to_datetime(df.pop(tcol), utc=True).dt.tz_convert(TZ)
    mins = (ts.dt.hour * 60 + ts.dt.minute).to_numpy(np.int16)
    wd = ts.dt.dayofweek.to_numpy()
    ld = ts.dt.strftime("%Y-%m-%d").to_numpy()
    m = (wd < 5) & (mins >= 0) & (mins <= 900)
    df = df.loc[m].reset_index(drop=True); mins = mins[m]; ld = ld[m]
    uniq = np.unique(ld)
    if min_date is not None:
        # keep prior dates only if needed for no cross-day lookback? strategy profile is intraday,
        # so they are unnecessary.
        pass
    D, M = len(uniq), 901
    mp = {d:i for i,d in enumerate(uniq)}
    di = np.fromiter((mp[x] for x in ld), dtype=np.int32, count=len(ld))
    shape=(D,M)
    O=np.full(shape,np.nan,np.float64);H=O.copy();L=O.copy();C=O.copy();V=np.zeros(shape,np.float64);actual=np.zeros(shape,np.uint8)
    O[di,mins]=df.open.to_numpy(); H[di,mins]=df.high.to_numpy(); L[di,mins]=df.low.to_numpy(); C[di,mins]=df.close.to_numpy(); V[di,mins]=df.volume.to_numpy(); actual[di,mins]=1
    valid=np.isfinite(C); idx=np.where(valid,np.arange(M)[None,:],0); idx=np.maximum.accumulate(idx,axis=1); C[:]=np.take_along_axis(C,idx,axis=1)
    valid=np.isfinite(C); ridx=np.where(valid,np.arange(M)[None,:],M-1); ridx=np.minimum.accumulate(ridx[:,::-1],axis=1)[:,::-1]; C[:]=np.take_along_axis(C,ridx,axis=1)
    for arr in (O,H,L):
        miss=~np.isfinite(arr); arr[miss]=C[miss]
    bad=set()
    if condition_path:
        cond=json.load(open(condition_path,"r",encoding="utf-8"))
        bad={x["date"] for x in cond if x.get("condition") != "available"}
    good=np.array([(d not in bad) and np.isfinite(C[i]).all() and actual[i].sum()>300 for i,d in enumerate(uniq)],dtype=np.uint8)
    if min_date is not None:
        good[(uniq < min_date)] = 0
    return dict(open=O,high=H,low=L,close=C,volume=V,actual=actual,dates=uniq,good=good)


@njit(parallel=True, cache=True)
def calc_profiles(H,L,C,O,V,good,bounds,lookback=LOOKBACK,nbins=NBINS):
    D=H.shape[0]; B=len(bounds)
    vah=np.full((D,B),np.nan); val=vah.copy(); poc=vah.copy(); comp=vah.copy(); eff=vah.copy(); inside=vah.copy()
    for d in prange(D):
        if good[d]==0: continue
        for bi in range(B):
            b=bounds[bi]; s=b-lookback
            if s<0: continue
            lo=1e100; hi=-1e100; trsum=0.0; prev=C[d,s]
            for j in range(s,b):
                xlo=L[d,j]; xhi=H[d,j]
                if xlo<lo: lo=xlo
                if xhi>hi: hi=xhi
                tr=xhi-xlo
                if j>s:
                    tr=max(tr,abs(xhi-prev),abs(xlo-prev))
                trsum+=tr; prev=C[d,j]
            span=hi-lo
            if not(span>0): continue
            bw=span/nbins
            diff=np.zeros(nbins+1,np.float64)
            for j in range(s,b):
                i0=int((L[d,j]-lo)/bw); i1=int((H[d,j]-lo)/bw)
                i0=max(0,min(nbins-1,i0)); i1=max(0,min(nbins-1,i1))
                if i1<i0: i0,i1=i1,i0
                cnt=max(1,i1-i0+1); w=V[d,j]/cnt
                diff[i0]+=w
                if i1+1<nbins: diff[i1+1]-=w
            hist=np.empty(nbins,np.float64); acc=0.0; total=0.0; mx=-1.0; pi=0
            for k in range(nbins):
                acc+=diff[k]; hist[k]=acc; total+=acc
                if acc>mx: mx=acc; pi=k
            if total<=0: continue
            vlo=pi; vhi=pi; vacc=hist[pi]; target=VA_PCT*total
            while vacc<target and (vlo>0 or vhi<nbins-1):
                lv=hist[vlo-1] if vlo>0 else -1.0
                rv=hist[vhi+1] if vhi<nbins-1 else -1.0
                if rv>lv: vhi+=1; vacc+=rv
                else: vlo-=1; vacc+=lv
            va_lo=lo+vlo*bw; va_hi=lo+(vhi+1)*bw
            vah[d,bi]=va_hi; val[d,bi]=va_lo; poc[d,bi]=lo+(pi+.5)*bw
            avgtr=trsum/lookback
            comp[d,bi]=span/(avgtr*math.sqrt(lookback)+1e-12)
            eff[d,bi]=abs(C[d,b-1]-O[d,s])/(span+1e-12)
            cin=0
            for j in range(s,b):
                if C[d,j]>=va_lo and C[d,j]<=va_hi: cin+=1
            inside[d,bi]=cin/lookback
    return vah,val,poc,comp,eff,inside


def run_strategy(grid: dict, friction_pts=FRICTION_PTS) -> pd.DataFrame:
    O,H,L,C,V=[grid[k] for k in ["open","high","low","close","volume"]]
    good=grid["good"]; dates=grid["dates"]
    bounds=np.arange(START_MIN, 14*60+30, 5, dtype=np.int32)  # 07:00..14:25
    vah,val,poc,comp,eff,inside=calc_profiles(H,L,C,O,V,good,bounds)
    rows=[]
    for d,date in enumerate(dates):
        if good[d]==0: continue
        next_allowed=0
        for bi,b in enumerate(bounds):
            vh,vl=vah[d,bi],val[d,bi]
            if not np.isfinite(vh): continue
            if not(comp[d,bi] <= 1.0 and eff[d,bi] <= 0.35 and inside[d,bi] >= 0.65): continue
            vw=vh-vl
            for off in range(5):
                t=int(b+off); em=t+1
                if em<next_allowed or em>LAST_ENTRY_MIN or V[d,t]<=0: continue
                prev=C[d,t-1]; s=0; mode=""; stop=np.nan
                if prev<=vh and C[d,t]>vh:
                    s=1; mode="ACC"; stop=vh-0.10*vw
                elif prev>=vl and C[d,t]<vl:
                    s=-1; mode="ACC"; stop=vl+0.10*vw
                elif L[d,t]<=vl and C[d,t]>vl and C[d,t]>O[d,t]:
                    s=1; mode="REJ"; stop=L[d,t]-TICK
                elif H[d,t]>=vh and C[d,t]<vh and C[d,t]<O[d,t]:
                    s=-1; mode="REJ"; stop=H[d,t]+TICK
                if s==0: continue
                sig_risk=(C[d,t]-stop)*s
                if not(np.isfinite(sig_risk) and sig_risk>=MIN_SIGNAL_RISK_PTS): continue
                entry=O[d,em]; risk=(entry-stop)*s
                if not(np.isfinite(risk) and risk>TICK): continue
                end=min(FLAT_MIN, em+MAX_HOLD-1); cur=stop; best=entry; exitpx=np.nan; xm=end; reason="TIME"
                for j in range(em,end+1):
                    stophit=(L[d,j]<=cur) if s==1 else (H[d,j]>=cur)
                    if stophit:
                        exitpx=cur; xm=j; reason="TRAIL/SL"; break
                    if s==1:
                        best=max(best,H[d,j]); cur=max(cur,best-TRAIL_R*risk)
                    else:
                        best=min(best,L[d,j]); cur=min(cur,best+TRAIL_R*risk)
                if not np.isfinite(exitpx): exitpx=C[d,end]
                grossR=(exitpx-entry)*s/risk; netR=grossR-friction_pts/risk
                def ts(minute): return f"{date} {minute//60:02d}:{minute%60:02d} America/Chicago"
                rows.append(dict(date=date,mode=mode,side="LONG" if s==1 else "SHORT",
                                 signal_time=ts(t),entry_time=ts(em),exit_time=ts(xm),
                                 vah=vh,val=vl,poc=poc[d,bi],va_width=vw,
                                 comp=comp[d,bi],eff=eff[d,bi],inside=inside[d,bi],
                                 signal_close=C[d,t],entry=entry,initial_stop=stop,
                                 signal_risk_pts=sig_risk,actual_risk_pts=risk,
                                 exit=exitpx,exit_reason=reason,duration_min=xm-em+1,
                                 gross_R=grossR,friction_pts=friction_pts,net_R=netR))
                next_allowed=xm+COOLDOWN_MIN+1
    return pd.DataFrame(rows)


def metrics(tr: pd.DataFrame, analyzed_days: int | None = None) -> dict:
    if tr.empty: return {}
    x=tr.net_R.to_numpy(float); pos=x[x>0].sum(); neg=-x[x<0].sum(); eq=np.cumsum(x); peaks=np.maximum.accumulate(np.r_[0.,eq]); dd=float(np.max(peaks[1:]-eq))
    nd=int(analyzed_days) if analyzed_days is not None else tr.date.nunique()
    return dict(n=len(x),days=nd,trades_per_day=len(x)/nd,win_rate=float((x>0).mean()),pf=float(pos/neg),expectancy_R=float(x.mean()),net_R=float(x.sum()),maxDD_R=dd)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",required=True)
    ap.add_argument("--condition",default=None)
    ap.add_argument("--min-date",default=None)
    ap.add_argument("--friction-points",type=float,default=FRICTION_PTS)
    ap.add_argument("--out",default="VP_DS180_CANONICAL_v1_trades.csv")
    args=ap.parse_args()
    grid=load_csv_to_daygrid(args.input,args.condition,args.min_date)
    tr=run_strategy(grid,args.friction_points)
    tr.to_csv(args.out,index=False)
    summary=metrics(tr, int(grid["good"].sum()))
    print(json.dumps(summary,indent=2))
    print(f"saved {args.out}")

if __name__=="__main__": main()