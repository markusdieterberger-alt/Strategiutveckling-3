"""Frozen 36-run inversion experiment. Original execution source remains untouched."""
from pathlib import Path
import json, hashlib, datetime, argparse
import numpy as np
import pandas as pd
from reverse_adapter import ROOT, BASE, execution, simulate, trade_dates

def label(dataset, model, scenario, rr):
    return f'{dataset}__{model}__{scenario}__R{rr:g}'

def save_csv(df,path):
    tmp=path.with_name(path.name+'.tmp')
    df.to_csv(tmp,index=False,compression={'method':'gzip','mtime':0} if path.name.endswith('.gz') else None)
    tmp.replace(path)

def compare_original(key,t,c,d,stats,dataset):
    oldkey=key.replace('__ORIGINAL__','__PRIMARY_ORIGINAL__')
    folder=BASE/f'results/economic_{dataset}'
    checks={}
    for suffix,new in [('trades.csv.gz',t),('candidates.csv.gz',c),('daily.csv',d)]:
        old=pd.read_csv(folder/(oldkey+'_'+suffix))
        # Round-trip in-memory output to exactly the same CSV types as delivered RECON04.
        import io
        new=pd.read_csv(io.StringIO(new.to_csv(index=False)))
        cols=[x for x in old.columns if x not in ('variant','trade_id')]
        pd.testing.assert_frame_equal(old[cols].reset_index(drop=True),new[cols].reset_index(drop=True),check_dtype=False,rtol=1e-12,atol=1e-9)
        checks[suffix]=dict(rows=len(old),columns_compared=len(cols),passed=True)
    old=pd.read_csv(folder/'summary.csv').set_index('variant').loc[oldkey]
    for k,v in old.items():
        if k not in stats or k in ('signal_model',):continue
        if isinstance(v,(float,int,np.number)):
            assert np.isclose(v,stats[k],rtol=1e-12,atol=1e-8,equal_nan=True),(key,k,v,stats[k])
        else:assert str(v)==str(stats[k]),(key,k,v,stats[k])
    return dict(variant=key,passed=True,ledger_checks=checks,summary_fields_compared=len(old)-1)

