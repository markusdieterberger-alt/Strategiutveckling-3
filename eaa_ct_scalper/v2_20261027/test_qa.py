"""Meaningful local checks. Passing is NOT native Pine/TV parity."""
import unittest, hashlib, re, copy
from pathlib import Path
from decimal import Decimal as D
import build_v2
from qa_tools import *

ROOT=Path(__file__).resolve().parent
SRC=(ROOT/'reference/EAA_CT_SCALPER_STRATEGY_V1.pine').read_text()
V2=(ROOT/'pine/EAA_CT_SCALPER_V2_DEV.pine').read_text()
DIAG=(ROOT/'pine/EAA_CT_DIAGNOSTIC_V1_V2.pine').read_text()

def functions(s):
    out={};ls=s.splitlines()
    for i,l in enumerate(ls):
        m=re.match(r'(f_\w+)\(.*=>$',l)
        if m:
            j=i+1
            while j<len(ls) and (not ls[j].strip() or ls[j].startswith(' ')):j+=1
            out[m[1]]='\n'.join(ls[i:j]).rstrip()
    return out

def fixture():
    c={'version':'SYNTHETIC_ONLY','model':'ABSORB','side':1,'entry_order_id':'CT2_L_ABSORB_100',
       'bracket_order_id':'CT2_X_100','signal_bar_ms':0,'signal_close_ms':60000,'intended_qty':1,
       'intended_sl':99.5,'intended_tp':102,'htf':{'mode':'CONFIRMED',**{x:0 for x in ['close5_ms','close15_ms','close60_ms','close240_ms']}}}
    e={'event':'ORDER_FILL','tv_time_utc':'2026-10-27T09:00:00Z','tv_order_id':c['entry_order_id'],
       'action':'buy','contracts':1,'fill_price':100,'position_size':1,'comment':'test',
       'intent':{'phase':'ENTRY','order_created_ms':60000,'context':c}}
    x=copy.deepcopy(e);x.update(tv_order_id=c['bracket_order_id'],action='sell',fill_price=99.25,position_size=0)
    x['intent']['phase']='SL';return [e,x]

