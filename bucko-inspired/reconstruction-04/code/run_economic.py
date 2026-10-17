"""Execute the preregistered matrix, preserving frozen signal identity."""
from pathlib import Path
import json,hashlib,datetime
import pandas as pd
from execution import simulate,summary,SCENARIOS
from prepare_data import trade_dates
ROOT=Path(__file__).resolve().parents[1]

def label(dataset,model,scenario,rr):return f'{dataset}__{model}__{scenario}__R{rr:g}'
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--dataset',choices=['master','legacy'],required=True);a=ap.parse_args()
 lock=json.loads((ROOT/'protocol_lock.json').read_text());assert hashlib.sha256((ROOT/'PROTOCOL_PRE_RESULTS.md').read_bytes()).hexdigest()==lock['protocol_sha256']
 assert 'Ran 13 tests' in (ROOT/'work/execution_tests.txt').read_text() and (ROOT/'work/execution_tests.txt').read_text().strip().endswith('OK')
 black=set(pd.read_csv(ROOT/'data/holiday_blackout.csv').trade_date)
 if a.dataset=='master':sets=[('PRIMARY_ORIGINAL',['BASE1','SLIP2','TP_THROUGH2','NO_ENTRY_BAR_TP'],[ROOT/'results/signals/master_master.csv.gz']),('PINE_SEMANTICS_04_1',['BASE1'],[ROOT/'results/signals/master_pine_semantics.csv.gz'])]
 else:
  seg=pd.read_csv(ROOT/'results/legacy_segments.csv').symbol
  sets=[('PRIMARY_ORIGINAL',['BASE1','SLIP2'],[ROOT/f'results/signals/legacy_{s}.csv.gz' for s in seg])]
 out=ROOT/f'results/economic_{a.dataset}';out.mkdir(exist_ok=True)
 all_summaries=[];signal_month=[];signal_counts=[]
 for model,names,files in sets:
  acc={label(a.dataset,model,s,r):dict(trades=[],cand=[],daily=[],cum=0.,cumR=0.,peak=0.,peakR=0.,dd=0.,ddR=0.,both_touch=0,gap_exits=0,late_cutoff_exits=0,entry_gaps=0,rr=r,scenario=s,raw_bars=0,approved=0,long_signals=0,short_signals=0,bar_days=set(),observed_dates=set(),episodes=0) for s in names for r in [1.5,2.,3.]}
  for file in files:
   bars=pd.read_csv(file);bars['time']=pd.to_datetime(bars.time,utc=True);td=trade_dates(bars.time)
   m=pd.DataFrame({'month':td.str[:7],'raw_bars':(bars.raw_mask>0).astype(int),'raw_long':(bars.raw_mask%2==1).astype(int),'raw_short':(bars.raw_mask>=2).astype(int),'approved':(bars.approved_mask>0).astype(int),'approved_long':(bars.approved_mask==1).astype(int),'approved_short':(bars.approved_mask==2).astype(int)})
   mm=m.groupby('month').sum().reset_index();mm['dataset']=a.dataset;mm['signal_model']=model;signal_month.append(mm)
   sig=bars[bars.approved_mask>0].copy();sigtd=trade_dates(sig.time)
   episode=(sig.approved_mask!=sig.approved_mask.shift())|(sig.time.diff()>pd.Timedelta(minutes=15))|(sigtd!=sigtd.shift());episodes=int(episode.sum())
   for key,v in acc.items():
    tr,ca,da,mt=simulate(bars,v['rr'],SCENARIOS[v['scenario']],black,a.dataset)
    if len(tr):
     tr['variant']=key;tr['segment']=file.stem;tr['trade_id']=[f'{key}:{file.stem}:{i+1}' for i in range(len(tr))]
    ca['variant']=key;ca['segment']=file.stem;da['variant']=key;da['equity_close']+=v['cum'];da['realized_equity']+=v['cum'];da['realized_R']+=v['cumR']
    v['dd']=max(v['dd'],mt['max_barclose_mtm_dd_usd'],v['peak']-(v['cum']+mt['mtm_min']));v['peak']=max(v['peak'],v['cum']+mt['mtm_max'])
    v['ddR']=max(v['ddR'],mt['max_barclose_mtm_dd_R'],v['peakR']-(v['cumR']+mt['mtm_min_R']));v['peakR']=max(v['peakR'],v['cumR']+mt['mtm_max_R'])
    if len(tr):v['cum']+=tr.net_usd.sum();v['cumR']+=tr.net_R.sum()
    for k in ['both_touch','gap_exits','late_cutoff_exits','entry_gaps']:v[k]+=mt[k]
    v['trades'].append(tr);v['cand'].append(ca);v['daily'].append(da);v['raw_bars']+=int((bars.raw_mask>0).sum());v['approved']+=len(sig);v['long_signals']+=int((sig.approved_mask==1).sum());v['short_signals']+=int((sig.approved_mask==2).sum());v['bar_days'].update(td);v['observed_dates'].update(bars.time.dt.strftime('%Y-%m-%d'));v['episodes']+=episodes
    v['start']=min(v.get('start',bars.time.iloc[0]),bars.time.iloc[0]);v['end']=max(v.get('end',bars.time.iloc[-1]),bars.time.iloc[-1])
   print(json.dumps({'dataset':a.dataset,'model':model,'segment':file.name,'completed_variants':len(acc),'approved_signals':len(sig)}),flush=True)
  for key,v in acc.items():
   t=pd.concat(v['trades'],ignore_index=True);c=pd.concat(v['cand'],ignore_index=True);d=pd.concat(v['daily'],ignore_index=True)
   t.to_csv(out/(key+'_trades.csv.gz'),index=False,compression={'method':'gzip','mtime':0});c.to_csv(out/(key+'_candidates.csv.gz'),index=False,compression={'method':'gzip','mtime':0});d.to_csv(out/(key+'_daily.csv'),index=False)
   observed_days=len(v['bar_days']);span_days=(v['end']-v['start']).total_seconds()/86400+1/1440
   stats={**summary(t),'variant':key,'dataset':a.dataset,'signal_model':model,'scenario':v['scenario'],'rr':v['rr'],'start_utc':v['start'].isoformat(),'end_bar_utc':v['end'].isoformat(),'calendar_days_inclusive':(v['end'].date()-v['start'].date()).days+1,'observed_utc_dates':len(v['observed_dates']),'observed_trade_days':observed_days,'execution_allowed_observed_days':sum(pd.Timestamp(day).weekday()<5 and day not in black for day in v['bar_days']),'days_with_trades':t.trade_date.nunique() if len(t) else 0,'raw_event_bars':v['raw_bars'],'approved_signals':v['approved'],'approved_long':v['long_signals'],'approved_short':v['short_signals'],'signal_episodes_15m':v['episodes'],'entry_candidates':int(c.entry_candidate.sum()),'eligible_blocked_position':int(((c.disposition=='POSITION_OPEN')&c.entry_candidate).sum()),'occupied_at_signal_close':int(c.occupied_at_signal_close.sum()),'trades_per_calendar_week':len(t)/(span_days/7),'trades_per_observed_trade_day':len(t)/observed_days,'max_barclose_mtm_dd_usd':v['dd'],'max_barclose_mtm_dd_R':v['ddR'],**{k:v[k] for k in ['both_touch','gap_exits','late_cutoff_exits','entry_gaps']}}
   all_summaries.append(stats)
 pd.DataFrame(all_summaries).to_csv(out/'summary.csv',index=False)
 pd.concat(signal_month).groupby(['dataset','signal_model','month'],as_index=False).sum().to_csv(out/'signals_monthly.csv',index=False)
 (out/'run_completed.json').write_text(json.dumps({'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variants':len(all_summaries),'protocol_sha256':lock['protocol_sha256'],'execution_sha256':hashlib.sha256((ROOT/'code/execution.py').read_bytes()).hexdigest(),'signal_adapter_sha256':hashlib.sha256((ROOT/'code/signal_adapter.py').read_bytes()).hexdigest()},indent=2))
 print(pd.DataFrame(all_summaries)[['variant','trades','winrate','pf','net_usd','max_closed_dd_usd']].to_string(index=False),flush=True)
if __name__=='__main__':main()
