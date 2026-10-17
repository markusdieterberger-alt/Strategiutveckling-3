"""Targeted semantic tests, not a Pine compilation claim."""
import unittest
from reference_replay import PriceEngine,Zone,footprint_decision

class CausalityTests(unittest.TestCase):
    def test_pivot_two_bar_delay_and_no_backdate(self):
        e=PriceEngine(); highs=[10,11,15,12,11,16]
        r=[]
        for i,h in enumerate(highs):
            r.append(e.step(i*60,h-1,h,h-2,h-.5,10))
            if i<4: self.assertIsNone(e.hi)
            if i==4: self.assertEqual(e.hi,15); self.assertFalse(r[-1]['bosL'])
        self.assertTrue(r[-1]['bosL'])
    def test_fvg_cannot_score_formation_bar(self):
        e=PriceEngine()
        for b in [(0,9,10,8,9,10),(60,10,12,10,11,10)]: e.step(*b)
        r=e.step(120,12,14,12,13,10)
        self.assertTrue(any(z.kind==1 for z in e.zones)); self.assertFalse(r['fvgL'])
        r=e.step(180,13,14,11,13,10); self.assertTrue(r['fvgL'])
        r=e.step(240,13,14,11,13,10); self.assertFalse(r['fvgL'])
    def test_full_fill_precedes_rejection(self):
        e=PriceEngine(); e.zones=[Zone(10,12,-1,1)]
        r=e.step(0,13,14,10,13,10)
        self.assertFalse(r['fvgL']); self.assertFalse(any(z.kind==1 for z in e.zones))
    def test_sd_close_invalidation_and_touch_consumption(self):
        e=PriceEngine(); e.zones=[Zone(10,12,-1,2)]
        r=e.step(0,13,14,9,13,10); self.assertTrue(r['sdL'])
        self.assertEqual(len(e.zones),1)
        e.step(60,11,12,8,9,10); self.assertFalse(any(z.kind==2 for z in e.zones))
    def test_gap_resets_zone_and_structure(self):
        e=PriceEngine(); e.step(0,10,11,9,10,10); e.hi=11; e.zones=[Zone(8,9,0,2)]
        r=e.step(120,12,13,11,12,10)
        self.assertTrue(r['gap']); self.assertFalse(r['bosL']); self.assertEqual(len(e.zones),0)
    def test_missing_fp_is_not_zero_or_permission(self):
        self.assertEqual(footprint_decision(1,'Gate'),0)
        self.assertEqual(footprint_decision(1,'Quality only'),1)
        self.assertEqual(footprint_decision(1,'Gate',80,20,100,60),1)
        self.assertEqual(footprint_decision(2,'Gate',80,20,100,60),0)
        self.assertEqual(footprint_decision(1,'Gate',80,20,100,99),0)
    def test_prefix_invariance(self):
        bars=[(60*i,100+(i%7),103+(i%7),99+(i%7),102+(i%7),10+i%9) for i in range(80)]
        e=PriceEngine(); full=[e.step(*b) for b in bars]
        for cut in (5,20,50):
            q=PriceEngine(); prefix=[q.step(*b) for b in bars[:cut]]
            self.assertEqual(prefix,full[:cut])
    def test_zone_cap_and_strict_ties(self):
        e=PriceEngine(cap=2)
        for i in range(5): e.add(Zone(i,i+1,i,1))
        self.assertEqual([z.born for z in e.zones],[3,4])
        e=PriceEngine()
        for i in range(10): e.step(i*60,10,11,9,10,10)
        self.assertIsNone(e.hi); self.assertIsNone(e.lo)

if __name__=='__main__': unittest.main(verbosity=2)
