"""Frozen next-open execution assumptions. No signal changes or parameter search."""
from dataclasses import dataclass,asdict
from pathlib import Path
import math
import numpy as np
import pandas as pd
from prepare_data import trade_dates
TICK=.25;POINT_VALUE=2.;COMMISSION=1.
@dataclass(frozen=True)
class Scenario:
 name:str='BASE1'
 slippage_ticks:int=1
 penetration_ticks:int=1
 no_entry_bar_tp:bool=False
SCENARIOS={'BASE1':Scenario(),'SLIP2':Scenario('SLIP2',2),'TP_THROUGH2':Scenario('TP_THROUGH2',1,2),'NO_ENTRY_BAR_TP':Scenario('NO_ENTRY_BAR_TP',1,1,True)}

def hit_bracket(direction,stop,target,open_,high,low,entry_bar,scenario):
 """Returns (reference exit, reason, phase, both). Stops win OHLC ties."""
 s=direction;tp_allowed=not(scenario.no_entry_bar_tp and entry_bar)
 stop_at_open=s*(open_-stop)<=0
 tp_at_open=tp_allowed and s*(open_-target)>=scenario.penetration_ticks*TICK
 if stop_at_open:return open_,'STOP_GAP','OPEN',False
 if tp_at_open:return target,'TARGET_GAP_NO_IMPROVEMENT','OPEN',False
 stop_hit=low<=stop if s==1 else high>=stop
 target_hit=tp_allowed and (high>=target+scenario.penetration_ticks*TICK if s==1 else low<=target-scenario.penetration_ticks*TICK)
 if stop_hit:return stop,'STOP','INTRABAR',bool(target_hit)
 if target_hit:return target,'TARGET','INTRABAR',False
 return None

