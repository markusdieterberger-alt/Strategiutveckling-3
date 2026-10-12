#!/usr/bin/env python3
# AMT BIAS 03: independent neutral-anchor prior-day HVN vs daily VA rejection × Globex IB.
# Research only. NOT Pine-compiled, NOT live, NOT a backtest profit claim.
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd

BIN = 2.0
MIN_RTH = 300
MIN_IB = 45
ANCHOR_MINUTES = {5, 20, 35, 50}
TICK = .25
MODELS = ("HL_EQUAL", "CLOSE_ONLY")
rng = np.random.default_rng(20261012)

def profile(frame: pd.DataFrame, mode: str):
    """Causal 2-point histogram: either spread each bar equally over touched rows or assign all to close."""
    if len(frame) == 0: return None
    lo = np.floor(frame.low.min() / BIN) * BIN
    hi = np.floor(frame.high.max() / BIN) * BIN
    nb = int(round((hi - lo) / BIN)) + 1
    if nb < 5 or nb > 5000: return None
    vol = np.zeros(nb, dtype=float)
    if mode == "CLOSE_ONLY":
        ix = np.floor((frame.close.to_numpy() - lo) / BIN).astype(int)
        vol = np.bincount(np.clip(ix, 0, nb - 1), weights=frame.volume.to_numpy(), minlength=nb).astype(float)
    else:
        lows = np.floor((frame.low.to_numpy() - lo) / BIN).astype(int)
        highs = np.floor((frame.high.to_numpy() - lo) / BIN).astype(int)
        widths = highs - lows + 1
        diff = np.zeros(nb + 1)
        weight = frame.volume.to_numpy() / widths
        np.add.at(diff, lows, weight)
        np.add.at(diff, highs + 1, -weight)
        vol = np.maximum(0, np.cumsum(diff[:-1]))
    smooth = np.convolve(vol, [0.25, 0.5, 0.25], mode="same")
    poc = int(np.argmax(smooth))
    active = smooth[smooth > 1e-9]
    med = float(np.median(active)) if len(active) else 0.
    peaks = []
    for j in range(1, nb-1):
        if smooth[j] >= smooth[j-1] and smooth[j] > smooth[j+1] and smooth[j] >= 1.25*med:
            peaks.append(j)
    # Enforce >=5 rows separation by retaining the larger peak (stable, no outcome sorting).
    peaks = sorted(peaks, key=lambda k: (-smooth[k], k))
    kept = []
    for x in peaks:
        if all(abs(x-y) >= 5 for y in kept): kept.append(x)
    kept.sort()
    # Overall previous-day 70% value area: expand around POC by stronger neighbor.
    target, total = .70 * np.sum(vol), vol[poc]
    a = b = poc
    while total < target and (a > 0 or b < nb - 1):
        lv = smooth[a-1] if a > 0 else -1
        rv = smooth[b+1] if b < nb-1 else -1
        if lv >= rv and a > 0: a -= 1; total += vol[a]
        elif b < nb-1: b += 1; total += vol[b]
        else: break
    return {"lo":float(lo),"volume":vol,"smooth":smooth,"poc":poc,"peaks":kept,
            "poc_price":float(lo+(poc+.5)*BIN),"val":float(lo+a*BIN),
            "vah":float(lo+(b+1)*BIN)}

def hvn_band(prof, current_price):
    if prof is None or not prof["peaks"]: return None
    pk = min(prof["peaks"], key=lambda k:(abs(prof["lo"]+(k+.5)*BIN-current_price),k))
    x = prof["smooth"]
    left=right=pk
    threshold = .60*x[pk]
    while left > 0 and x[left-1] >= threshold: left -= 1
    while right+1 < len(x) and x[right+1] >= threshold: right += 1
    return {"center":prof["lo"]+(pk+.5)*BIN,"lower":prof["lo"]+left*BIN,
            "upper":prof["lo"]+(right+1)*BIN}

