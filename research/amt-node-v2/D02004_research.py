#!/usr/bin/env python3
"""AMT Node Proxy V2 DEV. Deterministic research, NOT a Pine compiler.

Run: python D02004_research.py --data /path/MNQ_CANONICAL_1M_V1_0.csv.gz --out results
All output periods are DEV. Raw market data is never copied into the repository.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

EXPECTED_GZ = '468be1268212be3dc74149cfd5facb5b7c1c1623d7d304937922a1eff857f1ba'
EXPECTED_CSV = '45cb26293d64d77b10062a3603c38b5eb66743d22dea7611a9672478f54e1ccd'
TICK = .25
# UTC condition dates, preserved. Original condition.json + A002 extension section 20.
DEGRADED = {'2020-02-27','2020-02-28','2020-05-05','2020-06-30','2020-07-01',
            '2021-12-05','2022-01-02','2024-09-18','2025-09-17','2025-09-24',
            '2025-11-28','2026-01-31','2026-03-15','2026-03-16','2026-03-21',
            '2026-04-10','2026-05-24','2026-08-29'}

def sha(path, compressed=False):
    h = hashlib.sha256()
    with (gzip.open(path, 'rb') if compressed else open(path, 'rb')) as f:
        for b in iter(lambda: f.read(2**20), b''):
            h.update(b)
    return h.hexdigest()

def load_data(path, strict=True):
    hashes = dict(gzip_sha256=sha(path), csv_sha256=sha(path, True))
    if strict:
        assert hashes == dict(gzip_sha256=EXPECTED_GZ, csv_sha256=EXPECTED_CSV), hashes
    frame = pd.read_csv(path)
    ts = pd.DatetimeIndex(pd.to_datetime(frame.ts_event, utc=True))
    assert ts.is_monotonic_increasing and not ts.has_duplicates
    x = frame[['open', 'high', 'low', 'close', 'volume']].to_numpy(float)
    assert np.isfinite(x).all() and (x[:, 4] >= 0).all()
    assert np.max(np.abs(x[:, :4] * 4 - np.round(x[:, :4] * 4))) < 1e-7
    assert ((x[:, 1] >= x[:, [0, 2, 3]].max(1)) & (x[:, 2] <= x[:, [0, 1, 3]].min(1))).all()
    minute = ts.asi8 // 60_000_000_000
    symbol = frame.symbol.to_numpy()
    gap = np.r_[True, (np.diff(minute) != 1) | (symbol[1:] != symbol[:-1])]
    blockstart = np.maximum.accumulate(np.where(gap, np.arange(len(x)), 0))
    blockend = np.minimum.accumulate(np.where(np.r_[gap[1:], True], np.arange(len(x)), len(x))[::-1])[::-1]
    cont = np.arange(len(x)) - blockstart + 1
    ends = np.flatnonzero(((minute + 1) % 5 == 0) & (cont >= 5))
    close_ts = ts + pd.Timedelta(minutes=1)
    local = {}
    for label, zone in [('NY', 'America/New_York'), ('EU', 'Europe/Stockholm')]:
        z = close_ts.tz_convert(zone)
        local[label] = (z.hour * 60 + z.minute).to_numpy()
    cohort = np.full(len(x), 'OFF', dtype='<U3')
    cohort[(local['EU'] >= 420) & (local['EU'] < 720)] = 'EU'
    cohort[(local['NY'] >= 570) & (local['NY'] < 720)] = 'NY'
    atr = np.full(len(x), np.nan)
    seed, previous, value, oldblock = [], None, np.nan, -1
    for i in ends:
        if blockstart[i] != oldblock:
            seed, previous, value, oldblock = [], None, np.nan, blockstart[i]
        hh, ll = x[i-4:i+1, 1].max(), x[i-4:i+1, 2].min()
        tr = hh-ll if previous is None else max(hh-ll, abs(hh-previous), abs(ll-previous))
        previous = x[i, 3]
        if len(seed) < 14:
            seed.append(tr)
            if len(seed) == 14:
                value = float(np.mean(seed))
        else:
            value = (value * 13 + tr) / 14
        atr[i] = value
    ib = {}
    # Store only complete 60-observation IBs; searchsorted(asof) excludes future IBs.
    for label, zone, hour in [('NY', 'America/New_York', 18), ('EU', 'Europe/Stockholm', 0)]:
        z = ts.tz_convert(zone)
        eligible = np.flatnonzero(z.hour == hour)
        ibs = []
        for _, group in pd.Series(eligible, index=z[eligible].date).groupby(level=0, sort=True):
            ids = group.to_numpy()
            if len(ids) == 60 and minute[ids[-1]] - minute[ids[0]] == 59 and len(set(symbol[ids])) == 1:
                ibs.append((minute[ids[-1]] + 1, x[ids, 1].max(), x[ids, 2].min()))
        ib[label] = np.array(ibs, float)
    days = frame.trade_date.to_numpy()
    daystats = frame.groupby('trade_date').agg(high=('high','max'),low=('low','min'),bars=('open','size'))
    # Only full nominal 23-hour sessions count here; holiday/degraded days not silently filled.
    prior_ranges = (daystats.high-daystats.low).where(daystats.bars == 1380).shift(1).to_dict()
    degraded_prefix = np.r_[0, np.cumsum(pd.Series(ts.date).astype(str).isin(DEGRADED).to_numpy())]
    data = dict(x=x, ts=ts, minute=minute, gap=gap, start=blockstart, end=blockend,
                cont=cont, ends=ends, cohort=cohort, local=local, atr=atr, ib=ib,
                days=days, symbol=symbol, prior_ranges=prior_ranges,degraded_prefix=degraded_prefix)
    report = dict(**hashes, rows=len(x), first=str(ts[0]), last=str(ts[-1]),
                  trading_days=int(len(daystats)), rolls=int(np.count_nonzero(symbol[1:] != symbol[:-1])),
                  gap_transitions=int(gap.sum()-1), continuous_150m_5m_closes=int(np.count_nonzero(cont[ends]>=150)),
                  duplicates=0, invalid_ohlc=0, off_tick_grid=0, missing_values=0,
                  ib_complete={k:len(v) for k,v in ib.items()},
                  all_periods='EXPOSED_DEV', python=sys.version.split()[0],pandas=pd.__version__,numpy=np.__version__,
                  degraded_utc_dates=sorted(DEGRADED))
    return data, report

def profile(x, mode='HL'):
    """x is exactly 150 rows, chronological. Returns frozen geometry and audit arrays."""
    lo, hi = x[:, 2].min(), x[:, 1].max()
    width = max(4, math.floor((hi-lo)*4/64+.5)) / 4
    anchor = math.floor(lo/width)*width
    n = math.floor((hi-anchor)/width)+1
    a = np.floor(((x[:, 3] if mode == 'CLOSE' else x[:, 2])-anchor)/width).astype(int)
    b = np.floor(((x[:, 3] if mode == 'CLOSE' else x[:, 1])-anchor)/width).astype(int)
    w = np.ones(len(x)) if mode == 'TPO' else x[:, 4]/(b-a+1)
    delta = np.zeros(n+1)
    np.add.at(delta, np.column_stack((a,b+1)).ravel(), np.column_stack((w,-w)).ravel())
    raw = np.cumsum(delta[:-1])
    raw[raw <= np.sum(w*(b-a+1))*1e-12] = 0
    smooth = np.convolve(np.r_[0.,raw,0.], [.25,.5,.25], mode='valid')
    # Fixed numerical resolution, not a trading parameter: make exact plateaus
    # deterministic across evaluation orders in NumPy and Pine floating arithmetic.
    smooth = np.floor(smooth*1_000_000+.5)/1_000_000
    median = float(np.median(smooth[smooth > 0])) if np.any(smooth > 0) else np.nan
    peaks = np.flatnonzero((smooth[1:-1] > smooth[:-2]) & (smooth[1:-1] > smooth[2:]) & (smooth[1:-1] >= 1.25*median))+1
    pairs, best = [], None
    for a,b in zip(peaks[:-1], peaks[1:]):
        if b-a < 5:
            continue
        v = a+1+int(np.argmin(smooth[a+1:b]))
        if smooth[v] > .60*min(smooth[a], smooth[b]):
            continue
        low, mid, high = anchor+(a+.5)*width, anchor+(v+.5)*width, anchor+(b+.5)*width
        pairs.append((low,mid,high))
        for origin,target,side in [(low,high,1),(high,low,-1)]:
            distance = abs(x[-1,3]-mid)
            if abs(x[-1,3]-origin) <= width*.5 and (best is None or distance < best['distance']):
                best = dict(origin=origin, valley=mid, destination=target, direction=side, distance=distance)
    return dict(best=best, width=width, poc=anchor+(int(np.argmax(smooth))+.5)*width,
                pairs=pairs, raw=raw, smooth=smooth, anchor=anchor)

def step_episode(ep, close, high, low, now):
    """Shared transition logic, returns (family, side) or None. Updates ep causally."""
    d = ep['direction']
    if ep['kind'] == 'BALANCE' and d == 0:
        d = 1 if close > ep['upper'] else -1 if close < ep['lower'] else 0
        ep['direction'] = d
        if d:
            ep['valley'] = ep['upper'] if d == 1 else ep['lower']
    if not d:
        return None
    half = ep['width']*.5 if ep['kind'] != 'BALANCE' else 0
    beyond = d*(close-ep['valley']) > half
    returned = d*(close-ep['valley']) < -half
    if ep.get('probe') is None:
        if beyond:
            ep.update(probe=now, count=1, probe_high=high, probe_low=low)
        return None
    ep['probe_high'] = max(ep['probe_high'], high)
    ep['probe_low'] = min(ep['probe_low'], low)
    ep['count'] = ep['count']+1 if beyond else 0
    result = None
    if ep['count'] >= 3:
        result = ('A', d)
    elif returned and now-ep['probe'] <= 15:
        result = ('B', -d)
    if result or now-ep['probe'] >= 15:
        ep['consumed'] = True
    return result

def make_event(data, ep, i, result, mode):
    family, side = result
    if ep['kind'] == 'BALANCE':
        target = ep['valley']+side*ep['width'] if family == 'A' else ep['poc']
        ordertarget = target
        stop = ep['valley']-side*.25 if family == 'A' else (ep['probe_low']-.25 if side==1 else ep['probe_high']+.25)
    else:
        target = ep['destination'] if family == 'A' else ep['poc']
        ordertarget = target-side*ep['width']*.5 if family == 'A' else target
        stop = ep['valley']-side*(ep['width']*.5+.25) if family == 'A' else (ep['probe_low']-.25 if side==1 else ep['probe_high']+.25)
    rounding = math.floor if side == 1 else math.ceil
    stop, ordertarget = rounding(stop*4)/4, rounding(ordertarget*4)/4
    signal = data['minute'][i]+1
    e = dict(model=ep['kind'], construction=mode, family=family, side=side, i=int(i),
             signal_time=str(data['ts'][i]+pd.Timedelta(minutes=1)), trade_date=data['days'][i],
             year=int(data['ts'][i].year), cohort=data['cohort'][i],
             minute_local=int(data['local'][data['cohort'][i]][i]) if data['cohort'][i]!='OFF' else -1,
             frozen_minute=int(ep['frozen']), profile_age=int(signal-ep['frozen']),
             source_last_i=int(ep['source_i']), origin=ep.get('origin', np.nan), valley=ep['valley'],
             destination=ep.get('destination',np.nan), poc=ep['poc'], bin_width=ep['width'],
             target=target, stop=stop, order_target=ordertarget, close=data['x'][i,3],
             atr=data['atr'][i], control_eligible=not ep['has_pairs'])
    e['planned_risk'] = side*(e['close']+side*.25-stop)
    e['geometry_valid'] = side*(e['close']-stop)>0 and side*(ordertarget-e['close'])>0
    pref=data['degraded_prefix']
    e['degraded_source'] = bool(pref[i+1]-pref[ep['source_i']-149])
    for label, table in data['ib'].items():
        k = np.searchsorted(table[:,0],signal,side='right')-1 if len(table) else -1
        known = k>=0 and signal-table[k,0] < 24*60
        if known:
            _,hi,lo = table[k]
            state = 1 if e['close']>hi else -1 if e['close']<lo else 0
            e.update({f'ib_{label}_state':state,f'ib_{label}_alignment':state*side,
                      f'ib_{label}_high_atr':(hi-e['close'])/e['atr'],
                      f'ib_{label}_low_atr':(lo-e['close'])/e['atr'],
                      f'ib_{label}_width_prev_range':(hi-lo)/data['prior_ranges'].get(e['trade_date'],np.nan)})
        else:
            for key in ['state','alignment','high_atr','low_atr','width_prev_range']:
                e[f'ib_{label}_{key}'] = np.nan
    return e

def generate(data, mode='HL', kind='NODE'):
    x, minutes, starts = data['x'], data['minute'], data['start']
    out, audits, stats = [], [], Counter()
    ep, nextfreeze, oldblock = None, 0, -1
    for i in data['ends']:
        if data['cont'][i]<150:
            continue
        now = int(minutes[i]+1)
        if starts[i] != oldblock:
            ep, nextfreeze, oldblock = None, 0, starts[i]
        if ep is not None and now>=nextfreeze:
            ep = None
        emitted = False
        if ep is not None:
            result = step_episode(ep,x[i,3],x[i-4:i+1,1].max(),x[i-4:i+1,2].min(),now)
            if result:
                out.append(make_event(data,ep,i,result,mode))
                emitted = True
                stats['signals_'+data['cohort'][i]] += 1
            if ep.get('consumed'):
                ep = None
        if ep is None and not emitted and now>=nextfreeze:
            p = profile(x[i-149:i+1],mode)
            stats['profile_evaluations'] += 1
            if kind == 'BALANCE':
                lo,hi = x[i-29:i+1,2].min(),x[i-29:i+1,1].max()
                if hi<=lo:
                    continue
                ep = dict(kind=kind,direction=0,lower=lo,upper=hi,valley=np.nan,poc=(hi+lo)/2,width=hi-lo)
            elif p['best'] is not None:
                ep = dict(**p['best'],kind=kind,poc=p['poc'],width=p['width'])
                if kind == 'PSEUDO':
                    for key in ['origin','valley','destination','poc']:
                        ep[key] += ep['direction']*ep['width']
            if ep is not None:
                ep.update(frozen=now,source_i=int(i),has_pairs=bool(p['pairs']))
                nextfreeze = now+150
                stats['frozen_profiles'] += 1
                audits.append(dict(model=kind,construction=mode,source_last_i=int(i),
                                   frozen_minute=now,bin_width=p['width'],poc=p['poc'],
                                   pairs=len(p['pairs']),raw_mass=float(sum(p['raw']))))
    return out,audits,dict(stats)

def first_touch(x, side, entry, distance, limit):
    """One outcome per minute. Open ordering wins; unknown double touch is adverse."""
    tie = False
    for k, (o,h,l,c,v) in enumerate(x[:limit]):
        favorable_open = side*(o-entry)>=distance
        adverse_open = side*(o-entry)<=-distance
        if favorable_open or adverse_open:
            return (1 if favorable_open else -1), k+1, tie
        favorable = (h-entry if side==1 else entry-l)>=distance
        adverse = (entry-l if side==1 else h-entry)>=distance
        if favorable or adverse:
            tie = favorable and adverse
            return (-1 if adverse else 1), k+1, tie
    return 0, len(x[:limit]), tie

def outcomes(data, event, distance=None):
    i,side = int(event['i']),int(event['side'])
    if i+1>=len(data['x']) or data['gap'][i+1]:
        return dict(outcome_valid=False,outcome_reason='gap_or_end_before_entry')
    entry = data['x'][i+1,0]
    distance = side*(event['target']-entry) if distance is None else distance
    if distance<=0:
        return dict(outcome_valid=False,outcome_reason='target_not_ahead_at_open',distance=distance)
    rows = data['x'][i+1:min(i+121,data['end'][i]+1)]
    result = dict(outcome_valid=True,outcome_reason='ok',distance=distance,phenomenon_entry=entry,
                  distance_atr=distance/event['atr'])
    for horizon in (30,60,120):
        hit,duration,tie = first_touch(rows,side,entry,distance,horizon)
        avail = rows[:horizon]
        mfe = (avail[:,1]-entry).max() if side==1 else (entry-avail[:,2]).max()
        mae = (entry-avail[:,2]).max() if side==1 else (avail[:,1]-entry).max()
        result.update({f'hit_{horizon}':hit,f'duration_{horizon}':duration,
                       f'tie_{horizon}':tie,f'censored_{horizon}':len(avail)<horizon and hit==0,
                       f'mfe_{horizon}':mfe,f'mae_{horizon}':mae})
    for h in (5,15,30):
        result[f'return_{h}'] = side*(rows[h-1,3]-entry) if len(rows)>=h else np.nan
    return result

def fill_bar(o,h,l,side,stop,target):
    """Raw exit level before our adverse exit tick. Returns reason, level, ambiguous."""
    if side*(o-stop)<=0:
        return 'STOP_GAP',o,False
    if side*(o-target)>=0:
        return 'TP_GAP_CAPPED',target,False
    sh = l<=stop if side==1 else h>=stop
    th = h>=target if side==1 else l<=target
    if sh:
        return 'STOP',stop,bool(th)
    if th:
        return 'TP',target,False
    return None

def simulate_trade(data,e):
    x,minutes = data['x'],data['minute']
    i,side = int(e['i']),int(e['side'])
    if i+1>=len(x):
        return None
    first=i+1
    entry=x[first,0]+side*.25
    stop,target=e['stop'],e['order_target']
    planned=e['planned_risk']
    marked=[]
    gap_flag=bool(data['gap'][first])
    reason,rawexit,ambiguous,j='END_DATA',x[-1,3],False,len(x)-1
    for k in range(first,len(x)):
        o,h,l,c,v=x[k]
        result=fill_bar(o,h,l,side,stop,target)
        gap_now=bool(data['gap'][k])
        # The order was already committed. Do not silently discard gap-entry trades.
        open_cross = side*(o-stop)<=0 or side*(o-target)>=0
        if gap_now:
            gap_flag=True
            if not open_cross:
                result=('DATA_GAP',o,False)
        # A previous confirmed close requested a time/cutoff exit at this open.
        due = k>first and (minutes[k]>=minutes[first]+120 or data['local'][e['cohort']][k-1]>=720)
        if due and not open_cross and not gap_now:
            result=('CUTOFF' if data['local'][e['cohort']][k-1]>=720 else 'TIME',o,False)
        if result:
            reason,rawexit,ambiguous=result
            j=k
            # Before an intrabar fill, conservatively credit an adverse extreme up to stop;
            # no favorable high watermark is inferred inside the exit minute.
            adverse=min(o,stop) if side==1 else max(o,stop)
            if reason in ('TP','TP_GAP_CAPPED','TIME','CUTOFF','DATA_GAP'):
                adverse=o
            marked.append(side*(adverse-entry)-.5)
            break
        marked.append(side*((l if side==1 else h)-entry)-.5)
        marked.append(side*(c-entry)-.5)
    exit_price=rawexit-side*.25
    gross=side*(rawexit-x[first,0])
    net=side*(exit_price-entry)-.5
    assert abs(net-(gross-1))<1e-7
    return dict(**e,entry_i=first,exit_i=int(j),entry_time=str(data['ts'][first]),exit_time=str(data['ts'][j]),
                entry_price=entry,exit_price=exit_price,exit_reason=reason,ambiguous=ambiguous,
                gap_flag=gap_flag,actual_entry_risk=side*(entry-stop),
                target_crossed_at_entry=bool(side*(x[first,0]-target)>=0),
                gross_points=gross,net_points=net,net_usd=net*2,R=net/planned,
                duration_minutes=int(minutes[j]-minutes[first]),
                worst_open_equity_points=float(min(marked+[net])),
                _marks=marked)

def trade_engine(data, events):
    trades, gate=[] ,Counter()
    free={}
    for e in events:
        if e['cohort']=='OFF' or e['model']!='NODE':
            continue
        key=(e['construction'],e['family'],e['cohort'])
        if not e['geometry_valid']:
            gate[str(key)+' invalid_geometry']+=1
            continue
        if e['i'] < free.get(key,-1):
            gate[str(key)+' position_busy']+=1
            continue
        tr=simulate_trade(data,e)
        if tr is not None:
            free[key]=tr['exit_i']
            gate[str(key)+' submitted']+=1
            tr.pop('_marks',None)
            pref=data['degraded_prefix']
            tr['degraded_source_or_trade']=bool(pref[tr['exit_i']+1]-pref[tr['source_last_i']-149])
            trades.append(tr)
    return pd.DataFrame(trades),dict(gate)

def bootstrap_day(df,value,reps=1000):
    q=df.groupby('trade_date')[value].agg(['sum','count']).to_numpy(float)
    if len(q)<2:
        return [None,None]
    rng=np.random.default_rng(20261012)
    # Resample trading-day clusters, ratio of sums/counts (not mean of daily means).
    sample=rng.integers(0,len(q),(reps,len(q)))
    values=q[sample].sum(1)
    estimates=values[:,0]/values[:,1]
    return np.quantile(estimates,[.025,.975]).tolist()

def periods(df):
    yield 'ALL',df
    for label,a,b in [('2019-2022',2019,2022),('2023-2024',2023,2024),('2025-2026',2025,2026),('2026',2026,2026)]:
        yield label,df[df.year.between(a,b)]
    for y in range(2019,2027):
        if y != 2026:
            yield str(y),df[df.year==y]

def summaries(data,events,trades):
    phen,perf=[],[]
    unique_days=np.unique(data['days'])
    valid=events[(events.cohort!='OFF') & (events.outcome_valid==True)]
    keys=['model','construction','family','cohort','side']
    for key,base in valid.groupby(keys):
        for period,g in periods(base):
            if g.empty:
                continue
            base_period=g
            for horizon in (30,60,120):
                score=f'hit_{horizon}'
                g=base_period[base_period[f'censored_{horizon}'].eq(False)]
                if g.empty:
                    continue
                row=dict(zip(keys,key),period=period,horizon=horizon,n=len(g),
                         target_first=float((g[score]==1).mean()),mirror_first=float((g[score]==-1).mean()),
                         neither=float((g[score]==0).mean()),asymmetry=float(g[score].mean()),
                         ties=int(g[f'tie_{horizon}'].sum()),distance_median=float(g.distance.median()),
                         duration_median=float(g[f'duration_{horizon}'].median()),
                         mfe_median=float(g[f'mfe_{horizon}'].median()),mae_median=float(g[f'mae_{horizon}'].median()),
                         return15_mean=float(g.return_15.mean()),return30_mean=float(g.return_30.mean()))
                if period in ('ALL','2019-2022','2023-2024','2025-2026') and horizon==60:
                    row['ci_low'],row['ci_high']=bootstrap_day(g,score)
                phen.append(row)
    if not trades.empty:
        for key,base in trades.groupby(['construction','family','cohort']):
            for period,g in periods(base):
                if g.empty:
                    continue
                if period=='ALL':
                    ndays=len(unique_days)
                elif '-' in period:
                    a,b=map(int,period.split('-'))
                    ndays=sum(a<=int(d[:4])<=b for d in unique_days)
                else:
                    ndays=sum(int(d[:4])==int(period) for d in unique_days)
                for cost in (1,2,3):
                    net=g.gross_points-cost
                    equity=np.r_[0.,net.cumsum()]
                    closed_dd=float((np.maximum.accumulate(equity)-equity).max())
                    # Sampled minute adverse/close marks retained as per-trade trough.
                    # Conservative trough DD vs closed equity peak, not full tick path.
                    floor=np.r_[0.,net.cumsum().to_numpy()[:-1]]+g.worst_open_equity_points.to_numpy()-(cost-1)
                    open_dd=float((np.maximum.accumulate(equity[:-1])-floor).max())
                    gains=net[net>0].sum(); losses=-net[net<0].sum()
                    perf.append(dict(construction=key[0],family=key[1],cohort=key[2],period=period,cost_points=cost,
                                     n=len(g),trades_per_day=len(g)/ndays,PF=float(gains/losses) if losses else None,
                                     mean_R=float((net/g.planned_risk).mean()),net_points=float(net.sum()),net_usd=float(net.sum()*2),
                                     closed_DD_points=closed_dd,open_trough_DD_points=open_dd,win_rate=float((net>0).mean()),
                                     avg_win_points=float(net[net>0].mean()),avg_loss_points=float(net[net<0].mean()),
                                     ambiguous=int(g.ambiguous.sum()),gap_trades=int(g.gap_flag.sum())))
    return pd.DataFrame(phen),pd.DataFrame(perf)

def matched_controls(data, events, control_model='BALANCE'):
    nodes=events[(events.model=='NODE') & (events.construction=='HL') & (events.cohort!='OFF') & (events.outcome_valid==True)]
    controls=events[(events.model==control_model) & (events.cohort!='OFF')]
    if control_model=='BALANCE':
        controls=controls[controls.control_eligible==True]
    pool={}
    for key,g in controls.groupby(['family','year','side','cohort']):
        pool[key]=g
    rows=[]
    for _,e in nodes.iterrows():
        key=(e.family,e.year,e.side,e.cohort)
        c=pool.get(key)
        if c is None or not np.isfinite(e.atr) or e.atr<=0:
            rows.append(dict(event_id=e.event_id,matched=False));continue
        c=c[(c.minute_local//30==e.minute_local//30)&(abs(c.profile_age-e.profile_age)<=30)&(c.atr.between(e.atr/2,e.atr*2))].copy()
        if c.empty:
            rows.append(dict(event_id=e.event_id,matched=False));continue
        c['metric']=abs(np.log(c.atr/e.atr))
        match=c.sort_values(['metric','signal_time']).iloc[0]
        out=outcomes(data,match.to_dict(),float(e.distance))
        row=dict(event_id=e.event_id,matched=bool(out['outcome_valid']),control_id=match.event_id,
                 family=e.family,cohort=e.cohort,side=e.side,year=e.year,trade_date=e.trade_date,
                 distance=e.distance,control_day=match.trade_date,atr_ratio=match.atr/e.atr)
        if out['outcome_valid']:
            for h in (30,60,120):
                row[f'node_{h}']=e[f'hit_{h}'];row[f'control_{h}']=out[f'hit_{h}']
                row[f'lift_{h}']=e[f'hit_{h}']-out[f'hit_{h}']
                row[f'censored_{h}']=bool(e[f'censored_{h}'] or out[f'censored_{h}'])
        rows.append(row)
    result=pd.DataFrame(rows)
    result['control_model']=control_model
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic()
    data,qa=load_data(args.data)
    print('DATA VERIFIED',json.dumps(qa),flush=True)
    events,audits,diagnostics=[],[],{}
    for mode,kind in [('HL','NODE'),('CLOSE','NODE'),('TPO','NODE'),('HL','PSEUDO'),('HL','BALANCE')]:
        e,a,s=generate(data,mode,kind)
        events.extend(e);audits.extend(a);diagnostics[kind+'_'+mode]=s
        print('GENERATED',kind,mode,s,'seconds',round(time.monotonic()-started,1),flush=True)
    for k,e in enumerate(events):
        e['event_id']=k
        e.update(outcomes(data,e))
    events.sort(key=lambda e:(e['i'],e['model'],e['construction']))
    trades,gates=trade_engine(data,events)
    frame=pd.DataFrame(events)
    phen,perf=summaries(data,frame,trades)
    matches=pd.concat([matched_controls(data,frame,k) for k in ('BALANCE','PSEUDO')],ignore_index=True)
    frame.to_csv(args.out/'D02005_events.csv',index=False,float_format='%.10g')
    trades.to_csv(args.out/'D02006_trades.csv',index=False,float_format='%.10g')
    phen.to_csv(args.out/'D02007_phenomenon_summary.csv',index=False,float_format='%.10g')
    perf.to_csv(args.out/'D02008_baseline_summary.csv',index=False,float_format='%.10g')
    matches.to_csv(args.out/'D02009_matched_controls.csv',index=False,float_format='%.10g')
    # Compact freeze audit is folded into the machine-readable QA file, avoiding raw market redistribution.
    qa.update(generation=diagnostics,trade_gates=gates,freeze_count=len(audits),
              events=len(frame),trades=len(trades),elapsed_seconds=round(time.monotonic()-started,2),
              protocol_sha256=sha(Path(__file__).parents[2]/'docs/amt-node-v2/D02002_RULES_V2_DEV.md'),
              generator_sha256=sha(Path(__file__)),
              pine_compiled=False,pine_executed=False,parity_verified=False,optimization_executed=False,
              independent_validation_executed=False,funded_executed=False)
    (args.out/'D02010_run_manifest.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False)+'\n')
    print('FINISHED',len(frame),'events',len(trades),'trades',round(time.monotonic()-started,2),'seconds',flush=True)

if __name__=='__main__':
    main()