def simulate(bars,rr,scenario,blackouts,dataset):
 d=bars.reset_index(drop=True).copy();d['time']=pd.to_datetime(d.time,utc=True)
 # All calendar decisions depend on the current timestamp and saved ex-ante dates.
 times=d.time;close_times=times+pd.Timedelta(minutes=1)
 ny=times.dt.tz_convert('America/New_York');nyc=close_times.dt.tz_convert('America/New_York')
 minute=(ny.dt.hour*60+ny.dt.minute).to_numpy();cm=(nyc.dt.hour*60+nyc.dt.minute).to_numpy()
 td=trade_dates(times).to_numpy();ctd=trade_dates(close_times).to_numpy()
 def calendar_ok(day,m):return pd.Timestamp(day).weekday()<5 and day not in blackouts and (m<960 or m>=1080)
 # Unique-date cache avoids per-bar Timestamp parsing.
 day_ok={day:pd.Timestamp(day).weekday()<5 and day not in blackouts for day in set(td)|set(ctd)}
 enter_allowed=np.array([day_ok[t] and (m<960 or m>=1080) for t,m in zip(td,minute)])
 signal_allowed=np.array([day_ok[t] and (m<960 or m>=1080) for t,m in zip(ctd,cm)])
 rows=list(d.itertuples(index=False));n=len(rows)
 trades=[];candidates=[];daily={};pos=None;pending=None;real=realR=0.;peak=peakR=0.;low_eq=low_eqR=0.;max_mtm=max_mtmR=0.;flags={'both_touch':0,'gap_exits':0,'late_cutoff_exits':0,'entry_gaps':0}
 slip=scenario.slippage_ticks*TICK;cost_side=slip*POINT_VALUE
 def finish(i,reference,reason,phase,both=False):
  nonlocal pos,real,realR
  b=rows[i];gross=(reference-pos['entry_open'])*pos['direction']*POINT_VALUE;net=gross-2*cost_side-COMMISSION
  exit_time=b.time if phase=='OPEN' else b.time+pd.Timedelta(minutes=1)
  tr={**pos,'exit_bar_time':b.time.isoformat(),'exit_time':exit_time.isoformat(),'exit_phase':phase,'exit_reference_price':reference,'effective_exit_price':reference-pos['direction']*slip,'exit_reason':reason,'both_sl_tp':both,'gross_before_costs_usd':gross,'entry_slippage_usd':cost_side,'exit_execution_cost_usd':cost_side,'commission_usd':COMMISSION,'net_usd':net,'net_R':net/pos['risk_usd'],'gross_R':gross/pos['risk_usd'],'holding_minutes':(exit_time-pd.Timestamp(pos['entry_time'])).total_seconds()/60,'exit_bar_index':i}
  trades.append(tr);real+=net;realR+=tr['net_R'];flags['both_touch']+=int(both);flags['gap_exits']+=int(reason=='DATA_GAP');pos=None
 for i,b in enumerate(rows):
  gap=i>0 and (b.time-rows[i-1].time).total_seconds()!=60
  # No previous-bar-close exit can use knowledge of a future gap.
  if pos is not None:
   if gap:
    if td[i]!=pos['trade_date'] or minute[i]>=1005:flags['late_cutoff_exits']+=1
    finish(i,b.open,'DATA_GAP','OPEN')
   elif td[i]!=pos['trade_date'] or not day_ok[td[i]] or (990<=minute[i]<1080):
    flags['late_cutoff_exits']+=int(td[i]!=pos['trade_date'] or minute[i]>=1005)
    finish(i,b.open,'DAILY_FLAT','OPEN')
  if pending is not None:
   ci=pending['candidate_index'];c=candidates[ci]
   if not enter_allowed[i] or td[i]!=c['trade_date']:c['disposition']='NEXT_OPEN_OUTSIDE_WINDOW'
   elif pending['direction']*(b.open-pending['stop'])<=0:c['disposition']='NEXT_OPEN_PAST_STOP'
   elif pos is not None:raise AssertionError('overlapping pending order')
   else:
    s=pending['direction'];entry=b.open+s*slip;risk=s*(entry-pending['stop']);target_unrounded=entry+s*rr*risk
    target=(math.ceil(target_unrounded/TICK-1e-10) if s==1 else math.floor(target_unrounded/TICK+1e-10))*TICK
    pos={**pending['metadata'],'trade_id':len(trades)+1,'entry_time':b.time.isoformat(),'entry_open':float(b.open),'entry_fill':float(entry),'stop':float(pending['stop']),'target':float(target),'risk_usd':float(risk*POINT_VALUE),'target_R':float(s*(target-entry)/risk),'entry_bar_index':i,'entry_gap_minutes':float((b.time-pd.Timestamp(c['signal_time'])).total_seconds()/60-1)}
    c['disposition']='ENTERED';c['entry_time']=b.time.isoformat();flags['entry_gaps']+=int(gap)
   pending=None
  if pos is not None:
   hit=hit_bracket(pos['direction'],pos['stop'],pos['target'],b.open,b.high,b.low,i==pos['entry_bar_index'],scenario)
   if hit:finish(i,*hit)
  # State and signal are evaluated only at the completed bar.
  if b.approved_mask:
   assert b.approved_mask in (1,2)
   s=1 if b.approved_mask==1 else -1
   stop=(b.swing_low_close-TICK) if s==1 else (b.swing_high_close+TICK)
   known=np.isfinite(stop);valid=bool(known and s*(b.close-stop)>0)
   reason='SL_MISSING' if not known else 'SL_INVALID_AT_SIGNAL' if not valid else 'EXEC_WINDOW' if not signal_allowed[i] else 'POSITION_OPEN' if pos is not None else 'PENDING'
   typ='+'.join(k for k,key in [('BOS','bos'),('SWEEP','sweep'),('FVG','fvg'),('SD','sd')] if getattr(b,key+('L' if s==1 else 'S')))
   cand=dict(dataset=dataset,signal_model=b.signal_model,scenario=scenario.name,rr=rr,signal_time=b.time.isoformat(),signal_close_time=(b.time+pd.Timedelta(minutes=1)).isoformat(),trade_date=ctd[i],direction=s,score=b.score_L if s==1 else b.score_S,signal_type=typ,stop_at_signal=stop,stop_valid=valid,window_valid=bool(signal_allowed[i]),entry_candidate=bool(valid and signal_allowed[i]),occupied_at_signal_close=pos is not None,disposition=reason,entry_time='')
   candidates.append(cand)
   if reason=='PENDING':
    meta={k:cand[k] for k in ['dataset','signal_model','scenario','rr','signal_time','signal_close_time','trade_date','direction','score','signal_type']}
    meta.update(ema_regime=b.ema_regime,chop_regime=b.chop_regime,score_session=bool(b.score_session),symbol=b.symbol,signal_bar_index=i,signal_factor_mask=b.mask_L if s==1 else b.mask_S)
    pending=dict(direction=s,stop=stop,candidate_index=len(candidates)-1,metadata=meta)
  # Conservative liquidatable bar-close MTM, including commission and exit cost.
  unreal=0. if pos is None else (b.close-pos['entry_fill'])*pos['direction']*POINT_VALUE-COMMISSION-cost_side
  eq=real+unreal;eqR=realR+(unreal/pos['risk_usd'] if pos else 0.)
  low_eq=min(low_eq,eq);low_eqR=min(low_eqR,eqR);peak=max(peak,eq);peakR=max(peakR,eqR);max_mtm=max(max_mtm,peak-eq);max_mtmR=max(max_mtmR,peakR-eqR)
  daily[td[i]]=dict(trade_date=td[i],equity_close=eq,realized_equity=real,realized_R=realR)
 if pos is not None:
  finish(n-1,rows[-1].close,'END_SAMPLE','CLOSE')
  daily[td[-1]]=dict(trade_date=td[-1],equity_close=real,realized_equity=real,realized_R=realR)
 if pending is not None:candidates[pending['candidate_index']]['disposition']='END_OF_DATA'
 result=pd.DataFrame(trades);cand=pd.DataFrame(candidates)
 if len(result):
  assert (result.risk_usd>0).all()
  assert (pd.to_datetime(result.entry_time,utc=True)>=pd.to_datetime(result.signal_close_time,utc=True)).all()
  # Intrabar exits have an upper-bound timestamp; same-next-open is permitted.
  for a,b in zip(trades,trades[1:]):assert pd.Timestamp(a['exit_time'])<=pd.Timestamp(b['entry_time'])
  assert np.allclose(result.net_usd,result.gross_before_costs_usd-result.entry_slippage_usd-result.exit_execution_cost_usd-result.commission_usd,rtol=0,atol=1e-8)
 return result,cand,pd.DataFrame(daily.values()),dict(max_barclose_mtm_dd_usd=max_mtm,max_barclose_mtm_dd_R=max_mtmR,mtm_min=low_eq,mtm_max=peak,mtm_min_R=low_eqR,mtm_max_R=peakR,**flags)