def rejection(bars30, edge: float, opposite_edge: float, direction:int, last_close:float):
    """Probe and reclaim are known by anchor. Require >=3 of last 5 closes on recovered side."""
    if len(bars30) < 25: return False
    tail = bars30.iloc[-5:]
    if direction == 1:
        return (float(bars30.low.min()) <= edge-TICK
                and edge+TICK <= last_close <= opposite_edge+BIN/2
                and int((tail.close >= edge+TICK).sum()) >= 3)
    return (float(bars30.high.max()) >= edge+TICK
            and opposite_edge-BIN/2 <= last_close <= edge-TICK
            and int((tail.close <= edge-TICK).sum()) >= 3)


def map_first_touch(df, idx:int, direction:int, global_map):
    """Before outcome, select the NEAREST established directional HVN from frozen 1000 bars."""
    if global_map is None: return ("NO_MAP",np.nan,np.nan)
    if idx+1>=len(df): return ("NO_FUTURE",np.nan,np.nan)
    if (df.ts.iloc[idx+1]-df.ts.iloc[idx]).total_seconds()>61:
        return ("NEXT_OPEN_GAP",np.nan,np.nan)
    entry=float(df.open.iloc[idx+1])
    signal_close=float(df.close.iloc[idx])
    centers=global_map["peaks"]
    candidates=[]
    for pk in centers:
        center=global_map["lo"]+(pk+.5)*BIN
        if direction*(center-signal_close)<=0: continue
        band=hvn_band_at_peak(global_map,pk)
        target = band["lower"] if direction>0 else band["upper"]
        if direction*(target-signal_close) >= BIN:
            candidates.append((abs(center-signal_close),pk,target))
    if not candidates:return ("NO_HVN_B",np.nan,np.nan)
    candidates.sort(key=lambda v:(v[0],v[1]))
    target=float(candidates[0][2])
    if direction*(target-entry) < BIN:
        return ("TARGET_GAPPED_BEFORE_ENTRY",target,np.nan)
    mirror=2*entry-target
    last_t=df.ts.iloc[idx]+pd.Timedelta(minutes=120)
    end=int(df.ts.searchsorted(last_t,side="right"))
    seq=df.iloc[idx+1:end]
    if seq.empty:return ("NO_FUTURE",target,float(mirror))
    if seq.symbol.nunique()!=1 or seq.ts.diff().dt.total_seconds().dropna().max()>121:
        return ("OUTCOME_GAP",target,float(mirror))
    for bar in seq.itertuples(index=False):
        target_hit=(bar.high>=target if direction==1 else bar.low<=target)
        mirror_hit=(bar.low<=mirror if direction==1 else bar.high>=mirror)
        if target_hit and mirror_hit:return ("AMBIGUOUS",target,float(mirror))
        if target_hit:return ("TARGET_FIRST",target,float(mirror))
        if mirror_hit:return ("MIRROR_FIRST",target,float(mirror))
    return ("NEITHER",target,float(mirror))

def hvn_band_at_peak(prof, pk):
    x=prof["smooth"];left=right=pk;th=.60*x[pk]
    while left>0 and x[left-1]>=th:left-=1
    while right+1<len(x) and x[right+1]>=th:right+=1
    return {"lower":prof["lo"]+left*BIN,"upper":prof["lo"]+(right+1)*BIN}

def classify_value(prof, current_price):
    if prof is None: return "NO_LOCAL_PROFILE"
    return ("BELOW" if current_price < prof["val"] else
            "ABOVE" if current_price > prof["vah"] else "WITHIN")

def get_prev_series(frame, length, asof_index, min_fraction=.95, max_gap_seconds=120):
    segment = frame.iloc[asof_index-length+1:asof_index+1]
    if len(segment)!=length: return None
    delta = segment.ts.diff().dt.total_seconds().dropna()
    if float((delta<=61).mean()) < min_fraction or float(delta.max()) > max_gap_seconds: return None
    if segment.symbol.nunique()!=1: return None
    return segment

