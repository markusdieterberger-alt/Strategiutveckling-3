import unittest,sys
from pathlib import Path
import pandas as pd
import numpy as np
from execution import hit_bracket,SCENARIOS,simulate,summary
from signal_adapter import run_original,pine_semantics

def fixture(start='2026-09-22T13:30:00Z',n=5):
 rows=[]
 for t in pd.date_range(start,periods=n,freq='min'):
  rows.append(dict(time=t,open=100.,high=101.,low=99.,close=100.,volume=10,raw_mask=0,approved_mask=0,score_L=6,score_S=6,mask_L=1023,mask_S=1023,bosL=False,bosS=False,sweepL=False,sweepS=False,fvgL=False,fvgS=False,sdL=False,sdS=False,swing_low_close=95.,swing_high_close=105.,ema_regime='BULL',chop_regime='TREND',score_session=True,signal_model='TEST',symbol='MNQZ6'))
 d=pd.DataFrame(rows);d.loc[0,['approved_mask','raw_mask','bosL']]=[1,1,True];return d
class ExecutionTests(unittest.TestCase):
 def test_next_open_costs_and_stop_frozen(self):
  d=fixture(n=2);d.loc[1,['open','high','low','close','swing_low_close']]=[102.,104.,101.,103.,80.]
  t,c,_,_=simulate(d,2,SCENARIOS['BASE1'],set(),'TEST')
  self.assertEqual(t.iloc[0].entry_fill,102.25);self.assertEqual(t.iloc[0].stop,94.75)
  self.assertEqual(t.iloc[0].net_usd,0.);self.assertEqual(t.iloc[0].gross_before_costs_usd,2.)
  self.assertEqual(t.iloc[0].entry_time,d.time.iloc[1].isoformat())
 def test_stop_first_ambiguous_bar(self):
  hit=hit_bracket(1,95,110,100,112,94,False,SCENARIOS['BASE1']);self.assertEqual(hit,(95,'STOP','INTRABAR',True))
 def test_gap_stop_uses_worse_open(self):
  self.assertEqual(hit_bracket(1,95,110,90,92,89,False,SCENARIOS['BASE1'])[:3],(90,'STOP_GAP','OPEN'))
  self.assertEqual(hit_bracket(-1,105,90,111,112,109,False,SCENARIOS['BASE1'])[:3],(111,'STOP_GAP','OPEN'))
 def test_target_touch_is_not_fill(self):
  self.assertIsNone(hit_bracket(1,95,110,100,110,99,False,SCENARIOS['BASE1']))
  self.assertEqual(hit_bracket(1,95,110,100,110.25,99,False,SCENARIOS['BASE1'])[0],110)
  self.assertIsNone(hit_bracket(1,95,110,100,110.25,99,False,SCENARIOS['TP_THROUGH2']))
 def test_target_gap_has_no_improvement(self):
  self.assertEqual(hit_bracket(1,95,110,113,115,112,False,SCENARIOS['BASE1'])[0],110)
 def test_entry_bar_tp_stress_keeps_stop_active(self):
  self.assertIsNone(hit_bracket(1,95,110,100,112,99,True,SCENARIOS['NO_ENTRY_BAR_TP']))
  self.assertEqual(hit_bracket(1,95,110,100,112,94,True,SCENARIOS['NO_ENTRY_BAR_TP'])[1],'STOP')
 def test_opposite_signal_no_reversal(self):
  d=fixture();d.loc[1,['approved_mask','raw_mask','bosS']]=[2,2,True]
  t,c,_,_=simulate(d,2,SCENARIOS['BASE1'],set(),'TEST');self.assertEqual(len(t),1);self.assertEqual(c.iloc[1].disposition,'POSITION_OPEN')
 def test_no_retroactive_gap_exit(self):
  d=fixture();d.loc[2:,'time']+=pd.Timedelta(minutes=5);d.loc[2,['open','high','low','close']]=[90.,91.,89.,90.]
  t,_,_,flags=simulate(d,2,SCENARIOS['BASE1'],set(),'TEST');self.assertEqual(t.iloc[0].exit_reason,'DATA_GAP');self.assertEqual(t.iloc[0].exit_reference_price,90.);self.assertEqual(t.iloc[0].exit_time,d.time.iloc[2].isoformat());self.assertEqual(flags['gap_exits'],1)
 def test_pending_invalid_at_next_open(self):
  d=fixture();d.loc[1,['open','high','low','close']]=[94.,95.,93.,94.]
  t,c,_,_=simulate(d,2,SCENARIOS['BASE1'],set(),'TEST');self.assertEqual(len(t),0);self.assertEqual(c.iloc[0].disposition,'NEXT_OPEN_PAST_STOP')
 def test_daily_flat_and_holiday_blackout(self):
  d=fixture(start='2026-09-22T19:58:00Z',n=34)
  t,_,_,_=simulate(d,2,SCENARIOS['BASE1'],set(),'TEST');self.assertEqual(t.iloc[0].exit_time,'2026-09-22T20:30:00+00:00');self.assertEqual(t.iloc[0].exit_reason,'DAILY_FLAT')
  t,c,_,_=simulate(d,2,SCENARIOS['BASE1'],{'2026-09-22'},'TEST');self.assertEqual(len(t),0);self.assertEqual(c.iloc[0].disposition,'EXEC_WINDOW')
 def test_execution_prefix_no_future_exits(self):
  d=fixture(n=8);d.loc[2,['low','close']]=[94.,96.]
  a=simulate(d,2,SCENARIOS['BASE1'],set(),'TEST')[0];b=simulate(d.iloc[:4],2,SCENARIOS['BASE1'],set(),'TEST')[0]
  pd.testing.assert_frame_equal(a,b)
 def test_frozen_excerpt_matches_prior_events(self):
  root=Path(__file__).resolve().parents[1]
  d=pd.read_csv(root/'data/recon03_excerpt.csv.gz');r=run_original(d)
  old=pd.read_csv(root/'frozen/recon03_diagnostic_bars.csv.gz')
  cols=['raw_mask','approved_mask','score_L','score_S','mask_L','mask_S','block_L','block_S','known']
  pd.testing.assert_frame_equal(r[cols],old[cols]);self.assertEqual(int((r.approved_mask>0).sum()),95)
 def test_pine_approx_prefix_causality(self):
  n=900;t=pd.date_range('2026-09-21',periods=n,freq='min',tz='UTC');p=100+np.sin(np.arange(n)/4)+np.arange(n)*.002
  d=pd.DataFrame({'time':t,'open':p,'high':p+1,'low':p-1,'close':p+.2,'volume':np.where(np.arange(n)%5==0,30,10)})
  r=pine_semantics(run_original(d));s=pine_semantics(run_original(d.iloc[:800]))
  cols=['raw_mask','approved_mask','score_L','score_S','mask_L','mask_S','block_L','block_S','known']
  pd.testing.assert_frame_equal(r.loc[:799,cols].reset_index(drop=True),s[cols])
if __name__=='__main__':unittest.main(verbosity=2)
