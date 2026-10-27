#!/usr/bin/env python3
"""Alert evidence reconciliation and synthetic semantic fixtures. NOT a CT backtest.

Accepts JSONL messages produced by alert_order_fills_template.txt plus optional
DIAGNOSTIC_NOT_A_TRADE events. No price/footprint inference from OHLCV is performed.
"""
import argparse, csv, json
from collections import Counter
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
from pathlib import Path
from zoneinfo import ZoneInfo

D=Decimal

def parse_utc(text):
    dt=datetime.fromisoformat(text.replace('Z','+00:00'))
    if dt.utcoffset() is None: raise ValueError('Timezone required')
    return dt

def session_open(stamp, cutoff):
    """Source session predicate; no holiday/calendar guarantees."""
    t=parse_utc(stamp).astimezone(ZoneInfo('America/New_York'))
    minute=t.hour*60+t.minute
    return (t.weekday()<5 and minute<cutoff) or ((t.weekday()==6 or t.weekday()<4) and minute>=1080)

def tick_round(value, up, tick=D('.25')):
    return (D(str(value))/tick).to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR)*tick

def adverse_stop_fill(side, stop, next_price, slip=D('.25')):
    """Synthetic conditional example only; not proof of TV tick path."""
    stop,next_price=D(str(stop)),D(str(next_price))
    return min(stop,next_price)-slip if side==1 else max(stop,next_price)+slip

def confirmed_htf_available(htf_close_ms, chart_open_ms):
    return htf_close_ms is not None and htf_close_ms <= chart_open_ms

def reconcile(events):
    diagnostics=[];fills=[];errors=[];duplicates=[];seen=set()
    for row,e in enumerate(events,1):
        if e.get('event')=='DIAGNOSTIC_NOT_A_TRADE':diagnostics.append(e);continue
        if e.get('event')!='ORDER_FILL':errors.append({'row':row,'error':'UNKNOWN_EVENT'});continue
        key=json.dumps(e,sort_keys=True,separators=(',',':'))
        if key in seen:
            duplicates.append(row); continue
        seen.add(key); fills.append((row,e))
    # A tied second does not reveal exchange/tick ordering. Entry-before-exit is
    # only a causal reconstruction for a common parent ID, and is disclosed.
    ties={t:n for t,n in Counter(e['tv_time_utc'] for _,e in fills).items() if n>1}
    fills.sort(key=lambda re:(parse_utc(re[1]['tv_time_utc']),re[1]['intent']['phase']!='ENTRY',re[0]))
    active={};trades=[];contexts={}
    for row,e in fills:
        try:
            intent=e['intent'];c=intent['context'];phase=intent['phase'];key=c['entry_order_id']
            qty=D(str(e['contracts']));price=D(str(e['fill_price']));side=int(c['side'])
            if side not in (-1,1) or qty<=0 or qty!=int(qty):raise ValueError('INVALID_SIDE_OR_QTY')
            if qty!=D(str(c['intended_qty'])):raise ValueError('QTY_MISMATCH')
            if tick_round(price,False)!=price:raise ValueError('OFF_TICK_FILL')
            if any(tick_round(c[k],False)!=D(str(c[k])) for k in ('intended_sl','intended_tp')):raise ValueError('OFF_TICK_INTENT')
            if parse_utc(e['tv_time_utc']).timestamp()*1000 < intent['order_created_ms']:raise ValueError('FILL_BEFORE_SUBMIT')
            if c['htf']['mode']=='CONFIRMED':
                for k in ('close5_ms','close15_ms','close60_ms','close240_ms'):
                    if not confirmed_htf_available(c['htf'][k],c['signal_bar_ms']):raise ValueError('UNKNOWN_OR_FUTURE_HTF')
            if phase=='ENTRY':
                if e['tv_order_id']!=key:raise ValueError('ENTRY_ID_MISMATCH')
                if e['action']!=('buy' if side==1 else 'sell'):raise ValueError('ENTRY_ACTION_MISMATCH')
                if active:raise ValueError('SINGLE_SLOT_VIOLATION')
                if D(str(e['position_size']))!=qty*side:raise ValueError('ENTRY_POSITION_MISMATCH')
                active[key]=e;contexts[key]=c
            else:
                if phase not in ('SL','TP','BRACKET','PAT','SESSION_OR_TEST_END'):raise ValueError('UNKNOWN_EXIT_PHASE')
                if key not in active:raise ValueError('EXIT_WITHOUT_ENTRY')
                if c!=contexts[key]:raise ValueError('FROZEN_CONTEXT_CHANGED')
                if phase in ('SL','TP','BRACKET') and e['tv_order_id']!=c['bracket_order_id']:raise ValueError('BRACKET_ID_MISMATCH')
                if e['action']!=('sell' if side==1 else 'buy'):raise ValueError('EXIT_ACTION_MISMATCH')
                if D(str(e['position_size']))!=0:raise ValueError('EXIT_NOT_FLAT')
                entry=active.pop(key);gross=side*(price-D(str(entry['fill_price'])))*2*qty
                trade={'entry_id':key,'entry_utc':entry['tv_time_utc'],'exit_utc':e['tv_time_utc'],
                       'model':c['model'],'side':side,'qty':str(qty),'entry':str(entry['fill_price']),
                       'exit':str(price),'intended_sl':str(c['intended_sl']),'intended_tp':str(c['intended_tp']),
                       'exit_phase':phase,'gross_usd':str(gross),'assumed_commission_usd':str(qty),
                       'net_usd_assuming_1usd_rt':str(gross-qty),
                       'adverse_points_from_intended_sl':str(-side*(price-D(str(c['intended_sl'])))) if phase=='SL' else None}
                trades.append(trade)
        except (KeyError,ValueError,TypeError) as ex:errors.append({'row':row,'error':str(ex)})
    return {'scope':'OBSERVED ALERT MESSAGES ONLY; no independent feed/fill verification',
            'diagnostic_events':len(diagnostics),'unique_fill_events':len(fills),'duplicate_rows_excluded':duplicates,
            'second_resolution_ties':ties,'errors':errors,'open_entry_ids':list(active),
            'trades':trades,'net_usd_assuming_1usd_rt':str(sum((D(t['net_usd_assuming_1usd_rt']) for t in trades),D(0)))}

def main():
    p=argparse.ArgumentParser();p.add_argument('jsonl',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    events=[json.loads(x) for x in a.jsonl.read_text().splitlines() if x.strip()]
    result=reconcile(events);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'reconciliation.json').write_text(json.dumps(result,indent=2)+'\n')
    if result['trades']:
        with (a.out/'observed_alert_trades.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(result['trades'][0]));w.writeheader();w.writerows(result['trades'])
    print(json.dumps({k:v for k,v in result.items() if k!='trades'},indent=2))
    if result['errors']:raise SystemExit(2)

if __name__=='__main__':main()