def load(csv_path):
    df = pd.read_csv(csv_path,compression="infer",low_memory=False)
    time_col = "ts_event" if "ts_event" in df.columns else "time"
    needed={"open","high","low","close","volume"}
    if not needed.issubset(df.columns): raise ValueError("Missing OHLCV columns: "+repr(df.columns.tolist()))
    df["ts"] = pd.to_datetime(df[time_col],utc=True,errors="coerce")
    df=df.dropna(subset=["ts","open","high","low","close","volume"]).sort_values("ts")
    df=df.drop_duplicates("ts",keep="first").reset_index(drop=True)
    if "symbol" not in df.columns: df["symbol"]="MNQ1!"
    df["ny"]=df.ts.dt.tz_convert("America/New_York")
    df["eu"]=df.ts.dt.tz_convert("Europe/Stockholm")
    df["nyday"]=df.ny.dt.strftime("%Y-%m-%d")
    df["nyhm"]=df.ny.dt.hour*60+df.ny.dt.minute
    df["euhm"]=df.eu.dt.hour*60+df.eu.dt.minute
    return df

def complete_rth_profiles(df):
    cash=df[(df.nyhm>=570)&(df.nyhm<=959)]
    days={}
    for key,part in cash.groupby("nyday",sort=True):
        if len(part)<MIN_RTH or part.symbol.nunique()!=1: continue
        if part.ts.diff().dt.total_seconds().dropna().max()>360: continue
        # The profile becomes available only after 16:00 NY on this date.
        ends=pd.Timestamp(key+" 16:00:00",tz="America/New_York").tz_convert("UTC")
        days[key]={"ready":ends,"HL_EQUAL":profile(part,"HL_EQUAL"),"CLOSE_ONLY":profile(part,"CLOSE_ONLY"),
                   "range":float(part.high.max()-part.low.min()),"n":len(part)}
    return sorted(days.values(),key=lambda d:d["ready"])

def completed_globex_ib(df):
    # IB starts 18:00 NY and ends 18:59 NY; no future bars, current fully completed day.
    hour=df[(df.nyhm>=1080)&(df.nyhm<1140)]
    ibis=[]
    for key,part in hour.groupby("nyday",sort=True):
        if len(part)<MIN_IB or part.symbol.nunique()!=1: continue
        done=pd.Timestamp(key+" 19:00:00",tz="America/New_York").tz_convert("UTC")
        ibis.append({"ready":done,"lo":float(part.low.min()),"hi":float(part.high.max()),"n":len(part)})
    return sorted(ibis,key=lambda v:v["ready"])

def anchors(df):
    ny=df.nyhm; eu=df.euhm
    valid_ny=((ny>=575)&(ny<=710)&(df.ny.dt.minute.isin(ANCHOR_MINUTES)))
    valid_eu=((eu>=425)&(eu<=710)&(df.eu.dt.minute.isin(ANCHOR_MINUTES)))
    # NY 09:35, 09:50, 10:05,..11:50; EU 07:05, 07:20,...11:50
    # Exclude weekends in the respective sessions.
    valid_ny &= df.ny.dt.dayofweek<5
    valid_eu &= df.eu.dt.dayofweek<5
    return [(int(i),"NY" if valid_ny.iloc[i] else "EU") for i in np.flatnonzero((valid_ny|valid_eu).to_numpy())
            for _ in (0,) if valid_ny.iloc[i] or valid_eu.iloc[i]]

def outcomes(df, idx, side, period):
    base=idx+1
    if base>=len(df): return (np.nan,False)
    # Strictly next actual minute open; discontinuity invalidates outcome.
    t=df.ts.iloc[idx]
    if (df.ts.iloc[base]-t).total_seconds()>61: return (np.nan,False)
    future_t=t+pd.Timedelta(minutes=period)
    k=int(df.ts.searchsorted(future_t,side="left"))
    if k>=len(df): return (np.nan,False)
    if (df.ts.iloc[k]-future_t).total_seconds()>61: return (np.nan,False)
    seq=df.iloc[base:k+1]
    if seq.symbol.nunique()!=1 or seq.ts.diff().dt.total_seconds().dropna().max()>121:
        return (np.nan,False)
    return (float(side*(df.close.iloc[k]-df.open.iloc[base])),True)