def summary(trades):
 if len(trades)==0:return {'trades':0,'wins':0,'losses':0,'breakeven':0,'winrate':None,'pf':None,'net_usd':0,'expectancy_usd':None,'expectancy_R':None,'max_closed_dd_usd':0,'max_closed_dd_R':0}
 p=trades.net_usd.to_numpy();r=trades.net_R.to_numpy();wins=p>0;loss=p<0
 gross_profit=float(p[wins].sum());gross_loss=float(-p[loss].sum())
 eq=np.r_[0,np.cumsum(p)];eqR=np.r_[0,np.cumsum(r)];run=longest=0
 for x in p:run=run+1 if x<0 else 0;longest=max(longest,run)
 return dict(trades=len(p),wins=int(wins.sum()),losses=int(loss.sum()),breakeven=int((p==0).sum()),winrate=float(wins.mean()),gross_profit_net_trade_usd=gross_profit,gross_loss_net_trade_usd=gross_loss,pf=gross_profit/gross_loss if gross_loss else None,net_usd=float(p.sum()),gross_before_costs_usd=float(trades.gross_before_costs_usd.sum()),friction_usd=float((trades.entry_slippage_usd+trades.exit_execution_cost_usd+trades.commission_usd).sum()),expectancy_usd=float(p.mean()),expectancy_R=float(r.mean()),max_closed_dd_usd=float((np.maximum.accumulate(eq)-eq).max()),max_closed_dd_R=float((np.maximum.accumulate(eqR)-eqR).max()),mean_win_usd=float(p[wins].mean()) if wins.any() else None,mean_loss_usd=float(p[loss].mean()) if loss.any() else None,mean_win_R=float(r[wins].mean()) if wins.any() else None,mean_loss_R=float(r[loss].mean()) if loss.any() else None,max_loss_streak=longest,mean_risk_usd=float(trades.risk_usd.mean()),max_risk_usd=float(trades.risk_usd.max()),median_hold_minutes=float(trades.holding_minutes.median()))
