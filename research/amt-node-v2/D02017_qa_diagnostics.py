#!/usr/bin/env python3
"""Post-run QA and descriptive diagnostics. No parameter search or candidate selection."""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('amt',HERE/'D02004_research.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def records(frame):
    return json.loads(frame.to_json(orient='records'))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--out',type=Path,default=HERE/'results')
    a=ap.parse_args();p=a.out
    e=pd.read_csv(p/'D02005_events.csv');t=pd.read_csv(p/'D02006_trades.csv');matches=pd.read_csv(p/'D02009_matched_controls.csv')
    manifest=json.loads((p/'D02010_run_manifest.json').read_text())
    assert manifest['generator_sha256']==m.sha(HERE/'D02004_research.py')
    assert np.allclose(t.net_points,t.gross_points-1)
    assert np.allclose(t.R,t.net_points/t.planned_risk)
    assert (t.entry_i==t.i+1).all() and (t.exit_i>=t.entry_i).all()
    assert (t.source_last_i<t.i).all()
    assert np.allclose(t[['stop','order_target']].to_numpy()*4,np.round(t[['stop','order_target']].to_numpy()*4))
    for _,g in t.groupby(['construction','family','cohort']):
        assert (g.entry_i.to_numpy()[1:]>g.exit_i.to_numpy()[:-1]).all()
    data,_=m.load_data(a.data)
    # Exact event-prefix reproduction, with all later prices changed before recomputation.
    cutoff=50000
    d=dict(data);d['ends']=data['ends'][data['ends']<cutoff]
    d['x']=data['x'].copy();d['x'][cutoff:,:4]+=100000
    prefix,_,_=m.generate(d,'HL','NODE')
    expected=e[(e.model=='NODE')&(e.construction=='HL')&(e.i<cutoff)].sort_values('i')
    assert len(prefix)==len(expected)>0
    for x,(_,y) in zip(prefix,expected.iterrows()):
        for key in ('i','family','side','cohort','source_last_i','stop','order_target','valley','poc'):
            assert x[key]==y[key],(key,x[key],y[key])
    del d
    # Independent slow direct allocation vs optimized difference-array profile.
    rng=np.random.default_rng(20261012)
    candidates=e[(e.model=='NODE')&(e.construction=='HL')].source_last_i.unique()
    sampled=rng.choice(candidates,min(100,len(candidates)),replace=False)
    max_raw_error=0.
    for i in sampled:
        x=data['x'][i-149:i+1];pr=m.profile(x)
        direct=np.zeros(len(pr['raw']))
        for row in x:
            low=math.floor((row[2]-pr['anchor'])/pr['width']);high=math.floor((row[1]-pr['anchor'])/pr['width'])
            direct[low:high+1]+=row[4]/(high-low+1)
        err=float(np.max(np.abs(direct-pr['raw'])));max_raw_error=max(max_raw_error,err)
        np.testing.assert_allclose(direct,pr['raw'],rtol=1e-10,atol=1e-7)
    # Node-placement sensitivity on COMMON profile windows, not matching only profitable trades.
    common=[]
    for i in candidates:
        x=data['x'][i-149:i+1]
        hl=m.profile(x,'HL')
        for mode in ('CLOSE','TPO'):
            other=m.profile(x,mode)
            same_side=other['best'] is not None and other['best']['direction']==hl['best']['direction']
            common.append(dict(construction=mode,poc_delta_bins=abs(other['poc']-hl['poc'])/hl['width'],
                               corridor_available=other['best'] is not None,
                               same_side=same_side,
                               lvn_within_one_bin=same_side and abs(other['best']['valley']-hl['best']['valley'])<=hl['width']))
    common=pd.DataFrame(common)
    base=e[(e.model=='NODE')&(e.construction=='HL')&(e.cohort!='OFF')]
    valid=base[(base.outcome_valid==True)&(base.censored_60==False)].copy()
    qcols=['distance','distance_atr','duration_60','mfe_60','mae_60','return_5','return_15','return_30','profile_age']
    quantiles=valid.groupby(['family','cohort'])[qcols].quantile([.1,.25,.5,.75,.9]).reset_index().rename(columns={'level_2':'quantile'})
    ib=[]
    for label in ('NY','EU'):
        for key,g in valid.groupby(['family','cohort',f'ib_{label}_alignment'],dropna=False):
            ib.append(dict(ib=label,family=key[0],cohort=key[1],alignment=None if pd.isna(key[2]) else int(key[2]),
                           n=len(g),asymmetry60=float(g.hit_60.mean())))
    # Descriptive pooled volatility quartiles. Derived after the fact, NOT causal tradable filters.
    valid['volatility_quartile']=pd.qcut(valid.atr,4,labels=['Q1','Q2','Q3','Q4'],duplicates='drop')
    regimes=valid.groupby(['family','cohort','volatility_quartile'],observed=True).agg(n=('event_id','size'),asymmetry60=('hit_60','mean')).reset_index()
    matched=[]
    for key,g in matches[matches.matched==True].groupby(['control_model','family','cohort']):
        g=g[g.censored_60==False]
        if len(g):
            matched.append(dict(control=key[0],family=key[1],cohort=key[2],n=len(g),unique_control_events=g.control_id.nunique(),
                                node_asymmetry=float(g.node_60.mean()),control_asymmetry=float(g.control_60.mean()),
                                mean_lift=float(g.lift_60.mean())))
    sensitivity=[]
    for key,g in t.groupby(['construction','family','cohort']):
        for selection,label in [(np.ones(len(g),bool),'ALL'),(~g.degraded_source_or_trade,'EXCLUDE_DEGRADED'),(~g.gap_flag,'EXCLUDE_GAP_TRADES')]:
            z=g[selection];v=z.net_points
            sensitivity.append(dict(construction=key[0],family=key[1],cohort=key[2],sample=label,n=len(z),
                                    PF=float(v[v>0].sum()/-v[v<0].sum()) if (v<0).any() else None,net_points=float(v.sum())))
    # Independent year-by-year metrics re-sum exactly to full sample for each fixed model.
    perf=pd.read_csv(p/'D02008_baseline_summary.csv')
    for key,g in t.groupby(['construction','family','cohort']):
        r=perf[(perf.construction==key[0])&(perf.family==key[1])&(perf.cohort==key[2])&(perf.period=='ALL')&(perf.cost_points==1)].iloc[0]
        assert r.n==len(g) and abs(r.net_points-g.net_points.sum())<1e-7
    # Degraded flags use only source+event/trade exposure; no dates silently dropped.
    assert len(e)==manifest['events'] and len(t)==manifest['trades']
    out=dict(status='PYTHON_QA_PASS_NOT_PINE_COMPILATION',prefix_events_tested=len(prefix),
             prefix_cutoff_index=cutoff,independent_profile_windows_tested=len(sampled),max_raw_profile_error=max_raw_error,
             common_profile_window_population='HL frozen profiles that eventually emitted any event, including OFF-session',
             common_profile_windows=len(candidates),
             node_agreement=records(common.groupby('construction').agg(n=('same_side','size'),
                                   median_poc_delta_bins=('poc_delta_bins','median'),
                                   corridor_available=('corridor_available','mean'),same_side=('same_side','mean'),
                                   lvn_within_one_bin=('lvn_within_one_bin','mean')).reset_index()),
             signal_funnel=records(base.groupby(['family','cohort']).agg(signals=('event_id','size'),
                                  valid_geometry=('geometry_valid','sum'),valid_phenomenon=('outcome_valid','sum')).reset_index()),
             outcome_reasons=records(base.groupby(['family','cohort','outcome_reason']).size().rename('n').reset_index()),
             quantiles=records(quantiles),ib_descriptive_only=ib,regimes_descriptive_only=records(regimes),
             matched_control_descriptive=matched,matched_total=records(matches.groupby('control_model').agg(n=('event_id','size'),matched=('matched','sum')).reset_index()),
             sensitivity=sensitivity,
             diagnostic_notes=['No base-effect gate passed; IB incremental selection deliberately not performed.',
               'Matched controls reused; matched lift is descriptive, no independence or p-value claim.',
               'Open-trough DD uses sampled adverse excursion versus closed-equity peaks; not tick-accurate funded drawdown.',
               'Minute OHLC cannot certify actual intrabar order. No actual Pine execution occurred.'])
    (p/'D02016_diagnostics.json').write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({k:out[k] for k in ('status','prefix_events_tested','independent_profile_windows_tested','max_raw_profile_error','node_agreement','matched_control_descriptive','matched_total')},indent=2))

if __name__=='__main__':
    main()