def check_pair(bars,ca,cb,tr):
    assert len(ca)==len(cb)==int((bars.approved_mask>0).sum())
    for col in ['signal_time','signal_close_time','trade_date','score','signal_type','window_valid','source_direction']:
        pd.testing.assert_series_equal(ca[col],cb[col],check_names=False,check_dtype=False)
    assert (ca.direction==-cb.direction).all()
    b=bars[bars.approved_mask>0]
    newstop=np.where(b.approved_mask==1,b.swing_high_close+.25,b.swing_low_close-.25)
    assert np.allclose(cb.stop_at_signal,newstop,equal_nan=True,rtol=0,atol=1e-10)
    if len(tr):
        assert ((tr.entry_fill-tr.stop)*tr.direction>0).all()
        assert ((tr.target-tr.entry_fill)*tr.direction>0).all()
        joined=tr.merge(cb[['signal_time','direction','stop_at_signal','score']],on=['signal_time','direction'],suffixes=('','_candidate'),validate='one_to_one')
        assert len(joined)==len(tr)
        assert np.allclose(joined.stop,joined.stop_at_signal,rtol=0,atol=1e-10)
        assert (joined.score==joined.score_candidate).all()
    return dict(approved=len(cb),trades=len(tr),all_approved_directions_inverted=True,source_score_trigger_time_preserved=True,new_side_stop_verified=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=['master','legacy'],required=True);a=ap.parse_args()
    lock=json.loads((ROOT/'protocol_lock.json').read_text())
    assert hashlib.sha256((ROOT/'PROTOCOL_PRE_RESULTS.md').read_bytes()).hexdigest()==lock['sha256']
    assert hashlib.sha256((BASE/'code/execution.py').read_bytes()).hexdigest()=='802b406a465fabd64d9f4101dad03286f12dc6a647bdd19f3a0ac2ef2fe89d34'
    for f,n in [('original_tests.txt',13),('reverse_tests.txt',9)]:
        x=(ROOT/'work'/f).read_text();assert f'Ran {n} tests' in x and x.strip().endswith('OK')
    code_lock=json.loads((ROOT/'code_lock_pre_economic.json').read_text())
    for f,h in code_lock['sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
    black=set(pd.read_csv(BASE/'data/holiday_blackout.csv').trade_date)
    if a.dataset=='master':
        files=[ROOT/'cache/signals/master_master.csv.gz'];scenarios=['BASE1','SLIP2','TP_THROUGH2','NO_ENTRY_BAR_TP']
    else:
        files=[ROOT/f'cache/signals/legacy_{s}.csv.gz' for s in pd.read_csv(BASE/'results/legacy_segments.csv').symbol];scenarios=['BASE1','SLIP2']
    acc={label(a.dataset,m,s,r):dict(model=m,rr=r,scenario=s,trades=[],cand=[],daily=[],cum=0.,cumR=0.,peak=0.,peakR=0.,dd=0.,ddR=0.,both_touch=0,gap_exits=0,late_cutoff_exits=0,entry_gaps=0,raw_bars=0,approved=0,long_signals=0,short_signals=0,bar_days=set(),observed_dates=set(),episodes=0) for m in ['ORIGINAL','REVERSE'] for s in scenarios for r in [1.5,2.,3.]}
    out=ROOT/f'results/economic_{a.dataset}';out.mkdir(exist_ok=True)
    monthly=[];pair_checks=[]
    for file in files:
        bars=pd.read_csv(file);bars['time']=pd.to_datetime(bars.time,utc=True);td=trade_dates(bars.time)
        m=pd.DataFrame({'month':td.str[:7],'raw_bars':(bars.raw_mask>0).astype(int),'raw_long':(bars.raw_mask%2==1).astype(int),'raw_short':(bars.raw_mask>=2).astype(int),'approved':(bars.approved_mask>0).astype(int),'approved_source_long':(bars.approved_mask==1).astype(int),'approved_source_short':(bars.approved_mask==2).astype(int)})
        mm=m.groupby('month').sum().reset_index();mm['dataset']=a.dataset;monthly.append(mm)
        sig=bars[bars.approved_mask>0];sigtd=trade_dates(sig.time)
        episodes=int(((sig.approved_mask!=sig.approved_mask.shift())|(sig.time.diff()>pd.Timedelta(minutes=15))|(sigtd!=sigtd.shift())).sum())
        originals={}
        for key,v in acc.items():
            tr,ca,da,mt=simulate(bars,v['rr'],execution.SCENARIOS[v['scenario']],black,a.dataset,v['model']=='REVERSE')
            pairkey=(v['scenario'],v['rr'])
            if v['model']=='ORIGINAL':originals[pairkey]=ca.copy()
            else:pair_checks.append(dict(segment=file.name,scenario=v['scenario'],rr=v['rr'],**check_pair(bars,originals[pairkey],ca,tr)))
            if len(tr):
                tr['variant']=key;tr['segment']=file.stem;tr['trade_id']=[f'{key}:{file.stem}:{i+1}' for i in range(len(tr))]
            ca['variant']=key;ca['segment']=file.stem;da['variant']=key;da['equity_close']+=v['cum'];da['realized_equity']+=v['cum'];da['realized_R']+=v['cumR']
            v['dd']=max(v['dd'],mt['max_barclose_mtm_dd_usd'],v['peak']-(v['cum']+mt['mtm_min']));v['peak']=max(v['peak'],v['cum']+mt['mtm_max'])
            v['ddR']=max(v['ddR'],mt['max_barclose_mtm_dd_R'],v['peakR']-(v['cumR']+mt['mtm_min_R']));v['peakR']=max(v['peakR'],v['cumR']+mt['mtm_max_R'])
            if len(tr):v['cum']+=tr.net_usd.sum();v['cumR']+=tr.net_R.sum()
            for k in ['both_touch','gap_exits','late_cutoff_exits','entry_gaps']:v[k]+=mt[k]
            v['trades'].append(tr);v['cand'].append(ca);v['daily'].append(da)
            v['raw_bars']+=int((bars.raw_mask>0).sum());v['approved']+=len(sig)
            v['long_signals']+=int((sig.approved_mask==(2 if v['model']=='REVERSE' else 1)).sum())
            v['short_signals']+=int((sig.approved_mask==(1 if v['model']=='REVERSE' else 2)).sum())
            v['bar_days'].update(td);v['observed_dates'].update(bars.time.dt.strftime('%Y-%m-%d'));v['episodes']+=episodes
            v['start']=min(v.get('start',bars.time.iloc[0]),bars.time.iloc[0]);v['end']=max(v.get('end',bars.time.iloc[-1]),bars.time.iloc[-1])
        print(json.dumps(dict(dataset=a.dataset,segment=file.name,completed_variants=len(acc),approved=len(sig))),flush=True)
    summaries=[];parity=[]
    for key,v in acc.items():
        t=pd.concat(v['trades'],ignore_index=True);c=pd.concat(v['cand'],ignore_index=True);d=pd.concat(v['daily'],ignore_index=True)
        days=len(v['bar_days']);span=(v['end']-v['start']).total_seconds()/86400+1/1440
        stats={**execution.summary(t),'variant':key,'dataset':a.dataset,'signal_model':'PRIMARY_ORIGINAL' if v['model']=='ORIGINAL' else 'REVERSE_01','model':v['model'],'scenario':v['scenario'],'rr':v['rr'],'start_utc':v['start'].isoformat(),'end_bar_utc':v['end'].isoformat(),'calendar_days_inclusive':(v['end'].date()-v['start'].date()).days+1,'observed_utc_dates':len(v['observed_dates']),'observed_trade_days':days,'execution_allowed_observed_days':sum(pd.Timestamp(day).weekday()<5 and day not in black for day in v['bar_days']),'days_with_trades':t.trade_date.nunique() if len(t) else 0,'raw_event_bars':v['raw_bars'],'approved_signals':v['approved'],'approved_long':v['long_signals'],'approved_short':v['short_signals'],'signal_episodes_15m':v['episodes'],'entry_candidates':int(c.entry_candidate.sum()),'eligible_blocked_position':int(((c.disposition=='POSITION_OPEN')&c.entry_candidate).sum()),'occupied_at_signal_close':int(c.occupied_at_signal_close.sum()),'trades_per_calendar_week':len(t)/(span/7),'trades_per_observed_trade_day':len(t)/days,'max_barclose_mtm_dd_usd':v['dd'],'max_barclose_mtm_dd_R':v['ddR'],**{k:v[k] for k in ['both_touch','gap_exits','late_cutoff_exits','entry_gaps']}}
        if v['model']=='ORIGINAL':parity.append(compare_original(key,t,c,d,stats,a.dataset))
        save_csv(t,out/(key+'_trades.csv.gz'));save_csv(c,out/(key+'_candidates.csv.gz'));save_csv(d,out/(key+'_daily.csv'));summaries.append(stats)
    expected=4007 if a.dataset=='master' else 24603
    assert all(s['approved_signals']==expected for s in summaries)
    save_csv(pd.DataFrame(summaries),out/'summary.csv')
    save_csv(pd.concat(monthly).groupby(['dataset','month'],as_index=False).sum(),out/'signals_monthly.csv')
    (out/'original_parity.json').write_text(json.dumps(parity,indent=2))
    (out/'inversion_qa.json').write_text(json.dumps(pair_checks,indent=2))
    (out/'run_completed.json').write_text(json.dumps(dict(completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),variants=len(summaries),protocol_sha256=lock['sha256'],code_lock=code_lock,original_parity_pass=True,inversion_qa_pass=True),indent=2))
    print(pd.DataFrame(summaries)[['variant','trades','winrate','pf','net_usd','max_closed_dd_usd']].to_string(index=False),flush=True)

if __name__=='__main__':main()
