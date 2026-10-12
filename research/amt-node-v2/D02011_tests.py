#!/usr/bin/env python3
"""Independent hand-calculated invariants. These do NOT compile or execute Pine."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

path=Path(__file__).with_name('D02004_research.py')
spec=importlib.util.spec_from_file_location('amt',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def ep():
    return dict(kind='NODE',direction=1,valley=100.,width=2.,probe=None)

def trade_data(rows, gaps=None):
    x=np.array(rows,float)
    n=len(x)
    return dict(x=x,minute=np.arange(n),ts=pd.date_range('2026-01-02 10:00',periods=n,freq='min',tz='UTC'),
                gap=np.array(gaps if gaps is not None else [True]+[False]*(n-1)),
                local={'EU':np.arange(n)+600,'NY':np.arange(n)+600})

def event(**extra):
    return dict(dict(i=0,side=1,stop=98.,order_target=104.,planned_risk=2.25,cohort='EU'),**extra)

class ProfileTests(unittest.TestCase):
    def test_mass_is_preserved_HL(self):
        x=np.tile([100,105,99,102,120.],(150,1))
        p=m.profile(x)
        self.assertAlmostEqual(p['raw'].sum(),18000)
        np.testing.assert_allclose(p['raw'],np.repeat(18000/7,7))
    def test_close_only_uses_close_bin(self):
        x=np.tile([100,105,99,102,120.],(150,1))
        p=m.profile(x,'CLOSE')
        self.assertEqual(np.count_nonzero(p['raw']),1)
        self.assertEqual(p['raw'][3],18000)
    def test_tpo_is_time_not_volume(self):
        x=np.tile([100,105,99,102,120.],(150,1))
        p=m.profile(x,'TPO')
        np.testing.assert_allclose(p['raw'],150)
    def test_flat_has_no_pair(self):
        p=m.profile(np.tile([100,100,100,100,10.],(150,1)))
        self.assertEqual(p['pairs'],[])
        self.assertEqual(p['poc'],100.5)
    def test_grid_width_half_up(self):
        x=np.tile([100,172,100,120,10.],(150,1))
        self.assertEqual(m.profile(x)['width'],1.25) # 288/64=4.5 ticks ->5.
    def test_known_two_peak_corridor(self):
        vals=[99.,122.]+[120.5]*70+[110.5]*8+[100.5]*70
        x=np.array([[p,p,p,p,0 if p in (99,122) else 10 if p in (100.5,120.5) else 1] for p in vals])
        p=m.profile(x)
        self.assertEqual(len(p['pairs']),1)
        self.assertEqual(p['best']['direction'],1)
        self.assertEqual(p['best']['origin'],100.5)
        self.assertEqual(p['best']['destination'],120.5)
    def test_future_mutation_does_not_change_profile(self):
        rng=np.random.default_rng(13)
        c=np.round(rng.uniform(100,120,300)*4)/4
        x=np.column_stack([c,c+1,c-1,c,np.ones(300)])
        before=m.profile(x[:150])
        x[150:,:4]+=1000
        after=m.profile(x[:150])
        np.testing.assert_array_equal(before['smooth'],after['smooth'])

class StateTests(unittest.TestCase):
    def test_A_needs_three_confirmed_closes(self):
        e=ep()
        self.assertIsNone(m.step_episode(e,102,103,101,0))
        self.assertIsNone(m.step_episode(e,102,103,101,5))
        self.assertEqual(m.step_episode(e,102,103,101,10),('A',1))
    def test_B_return_before_acceptance(self):
        e=ep();m.step_episode(e,102,105,100,0)
        self.assertEqual(m.step_episode(e,98,103,97,5),('B',-1))
        self.assertEqual(e['probe_high'],105)
        self.assertEqual(e['probe_low'],97)
    def test_inside_breaks_consecutive_acceptance(self):
        e=ep();m.step_episode(e,102,103,101,0)
        m.step_episode(e,100,102,99,5)
        self.assertIsNone(m.step_episode(e,102,103,101,10))
        self.assertIsNone(m.step_episode(e,102,103,101,15))
        self.assertTrue(e['consumed'])
    def test_return_on_third_bar_is_allowed(self):
        e=ep();m.step_episode(e,102,103,101,0)
        m.step_episode(e,100,102,99,5);m.step_episode(e,100,102,99,10)
        self.assertEqual(m.step_episode(e,98,102,97,15),('B',-1))
    def test_boundary_equality_is_not_acceptance(self):
        e=ep();self.assertIsNone(m.step_episode(e,101,102,100,0))
        self.assertIsNone(e['probe'])
    def test_short_symmetry(self):
        e=ep();e['direction']=-1
        m.step_episode(e,98,99,97,0);m.step_episode(e,98,99,97,5)
        self.assertEqual(m.step_episode(e,98,99,97,10),('A',-1))

class FillTests(unittest.TestCase):
    def test_stop_gap_is_worse_open(self):
        self.assertEqual(m.fill_bar(90,102,89,1,98,104),('STOP_GAP',90,False))
    def test_double_touch_stop_first(self):
        self.assertEqual(m.fill_bar(100,106,96,1,98,104),('STOP',98,True))
    def test_target_gap_precedes_later_stop(self):
        self.assertEqual(m.fill_bar(105,106,96,1,98,104),('TP_GAP_CAPPED',104,False))
    def test_short_gap_and_tie(self):
        self.assertEqual(m.fill_bar(110,112,90,-1,102,96),('STOP_GAP',110,False))
        self.assertEqual(m.fill_bar(100,104,95,-1,102,96),('STOP',102,True))
    def test_signal_bar_cannot_fill(self):
        d=trade_data([[100,150,50,100,1],[100,101,99,100,1],[101,105,100,104,1]])
        t=m.simulate_trade(d,event())
        self.assertEqual(t['entry_i'],1);self.assertEqual(t['exit_i'],2)
        self.assertEqual(t['net_points'],3.)
    def test_entry_minute_protected(self):
        d=trade_data([[100,100,100,100,1],[100,105,97,100,1]])
        t=m.simulate_trade(d,event())
        self.assertEqual(t['net_points'],-3.)
        self.assertTrue(t['ambiguous'])
    def test_unknown_entry_gap_cannot_be_skipped(self):
        d=trade_data([[100,100,100,100,1],[90,105,89,100,1]],[True,True])
        t=m.simulate_trade(d,event())
        self.assertTrue(t['gap_flag']);self.assertEqual(t['net_points'],-1.)
    def test_cutoff_market_exit_next_open(self):
        d=trade_data([[100,100,100,100,1],[100,101,99,100,1],[102,105,99,102,1]])
        d['local']['EU'][1]=720
        t=m.simulate_trade(d,event())
        self.assertEqual(t['exit_reason'],'CUTOFF');self.assertEqual(t['net_points'],1.)
    def test_adverse_gap_overrides_market_time_exit(self):
        d=trade_data([[100,100,100,100,1],[100,101,99,100,1],[90,105,89,100,1]])
        d['local']['EU'][1]=720
        t=m.simulate_trade(d,event())
        self.assertEqual(t['exit_reason'],'STOP_GAP');self.assertEqual(t['net_points'],-11.)

class OutcomeTests(unittest.TestCase):
    def test_mirror_same_minute_adverse(self):
        self.assertEqual(m.first_touch(np.array([[100,110,90,100,1]]),1,100,5,30),(-1,1,True))
    def test_open_resolves_mirror_order(self):
        self.assertEqual(m.first_touch(np.array([[106,110,90,100,1]]),1,100,5,30),(1,1,False))
    def test_unhit_is_zero(self):
        self.assertEqual(m.first_touch(np.array([[100,101,99,100,1]]),1,100,5,30),(0,1,False))
    def test_bootstrap_is_deterministic_and_day_blocked(self):
        d=pd.DataFrame({'trade_date':['a','a','b','b'],'v':[1,1,-1,-1]})
        a=m.bootstrap_day(d,'v',100)
        self.assertEqual(a,m.bootstrap_day(d,'v',100));self.assertEqual(a,[-1.,1.])

if __name__=='__main__':
    unittest.main(verbosity=2)