def run(args):
    df=load(args.data)
    profiles=complete_rth_profiles(df)
    ibs=completed_globex_ib(df)
    prof_ready=np.array([p["ready"].value for p in profiles],dtype=np.int64)
    ib_ready=np.array([p["ready"].value for p in ibs],dtype=np.int64)
    rows=[]; seen=set(); qa={"bars":len(df),"profile_days":len(profiles),"ib_sessions":len(ibs),
                            "neutral_anchors":0,"missing_prior_day":0,"missing_ib":0,
                            "missing_local150":0,"reject_events":0}
    for i,session in anchors(df):
        qa["neutral_anchors"]+=1
        now=df.ts.iloc[i]
        if i<1000:continue
        k=int(np.searchsorted(prof_ready,now.value,side="right"))-1
        j=int(np.searchsorted(ib_ready,now.value,side="right"))-1
        if k<0: qa["missing_prior_day"]+=1;continue
        if j<0: qa["missing_ib"]+=1;continue
        # Previous cash RTH must be from a *previous NY date*, not current session.
        day=profiles[k]
        if str(day["ready"].tz_convert("America/New_York").date())==df.nyday.iloc[i]:
            qa["missing_prior_day"]+=1;continue
        # Reject IB older than 24 hours except first weekday post-weekend.
        if (now-ibs[j]["ready"]).total_seconds()>3*86400: qa["missing_ib"]+=1;continue
        last30=get_prev_series(df,30,i,1.0)
        if last30 is None: continue
        last150=get_prev_series(df,150,i,0.99)
        if last150 is None: qa["missing_local150"]+=1;continue
        price=float(df.close.iloc[i]); ib=ibs[j]
        ib_side=1 if price>ib["hi"] else -1 if price<ib["lo"] else 0
        # Local context *classification*, not an inclusion filter.
        local={m:classify_value(profile(last150,m),price) for m in MODELS}
        map150_context = {}
        map1000_source=get_prev_series(df,1000,i,min_fraction=.998,max_gap_seconds=5400)
        # One <=90m maintenance gap permitted in global 1000bar map; not weekends or rolls.
        map1000={m:profile(map1000_source,m) if map1000_source is not None else None for m in MODELS}
        for m in MODELS:
            d=day[m]
            if d is None: continue
            hvn=hvn_band(d,price)
            candidates=[("DAILY_VA_EDGE",d["val"],d["vah"])]
            if hvn:candidates.append(("DAILY_HVN_BAND",hvn["lower"],hvn["upper"]))
            for kind,lower,upper in candidates:
                for side,edge in [(1,lower),(-1,upper)]:
                    if not rejection(last30,edge,upper if side==1 else lower,side,price):continue
                    # One event per symbol/session/day/model/kind/side/edge.
                    uniq=(df.nyday.iloc[i],session,m,kind,side,round(edge,2))
                    if uniq in seen:continue
                    seen.add(uniq)
                    r30,valid30=outcomes(df,i,side,30)
                    r60,valid60=outcomes(df,i,side,60)
                    if not valid30:continue
                    map_result,map_target,map_mirror=map_first_touch(df,i,side,map1000[m])
                    # 120-minute momentum is a diagnostic, NOT the entry selection.
                    m120=float(side*(df.close.iloc[i]-df.close.iloc[i-120]))
                    row={"ts":str(now),"nyday":df.nyday.iloc[i],"session":session,"year":int(df.ny.iloc[i].year),
                         "model":m,"rejection":kind,"side":side,"edge":edge,"price":price,
                         "ib_side":ib_side,"ib_aligned":bool(ib_side==side),
                         "ib_opposite":bool(ib_side==-side),"ib_inside":bool(ib_side==0),
                         "local_value_state":local[m],"momentum_120_signed":m120,
                         "next30_signed":r30,"next60_signed":r60 if valid60 else np.nan,
                         "prior_day_rth_range":day["range"],"source_contract":df.symbol.iloc[i],
                         "map_result":map_result,"map_target":map_target,"map_mirror":map_mirror,
                         "map_distance":abs(map_target-price) if np.isfinite(map_target) else np.nan}
                    rows.append(row)
                    qa["reject_events"]+=1
    return pd.DataFrame(rows),qa

