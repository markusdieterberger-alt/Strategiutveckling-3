import unittest
import pandas as pd
import numpy as np
from reverse_adapter import execution_view,simulate,source,execution,ROOT,BASE
from test_execution import fixture

class ReverseTests(unittest.TestCase):
 def run_model(self,d,reverse=True,rr=2):return simulate(d,rr,execution.SCENARIOS['BASE1'],set(),'TEST',reverse)
 def test_long_becomes_short_with_new_bracket_and_source_score(self):
  d=fixture(n=2);d.loc[0,['score_L','score_S','mask_L','mask_S','fvgL']]=[7,1,127,1,True]
  d.loc[1,['open','high','low','close','swing_high_close']]=[102.,104.,101.,103.,120.]
  a=self.run_model(d,False)[0].iloc[0];b=self.run_model(d)[0].iloc[0]
  self.assertEqual((b.direction,b.source_direction),(-1,1));self.assertEqual(b.score,7);self.assertEqual(b.signal_type,'BOS+FVG');self.assertEqual(b.signal_factor_mask,127)
  self.assertEqual(b.stop,105.25);self.assertEqual(b.entry_fill,101.75);self.assertEqual(b.target,94.75)
  self.assertNotEqual(b.stop,a.stop);self.assertNotEqual(b.target,a.target);self.assertEqual(b.entry_time,d.time.iloc[1].isoformat())
 def test_short_becomes_long_with_new_bracket(self):
  d=fixture(n=2);d.loc[0,['approved_mask','bosL','bosS','score_L','score_S']]=[2,False,True,2,8]
  t=self.run_model(d)[0].iloc[0]
  self.assertEqual((t.direction,t.source_direction,t.score),(1,-1,8));self.assertEqual(t.stop,94.75);self.assertEqual(t.entry_fill,100.25);self.assertEqual(t.target,111.25)
 def test_wrong_side_reverse_stop_is_rejected(self):
  d=fixture(n=2);d.loc[0,'swing_high_close']=99.
  t,c,_,_=self.run_model(d);self.assertEqual(len(t),0);self.assertEqual(c.iloc[0].disposition,'SL_INVALID_AT_SIGNAL')
  self.assertEqual(len(self.run_model(d,False)[0]),1)
 def test_open_past_new_stop_rejects_without_old_stop_fallback(self):
  d=fixture(n=2);d.loc[1,['open','high','low','close']]=[106.,107.,105.,106.]
  t,c,_,_=self.run_model(d);self.assertEqual(len(t),0);self.assertEqual(c.iloc[0].disposition,'NEXT_OPEN_PAST_STOP')
 def test_only_approval_inverted_and_prices_swings_regimes_unchanged(self):
  d=fixture();d.loc[1,['raw_mask','approved_mask']]=[2,0];d.loc[2,'approved_mask']=2;old=d.copy(deep=True)
  v=execution_view(d,True);pd.testing.assert_frame_equal(d,old)
  self.assertEqual(v.approved_mask.tolist(),[2,0,1,0,0])
  for col in ['time','open','high','low','close','raw_mask','swing_low_close','swing_high_close','ema_regime','chop_regime','score_session']:pd.testing.assert_series_equal(v[col],d[col])
 def test_all_approved_candidates_survive_transport_while_position_blocks(self):
  d=fixture(n=6);d.loc[1,['approved_mask','raw_mask','bosS']]=[2,2,True]
  a=self.run_model(d,False)[1];b=self.run_model(d)[1]
  self.assertEqual(a.signal_time.tolist(),b.signal_time.tolist());self.assertEqual(a.direction.tolist(),(-b.direction).tolist());self.assertEqual(b.iloc[1].disposition,'POSITION_OPEN')
 def test_target_recomputed_for_every_rr_and_slippage(self):
  for s in execution.SCENARIOS.values():
   for rr in [1.5,2.,3.]:
    d=fixture(n=2);x=simulate(d,rr,s,set(),'TEST',True)[0].iloc[0]
    risk=(x.stop-x.entry_fill);expected=np.floor((x.entry_fill-rr*risk)/.25+1e-10)*.25
    self.assertEqual(x.target,expected);self.assertEqual(x.risk_usd,risk*2);self.assertLess(x.target,x.entry_fill);self.assertGreater(x.stop,x.entry_fill)
 def test_reverse_prefix_execution_and_signal_transport_causal(self):
  d=fixture(n=8);d.loc[2,['high','close']]=[106.,104.]
  a=self.run_model(d)[0];b=self.run_model(d.iloc[:4])[0];pd.testing.assert_frame_equal(a,b)
  e=pd.read_csv(BASE/'data/recon03_excerpt.csv.gz').iloc[:1500]
  full=execution_view(source.run_original(e),True);prefix=execution_view(source.run_original(e.iloc[:1200]),True)
  pd.testing.assert_frame_equal(full.iloc[:1200].reset_index(drop=True),prefix,check_dtype=False)
 def test_ambiguous_approved_mask_cannot_silently_select_direction(self):
  d=fixture();d.loc[0,'approved_mask']=3
  with self.assertRaises(AssertionError):execution_view(d,True)
if __name__=='__main__':unittest.main(verbosity=2)
