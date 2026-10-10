"""Static identity + synthetic execution contracts; never Pine runtime tests."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import math
import unittest

from eaa.ct_audit import audit, balanced, executable_text
from eaa.ct_contract import Bar, MODELS, Slot, audit_exposure, levels, session_open, stop_first_exit, stress_net


class CTSourceTests(unittest.TestCase):
    def test_all_source_contracts(self):
        evidence = audit()
        for name, passed in evidence['checks'].items():
            with self.subTest(check=name):
                self.assertTrue(passed, name)
        self.assertFalse(evidence['pine_compiled'])
        self.assertFalse(evidence['signal_parity_on_market_data_verified'])

    def test_scanner_ignores_comments_strings_and_escapes(self):
        self.assertTrue(balanced('x = f("[ \\\"", 1) // [\n'))
        self.assertNotIn('open[-1]', executable_text('// open[-1]\nx="open[-1]"'))
        self.assertFalse(balanced('f([1))'))
        with self.assertRaises(ValueError):
            balanced('f("unclosed)')


class CTLevelTests(unittest.TestCase):
    def test_long_original_minimum_stop_and_outward_tick(self):
        self.assertEqual(levels(1, 100, 99.9, 104.01, 1.1), (98.75, 104.25))

    def test_short_original_minimum_stop_and_outward_tick(self):
        self.assertEqual(levels(-1, 100, 100.1, 95.99, 1.1), (101.25, 95.75))

    def test_existing_wider_stop_not_tightened(self):
        self.assertEqual(levels(1, 100, 90, 110, 1), (90, 110))
        self.assertEqual(levels(-1, 100, 110, 90, 1), (110, 90))

    def test_negative_prices_round_correctly(self):
        self.assertEqual(levels(1, -10, -11.1, -9.1, .5), (-11.25, -9))
        self.assertEqual(levels(-1, -10, -8.9, -11.1, .5), (-8.75, -11.25))

    def test_bad_inputs_rejected(self):
        for values in ((0,100,90,110,1), (1,100,90,99,1), (-1,100,110,101,1), (1,100,90,math.nan,1), (1,100,90,110,0)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                levels(*values)

    def test_invalid_ohlc_rejected(self):
        for values in ((1,100,99,95,98), (1,100,105,95,106), (1,100,105,math.nan,101)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                Bar(*values)


class CTExitTests(unittest.TestCase):
    def test_long_both_levels_stop_first(self):
        self.assertEqual(stop_first_exit(1,95,105,Bar(1,100,106,94,101)), ('SL',94.75,True))

    def test_short_both_levels_stop_first(self):
        self.assertEqual(stop_first_exit(-1,105,95,Bar(1,100,106,94,99)), ('SL',105.25,True))

    def test_long_adverse_gap(self):
        self.assertEqual(stop_first_exit(1,95,105,Bar(1,90,94,89,92)), ('SL',89.75,False))

    def test_short_adverse_gap(self):
        self.assertEqual(stop_first_exit(-1,105,95,Bar(1,110,111,106,109)), ('SL',110.25,False))

    def test_target_gap_receives_no_beneficial_price(self):
        self.assertEqual(stop_first_exit(1,95,105,Bar(1,110,111,106,109)), ('TP',105,False))
        self.assertEqual(stop_first_exit(-1,105,95,Bar(1,90,94,89,92)), ('TP',95,False))

    def test_neither_level_no_exit(self):
        self.assertIsNone(stop_first_exit(1,95,105,Bar(1,100,104,96,101)))

    def test_exact_touch_in_adverse_oracle(self):
        self.assertEqual(stop_first_exit(1,95,105,Bar(1,100,104,95,101))[0], 'SL')
        # Native limit orders additionally require the configured 1-tick penetration.
        self.assertEqual(stop_first_exit(-1,105,95,Bar(1,100,104,95,99))[0], 'TP')

    def test_stress_reprices_winner_with_fees_and_qty(self):
        self.assertEqual(stress_net(1,100,105,94.75,qty=2,fees=2), -23)
        self.assertEqual(stress_net(-1,100,95,105.25,qty=2,fees=2), -23)

    def test_stress_never_masks_worse_actual_loss(self):
        self.assertEqual(stress_net(1,100,90,94.75), -21)
        self.assertEqual(stress_net(-1,100,110,105.25), -21)

    def test_non_ambiguous_stress_equals_native(self):
        self.assertEqual(stress_net(1,100,105,None), 9)

    def test_invalid_stress_quantity_rejected(self):
        with self.assertRaises(ValueError):
            stress_net(1,100,105,95,qty=1.5)


class CTSlotTests(unittest.TestCase):
    def test_all_six_models_both_directions_survive_dispatch(self):
        for side in (-1,1):
            for model in MODELS:
                with self.subTest(side=side, model=model):
                    slot=Slot()
                    candidate=(side,model,100-side*5,100+side*5)
                    self.assertEqual(slot.submit(0,[candidate]),candidate)
                    slot.next_bar(Bar(1,100,101,99,100))
                    self.assertEqual(slot.active[:2],(side,model))

    def test_priority_is_source_order(self):
        slot=Slot()
        self.assertEqual(slot.submit(0,[(1,m,95,105) for m in reversed(MODELS)])[1], 'FADE')
        slot=Slot()
        self.assertEqual(slot.submit(0,[(1,m,95,105) for m in ('VRZ','AGG','DIV')])[1], 'DIV')

    def test_opposite_candidates_rejected(self):
        slot=Slot()
        self.assertIsNone(slot.submit(0,[(1,'FADE',95,105),(-1,'DIV',105,95)]))

    def test_no_signal_bar_fill(self):
        slot=Slot()
        slot.submit(0,[(1,'FADE',95,105)])
        self.assertIsNone(slot.next_bar(Bar(0,100,106,94,100)))
        self.assertIsNotNone(slot.pending)

    def test_next_bar_entry_and_same_bar_stop(self):
        slot=Slot()
        slot.submit(0,[(1,'TRAP',95,105)])
        self.assertEqual(slot.next_bar(Bar(1,100,106,94,100)),('SL',94.75,True))

    def test_busy_blocks_reversal_and_repricing(self):
        slot=Slot()
        slot.submit(0,[(1,'AGG',95,105)])
        self.assertIsNone(slot.submit(0,[(-1,'TRAP',105,95)]))
        slot.next_bar(Bar(1,100,101,99,100))
        self.assertIsNone(slot.submit(1,[(1,'DIV',94,106)]))
        self.assertEqual(slot.active[2:4],(95,105))

    def test_no_reentry_on_exit_bar(self):
        slot=Slot()
        slot.submit(0,[(1,'FADE',95,105)])
        slot.next_bar(Bar(1,100,106,94,100))
        self.assertIsNone(slot.submit(1,[(1,'VRZ',95,105)]))
        self.assertIsNotNone(slot.submit(2,[(1,'VRZ',95,105)]))

    def test_cancel_pending_prevents_later_fill(self):
        slot=Slot()
        slot.submit(0,[(1,'FADE',95,105)])
        slot.cancel()
        self.assertIsNone(slot.next_bar(Bar(1,100,106,94,100)))
        self.assertIsNone(slot.active)

    def test_session_close_for_open_position(self):
        slot=Slot()
        slot.submit(0,[(1,'ABSORB',95,105)])
        self.assertEqual(slot.next_bar(Bar(1,100,102,98,101),force_flat=True),('SESSION',101,False))

    def test_data_and_session_blocks(self):
        for allowed,data in ((False,True),(True,False),(False,False)):
            with self.subTest(allowed=allowed,data=data):
                self.assertIsNone(Slot().submit(0,[(1,'FADE',95,105)],allowed,data))


class CTAuditTimingTests(unittest.TestCase):
    def test_rejected_unfilled_order_not_exposure(self):
        self.assertFalse(audit_exposure(1,2,1))

    def test_delayed_immediate_close_not_following_bar(self):
        self.assertFalse(audit_exposure(1,4,1,closed_exit_bar=3))

    def test_open_position_and_same_bar_roundtrip_audited(self):
        self.assertTrue(audit_exposure(1,2,1,position_size=1))
        self.assertTrue(audit_exposure(1,2,-1,closed_exit_bar=2))

    def test_signal_bar_never_audited(self):
        self.assertFalse(audit_exposure(1,1,1,position_size=1))


class CTSessionTests(unittest.TestCase):
    def local(self, date, clock):
        return datetime.fromisoformat(date+'T'+clock).replace(tzinfo=ZoneInfo('America/New_York'))

    def test_regular_cutoff_entry_buffer_and_reopen(self):
        day='2026-10-08'
        self.assertTrue(session_open(self.local(day,'16:42'),1003))
        self.assertFalse(session_open(self.local(day,'16:43'),1003))
        self.assertTrue(session_open(self.local(day,'16:43'),1004))
        self.assertFalse(session_open(self.local(day,'16:44'),1004))
        self.assertFalse(session_open(self.local(day,'17:59')))
        self.assertTrue(session_open(self.local(day,'18:00')))

    def test_weekend_closure(self):
        self.assertFalse(session_open(self.local('2026-10-09','18:00')))
        self.assertFalse(session_open(self.local('2026-10-10','12:00')))
        self.assertFalse(session_open(self.local('2026-10-11','17:59')))
        self.assertTrue(session_open(self.local('2026-10-11','18:00')))
        self.assertTrue(session_open(self.local('2026-10-12','00:00')))

    def test_dst_uses_new_york_not_fixed_utc_offset(self):
        for utc_hour,day in ((20,'2026-07-08'),(21,'2026-12-08')):
            stamp=datetime.fromisoformat(day+f'T{utc_hour}:44').replace(tzinfo=timezone.utc)
            self.assertFalse(session_open(stamp))
            self.assertTrue(session_open(stamp.replace(minute=43)))

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            session_open(datetime(2026,10,8,12))


if __name__ == '__main__':
    unittest.main()