class SourceAndCausalityTests(unittest.TestCase):
    def test_source_hash_and_deterministic_build(self):
        self.assertEqual(hashlib.sha256(SRC.encode()).hexdigest(),build_v2.SOURCE_SHA)
        self.assertEqual(build_v2.derive(SRC),V2)
        self.assertEqual(build_v2.derive(SRC,True),DIAG)
    def test_original_functions_unchanged(self):
        for text in (V2,DIAG):
            for k,v in functions(SRC).items():self.assertEqual(functions(text)[k],v,k)
    def test_model_region_unchanged_after_removing_telemetry(self):
        def section(s):return s[s.index('// ── ENTRY GATES'):s.index('// ── SMART EXIT')]
        for text in (V2,DIAG):
            region=section(text)
            region=re.sub(r'^if use\w+ and ct(?:Long|Short)FiredThisBar\n    v2PrioritySkipped \+= \d+\n','',region,flags=re.M)
            region=re.sub(r'^\s+v2(?:EvalMask|FlowMask|RawMask) \+= \d+\n','',region,flags=re.M)
            self.assertEqual(region,section(SRC))
    def test_signal_inputs_and_properties_preserved(self):
        inputs=lambda s:[x.strip() for x in s.splitlines() if 'input.' in x and not x.startswith('bool v2') and 'eaaStressSlip' not in x]
        self.assertEqual(inputs(SRC),inputs(V2));self.assertEqual(inputs(SRC),inputs(DIAG))
        for text in (V2,DIAG):
            for flag in ('calc_on_every_tick=false','calc_on_order_fills=false','process_orders_on_close=false','use_bar_magnifier=true','slippage=1','backtest_fill_limits_assumption=1','pyramiding=0'):
                self.assertIn(flag,text)
    def test_htf_offsets_and_daily_unchanged(self):
        for tf,n in [('5',5),('15',5),('60',5),('240',3)]:
            m=re.search(r'request.security\(syminfo.tickerid, "'+tf+r'",\n    \[(.*?)\], lookahead=barmerge.lookahead_on\)',V2)
            self.assertIsNotNone(m);self.assertEqual(m[1].count('[1]'),n+1 if tf!='240' else n)
        daily=lambda s:s[s.index('[pivotP,'):s.index('//',s.index('lookahead=barmerge.lookahead_on)',s.index('[pivotP,')))]
        self.assertEqual(daily(SRC),daily(V2))
        self.assertEqual(V2.count('request.footprint(50, 70)'),1)
    def test_htf_boundary_no_early_access(self):
        # Last confirmed 15m close is available from the NEXT 1m bar's open.
        boundary=15*60000
        self.assertFalse(confirmed_htf_available(boundary,boundary-60000))
        self.assertTrue(confirmed_htf_available(boundary,boundary))
        self.assertFalse(confirmed_htf_available(None,boundary))
    def test_no_fake_native_fill_in_payload(self):
        self.assertNotIn('{{',V2)
        self.assertNotIn('eaaStressNet',V2)
        self.assertEqual(V2.count('alert_profit=v2TpPayload, alert_loss=v2SlPayload'),2)
        for field in ('signal_bar_ms','signal_close_ms','intended_sl','intended_tp','order_created_ms','entry_order_id','bracket_order_id'):self.assertIn(field,V2)
        self.assertIn('"fill_price":{{strategy.order.price}}',(ROOT/'alert_order_fills_template.txt').read_text())
    def test_bracket_written_at_submission_only(self):
        assignments=re.findall(r'^\s*(ctActiveS[l]|ctActiveTp) := (.+)$',V2,re.M)
        for var,value in assignments:self.assertIn(value,('na','finalSl','finalTp'))
        self.assertIn('if not barstate.isconfirmed or v2CalcInBar > 1',V2)
        self.assertNotIn('if not barstate.isconfirmed or v2CalcInBar > 1',DIAG)
    def test_plot_request_budget_static(self):
        for s in (V2,DIAG):
            count=len(re.findall(r'^plot\(',s,re.M))+1 # SuperTrend series color
            self.assertLessEqual(count,64)
            self.assertLessEqual(s.count('request.security(')+s.count('request.footprint('),40)
    def test_us_europe_dst_divergence(self):
        self.assertTrue(session_open('2026-10-26T20:43:00Z',1004))
        self.assertFalse(session_open('2026-10-26T20:44:00Z',1004))
        self.assertTrue(session_open('2026-11-02T21:43:00Z',1004))
        self.assertFalse(session_open('2026-11-02T21:44:00Z',1004))
        self.assertEqual(parse_utc('2026-10-27T09:07:00Z').astimezone(ZoneInfo('Europe/Stockholm')).hour,10)
    def test_tick_and_adverse_gap_bounds(self):
        self.assertEqual(tick_round('100.13',False),D('100'))
        self.assertEqual(tick_round('100.13',True),D('100.25'))
        self.assertEqual(adverse_stop_fill(1,99.5,98),D('97.75'))
        self.assertEqual(adverse_stop_fill(-1,100.5,102),D('102.25'))

class AlertTests(unittest.TestCase):
    def test_same_second_pair_is_disclosed(self):
        r=reconcile(fixture());self.assertFalse(r['errors']);self.assertEqual(r['net_usd_assuming_1usd_rt'],'-2.50');self.assertTrue(r['second_resolution_ties'])
    def test_diagnostic_is_not_a_trade(self):
        r=reconcile([{'event':'DIAGNOSTIC_NOT_A_TRADE'}]);self.assertEqual(len(r['trades']),0)
    def test_duplicate_alert_does_not_double_count(self):
        f=fixture();r=reconcile(f+[copy.deepcopy(f[1])]);self.assertEqual(r['duplicate_rows_excluded'],[3]);self.assertEqual(len(r['trades']),1)
    def test_changed_stop_is_flagged(self):
        f=fixture();f[1]['intent']['context']['intended_sl']=99;r=reconcile(f);self.assertIn('FROZEN_CONTEXT_CHANGED',str(r['errors']))
    def test_exit_without_entry_is_not_invented(self):
        r=reconcile([fixture()[1]]);self.assertIn('EXIT_WITHOUT_ENTRY',str(r['errors']));self.assertFalse(r['trades'])
    def test_reversal_and_partial_close_rejected(self):
        f=fixture();f[1]['position_size']=-1;self.assertIn('EXIT_NOT_FLAT',str(reconcile(f)['errors']))
        f=fixture();f[1]['contracts']=0.5;self.assertIn('INVALID_SIDE_OR_QTY',str(reconcile(f)['errors']))
    def test_unknown_or_future_htf_is_not_passed(self):
        f=fixture();f[0]['intent']['context']['htf']['close15_ms']=60000
        self.assertIn('UNKNOWN_OR_FUTURE_HTF',str(reconcile(f)['errors']))

if __name__=='__main__':unittest.main(verbosity=2)