def summary(events):
    if events.empty:return pd.DataFrame()
    x=events.copy()
    x["period"]=np.where(x.year<=2022,"2019_22",np.where(x.year<=2024,"2023_24","2025_26"))
    g=["model","session","rejection","local_value_state","period","ib_aligned"]
    return x.groupby(g,dropna=False,observed=True).agg(n=("next30_signed","size"),
        mean30=("next30_signed","mean"),mean60=("next60_signed","mean"),
        mean_momentum=("momentum_120_signed","mean"),
        winning30_pct=("next30_signed",lambda a:100*(a>0).mean()),
        eligible_map=("map_result",lambda a:int(a.isin(["TARGET_FIRST","MIRROR_FIRST","AMBIGUOUS","NEITHER"]).sum())),
        map_target_first=("map_result",lambda a:int((a=="TARGET_FIRST").sum())),
        map_mirror_first=("map_result",lambda a:int((a=="MIRROR_FIRST").sum()))).reset_index()

def day_bootstrap(events,reps=1000):
    # Day-level bootstrap from 2x2 sufficient statistics, rather than
    # concatenating thousands of Pandas DataFrames on every resample.
    out=[]
    for (model,session,rejection),part in events.groupby(["model","session","rejection"]):
        aligned=part.loc[part.ib_aligned,"next30_signed"]
        other=part.loc[~part.ib_aligned,"next30_signed"]
        if len(aligned)<15 or len(other)<15:continue
        daily=part.groupby(["nyday","ib_aligned"]).next30_signed.agg(["size","sum"]).unstack(fill_value=0)
        daylist=sorted(part.nyday.unique())
        if len(daylist)<15:continue
        daymap=part.assign(a_n=part.ib_aligned.astype(int),
                          a_sum=part.next30_signed*part.ib_aligned.astype(int),
                          b_n=(~part.ib_aligned).astype(int),
                          b_sum=part.next30_signed*(~part.ib_aligned).astype(int)
                        ).groupby("nyday")[["a_n","a_sum","b_n","b_sum"]].sum()
        values=daymap.to_numpy(dtype=float)
        indexes=rng.integers(0,len(values),size=(reps,len(values)))
        roll=values[indexes].sum(axis=1)
        valid=(roll[:,0]>0)&(roll[:,2]>0)
        dif=roll[valid,1]/roll[valid,0]-roll[valid,3]/roll[valid,2]
        lo,hi=np.quantile(dif,[.025,.975]) if len(dif) else (np.nan,np.nan)
        out.append(dict(model=model,session=session,rejection=rejection,
                        n=int(len(part)),ib_aligned_n=len(aligned),not_aligned_n=len(other),
                        delta_mean30=float(aligned.mean()-other.mean()),
                        ci95_low=float(lo),ci95_high=float(hi),
                        independent_days=len(values)))
    return pd.DataFrame(out)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data",required=True,help="Owned MNQ canonical CSV or CSV.GZ")
    p.add_argument("--output",default="amt_bias03_output")
    a=p.parse_args()
    d=Path(a.output);d.mkdir(parents=True,exist_ok=True)
    es,qa=run(a)
    es.to_csv(d/"D02032_AMT_BIAS03_EVENTS.csv",index=False)
    summary(es).to_csv(d/"D02033_AMT_BIAS03_PERIODS.csv",index=False)
    day_bootstrap(es).to_csv(d/"D02034_AMT_BIAS03_DAY_BOOTSTRAP.csv",index=False)
    qa["input_sha256"]=hashlib.sha256(Path(a.data).read_bytes()).hexdigest()
    qa["status"]="NOT_TV_PINE_VERIFIED_NOT_BLIND_OOS"
    (d/"D02035_AMT_BIAS03_QA.json").write_text(json.dumps(qa,indent=2),encoding="utf-8")
    print(json.dumps(qa,indent=2))
if __name__=="__main__":main()
