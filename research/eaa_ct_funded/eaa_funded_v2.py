#!/usr/bin/env python3
"""EAA CT Scalper exploratory funded 15-session evaluation, source TV trade CSV.
No independent TV rerun or tick replay. Uses 1-MNQ TV fills as CONDITIONAL opportunity stream.
Only exec with -600 DLL, -1000 EOD MLL, 50% consistency, stop risk gate.
"""
import csv, datetime as dt, statistics, collections, itertools, random, math, json, re
from zoneinfo import ZoneInfo
from pathlib import Path
D=Path('/mnt/data')
SRC=D/'EAA_CT_Scalper_STRATEGY_V1_CME_MINI_MNQ1!_2026-10-11_05989.csv'
TZ=ZoneInfo('Europe/Stockholm'); NY=ZoneInfo('America/New_York')
MODELS=('FADE','DIV','TRAP','AGG','ABSORB','VRZ')
TGT=1250.0; DLL=600.; MLL=1000.; MAXSIZE=20.; CONS=.50
CUTOFF=dt.datetime(2026,10,9,tzinfo=TZ)
MONTH_START=dt.datetime(2026,9,9,tzinfo=TZ)
C365=dt.datetime(2025,10,9,tzinfo=TZ)
C2026=dt.datetime(2026,1,1,tzinfo=TZ)

def import_trades(path):
    raw=list(csv.DictReader(open(path,encoding='utf-8-sig',newline='')))
    ee={int(r['Trade number']):r for r in raw if r['Type'].startswith('Entry')}
    xx={int(r['Trade number']):r for r in raw if r['Type'].startswith('Exit')}
    assert len(ee)==len(xx)==1197 and set(ee)==set(xx)
    out=[]
    for i in sorted(ee):
        e=ee[i]; x=xx[i];label=e['Signal'].split('|')[0];model=label.split('_')[-1]
        assert model in MODELS
        entry=dt.datetime.strptime(e['Date and time'],'%Y-%m-%d %H:%M').replace(tzinfo=TZ)
        exit=dt.datetime.strptime(x['Date and time'],'%Y-%m-%d %H:%M').replace(tzinfo=TZ)
        if exit<entry: raise ValueError('Time backwards')
        ny=entry.astimezone(NY)
        if ny.hour>=18: market_day=ny.date()+dt.timedelta(days=1)
        else: market_day=ny.date()
        ep=float(e['Price USD']);slmatch=re.search(r'\|SL=([0-9.]+)\|TP=([0-9.]+)',e['Signal']);assert slmatch,e['Signal']
        sl=float(slmatch.group(1));tp=float(slmatch.group(2))
        risk=(abs(ep-sl)*2.0+1.0) # MNQ index point value $2, fee $1 RT included
        exitprofit=float(x['Net PnL USD']);mae=float(x['Adverse excursion USD']);mfe=float(x['Favorable excursion USD'])
        out.append({'id':i,'entry':entry,'exit':exit,'market_day':market_day,'model':model,'side':'LONG' if 'long' in e['Type'] else 'SHORT',
        'pnl':exitprofit,'mae':mae,'mfe':mfe,'entry_px':ep,'sl':sl,'tp':tp,'risk':risk,'duration':int(x['Duration (bars)']), 'exit_reason':x['Signal'],
        'rr_proxy':abs(tp-ep)/abs(ep-sl) if abs(ep-sl)>0 else 0.,'ny_hour':ny.hour,'ny_wd':ny.weekday(),'signal':e['Signal']})
    assert all(t['entry']<CUTOFF for t in out)
    out.sort(key=lambda x:(x['entry'],x['id']))
    assert all(out[i]['entry']>=out[i-1]['exit']-dt.timedelta(minutes=1) for i in range(1,len(out))) # no overlapping trades; ties possible
    return out
T=import_trades(SRC)

def subset(trs,start,end=CUTOFF): return [t for t in trs if t['entry']>=start and t['entry']<end]
PERIODS={'trailing_365d':subset(T,C365),'calendar_2026':subset(T,C2026),'last_30d':subset(T,MONTH_START)}
PERIOD_START={'trailing_365d':C365,'calendar_2026':C2026,'last_30d':MONTH_START}

def sessions(period):
    # Conservative standardized roll: NY weekdays, including some CME closed days as zero-trade days.
    a=PERIOD_START[period].astimezone(NY).date();b=dt.date(2026,10,8)
    days=[];c=a
    while c<=b:
        if c.weekday()<5: days.append(c)
        c+=dt.timedelta(days=1)
    return days

def trade_sig(t):return (t['entry'],t['exit'],t['model'],t['side'],t['pnl'],t['exit_reason'])
ref=import_trades(D/'EAA_CT_Scalper_STRATEGY_V1_CME_MINI_MNQ1!_2026-10-11_05989.csv')
assert len(T)==1197
assert collections.Counter(trade_sig(t) for t in T if t['entry'].year==2026)==collections.Counter(trade_sig(t) for t in subset(T,C2026))

# Trailing EOD MLL is initially -1000 and locks at +100 once prior highest EOD profit >=+1100.
def run_window(trs,days,models,qmode,qvalue,extra_per_mnq=0.,day_profit_stop=None, intraday='liquidate_DLL', risk_buffer=5.):
    selected=set(models)
    groups=collections.defaultdict(list)
    for t in trs:
        if t['model'] in selected:groups[t['market_day']].append(t)
    balance=0.; peak_eod=0.; floor=-MLL;largest_profit_day=0.;lastday=None
    total_executed=0;total_skipped=0; dll_hits=0;max_contracts=0;max_worst_sl=0;max_drawdown=0;realized_peak=0;
    for day_index,day in enumerate(days):
        start_balance=balance;locked=False
        for t in groups.get(day,[]):
            if locked:
                total_skipped+=1;continue
            # Only trades actually in allowed historical strategy session; exact market holiday/halfday handling already part of TV native fills.
            risk_per_mnq=t['risk']+extra_per_mnq
            maxq=min(20,int((start_balance-balance+DLL-risk_buffer)//risk_per_mnq),int((balance-floor-risk_buffer)//risk_per_mnq))
            if qmode=='fixed': q=min(int(qvalue),maxq) if maxq>=int(qvalue) else 0
            elif qmode=='riskcap':q=min(maxq, int(float(qvalue)//risk_per_mnq))
            else:raise ValueError(qmode)
            if q<=0:
                total_skipped+=1;continue
            total_executed+=1;max_contracts=max(max_contracts,q)
            position_pnl=q*(t['pnl']-extra_per_mnq)
            # Reported MAE is adverse excursion over entire trade, not timestamped.
            # use MAE-first conditional liquidation; one-minute footprint path not available.
            worst=q*(min(0.,t['mae']-extra_per_mnq))
            max_worst_sl=max(max_worst_sl,risk_per_mnq*q)
            if intraday=='liquidate_DLL':
                # First threshold reached along a pessimistic continuous path from entry to MAE.
                dll_remaining=start_balance-DLL-balance
                mll_remaining=floor-balance
                if balance+worst<=floor+1e-9 and floor>=start_balance-DLL-1e-9:
                    # MLL at/above daily DLL; hard breach first.
                    return {'outcome':'FAIL','reason':'MLL_INTRADAY','days':day_index+1,'trades':total_executed,'balance':round(balance+worst,2),'dll_hits':dll_hits,'skipped':total_skipped,'maxq':max_contracts}
                if balance+worst<=start_balance-DLL+1e-9:
                    # DLL soft lock and forced close at threshold plus $5 adverse execution stress.
                    # Amount must not unrealistically improve an already filled worse exit.
                    breach_pnl=min(position_pnl,(start_balance-DLL-balance)-5.0)
                    balance+=breach_pnl;locked=True;dll_hits+=1
                    if balance<=floor:
                        return {'outcome':'FAIL','reason':'MLL_AFTER_DLL','days':day_index+1,'trades':total_executed,'balance':round(balance,2),'dll_hits':dll_hits,'skipped':total_skipped,'maxq':max_contracts}
                    continue
                if balance+worst<=floor+1e-9:
                    return {'outcome':'FAIL','reason':'MLL_INTRADAY','days':day_index+1,'trades':total_executed,'balance':round(balance+worst,2),'dll_hits':dll_hits,'skipped':total_skipped,'maxq':max_contracts}
                balance+=position_pnl
            elif intraday=='MAE_hard':
                # Strong stress: assume MLL breach can occur despite DLL intervention.
                if balance+worst<=floor+1e-9:
                    return {'outcome':'FAIL','reason':'MLL_ADVERSE_STRESS','days':day_index+1,'trades':total_executed,'balance':round(balance+worst,2),'dll_hits':dll_hits,'skipped':total_skipped,'maxq':max_contracts}
                if balance+worst<=start_balance-DLL+1e-9:
                    dll_hits+=1;locked=True
                    balance+=min(position_pnl,worst)
                else:balance+=position_pnl
            else:raise ValueError(intraday)
            if balance<=floor:
                return {'outcome':'FAIL','reason':'MLL_CLOSE','days':day_index+1,'trades':total_executed,'balance':round(balance,2),'dll_hits':dll_hits,'skipped':total_skipped,'maxq':max_contracts}
            if day_profit_stop is not None and balance-start_balance>=day_profit_stop:
                locked=True
        day_profit=balance-start_balance
        largest_profit_day=max(largest_profit_day,day_profit)
        peak_eod=max(peak_eod,balance)
        floor=min(100.,peak_eod-1000.)
        realized_peak=max(realized_peak,balance)
        max_drawdown=max(max_drawdown,realized_peak-balance)
        # Do not declare pass before trade group and prior EOD compliance.
        # Exact Lucid cushion details vary; here strict 50% of cumulative profit.
        if balance>=TGT and largest_profit_day<=CONS*balance+1e-8:
            return {'outcome':'PASS','reason':'TARGET_CONSISTENCY','days':day_index+1,'trades':total_executed,'balance':round(balance,2),'dll_hits':dll_hits,'skipped':total_skipped,'maxq':max_contracts}
    return {'outcome':'ALIVE','reason':'HORIZON','days':len(days),'trades':total_executed,'balance':round(balance,2),'dll_hits':dll_hits,'skipped':total_skipped,'maxq':max_contracts}

def evaluate(period,models,qmode,qvalue,extra=0.,daycap=None,mode='liquidate_DLL',winsize=15):
    all_days=sessions(period)
    start=PERIOD_START[period].astimezone(NY).date()
    period_trades=[t for t in PERIODS[period] if t['market_day']>=start]
    outs=[]
    for i in range(len(all_days)-winsize+1):
        d=all_days[i:i+winsize];tt=[t for t in period_trades if d[0]<=t['market_day']<=d[-1]]
        v=run_window(tt,d,models,qmode,qvalue,extra,daycap,mode)
        v['start']=str(d[0]);v['end']=str(d[-1]);outs.append(v)
    n=len(outs);passn=sum(z['outcome']=='PASS' for z in outs);failn=sum(z['outcome']=='FAIL' for z in outs)
    dayspass=sorted(z['days'] for z in outs if z['outcome']=='PASS')
    return {'period':period,'models':'+'.join(models),'qmode':qmode,'qvalue':qvalue,'extra_per_contract':extra,'daycap':daycap or 'NONE', 'intraday':mode,
      'windows':n,'pass':passn,'fail':failn,'alive':n-passn-failn,'pass_pct':round(passn/n*100,2) if n else None,'fail_pct':round(failn/n*100,2) if n else None,
      'alive_pct':round((n-passn-failn)/n*100,2) if n else None,'median_pass_day':statistics.median(dayspass) if dayspass else '',
      'mean_end_balance':round(statistics.mean(z['balance'] for z in outs),2) if n else None,'median_executed':statistics.median(z['trades'] for z in outs) if n else None,
      'median_skipped':statistics.median(z['skipped'] for z in outs) if n else None,'mean_dll_hits':round(statistics.mean(z['dll_hits'] for z in outs),2) if n else None,'max_q':max((z['maxq'] for z in outs),default=0)},outs

if __name__=='__main__':
 print('SOURCE',SRC.name,len(T),'rows; UTC offset diagnostic',len(PERIODS['calendar_2026']))
 for p in PERIODS:
  arr=PERIODS[p]
  print('PERIOD',p,'first/last',arr[0]['entry'],arr[-1]['exit'],'trades',len(arr),'days',len(sessions(p)),'windows',len(sessions(p))-14)
 for combo in [MODELS,('FADE','DIV','TRAP'),('FADE','DIV'),('FADE','ABSORB'),('ABSORB',),('DIV','ABSORB')]:
  for q in (2,3,4,5,6):
   row,_=evaluate('calendar_2026',combo,'fixed',q)
   print('EXAMPLE',row['models'],q,row['pass_pct'],row['fail_pct'],row['median_pass_day'],row['median_executed'])
