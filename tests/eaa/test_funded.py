from dataclasses import replace
from datetime import date, datetime, timedelta
import math
import unittest
from zoneinfo import ZoneInfo

from eaa.funded import Rules, Sample, Trade, allowed, bootstrap, contracts_for, rolling, session_day, simulate, summarize, validate_trades


ZONE = ZoneInfo("America/New_York")


def trade(day="2026-01-05", profit=0, *, ident="1", hour=10, samples=(), stop=None):
    entry = datetime.fromisoformat(f"{day}T{hour:02}:00:00").replace(tzinfo=ZONE)
    return Trade(ident, entry, entry + timedelta(minutes=5), 1, 20000, 20000 + profit / 2, stop_points=stop, samples=tuple(Sample(entry + timedelta(minutes=i + 1), v / 2) for i, v in enumerate(samples)), quality="SYNTHETIC_CONTROL" if samples else "CLOSED_TRADES_ONLY")


def run_days(items, rules=None):
    return simulate([(date.fromisoformat(d), rows) for d, rows in items], rules or Rules(commission_rt=0))


class FundedTests(unittest.TestCase):
    def test_intraday_winner_can_fail(self):
        t = trade(profit=100, samples=(-1001,))
        r = run_days([("2026-01-05", [t])], Rules(commission_rt=0, daily_loss=None))
        self.assertEqual((r.status, r.failure, r.net), ("FAIL", "MLL", -1001))

    def test_closed_only_never_certified(self):
        r = run_days([("2026-01-05", [trade(profit=100)])])
        self.assertTrue(r.approximate)
        self.assertFalse(r.rules_verified)
        self.assertIn("CLOSED_TRADES_ONLY", r.quality)

    def test_eod_trail_does_not_follow_open_high(self):
        r = run_days([("2026-01-05", [trade(profit=100, samples=(900, -200))])], Rules(commission_rt=0, daily_loss=None, daily_profit=None))
        self.assertEqual((r.status, r.net, r.floor), ("ALIVE", 100, -900))

    def test_eod_high_water_never_decreases(self):
        r = run_days([("2026-01-05", [trade(profit=400)]), ("2026-01-06", [trade("2026-01-06", -200, ident="2")])])
        self.assertEqual(r.floor, -600)

    def test_previous_day_floor_applies_intraday(self):
        r = run_days([("2026-01-05", [trade(profit=500)]), ("2026-01-06", [trade("2026-01-06", 50, ident="2", samples=(-1000,))])], Rules(commission_rt=0, daily_loss=None))
        self.assertEqual((r.status, r.failure), ("FAIL", "MLL"))

    def test_lock_at_initial_plus_100(self):
        r = run_days([("2026-01-05", [trade(profit=1200)])], Rules(commission_rt=0, daily_loss=None, daily_profit=None))
        self.assertEqual(r.floor, 100)

    def test_touch_mll_is_fail(self):
        r = run_days([("2026-01-05", [trade(profit=-1000)])], Rules(commission_rt=0, daily_loss=None))
        self.assertEqual(r.failure, "MLL")

    def test_dll_is_day_lock_not_account_fail(self):
        r = run_days([("2026-01-05", [trade(profit=200, samples=(-600,)), trade(profit=300, ident="2", hour=11)]), ("2026-01-06", [trade("2026-01-06", 100, ident="3")])])
        self.assertEqual((r.status, r.net), ("ALIVE", -500))
        self.assertEqual([e["event"] for e in r.events], ["DLL", "SKIP_DAY_LOCK", "EOD", "EXIT", "EOD"])

    def test_dll_hard_fail_is_explicit_profile(self):
        r = run_days([("2026-01-05", [trade(profit=-600)])], Rules(commission_rt=0, dll_action="fail"))
        self.assertEqual(r.failure, "DLL_PROJECT_HARD_FAIL")

    def test_gap_through_both_limits_is_mll(self):
        r = run_days([("2026-01-05", [trade(profit=100, samples=(-1100,))])])
        self.assertEqual((r.failure, r.net), ("MLL", -1100))

    def test_exit_fee_can_cause_breach(self):
        r = run_days([("2026-01-05", [trade(profit=-999)])], Rules(commission_rt=1, daily_loss=None))
        self.assertEqual(r.failure, "MLL")

    def test_profit_liquidation_not_clipped(self):
        r = run_days([("2026-01-05", [trade(profit=10, samples=(600,)), trade(profit=100, ident="2", hour=11)]), ("2026-01-06", [])])
        self.assertEqual(r.net, 600)
        self.assertEqual(r.events[0]["event"], "PROFIT_STOP")

    def test_realized_profit_stop_does_not_use_open_high(self):
        r = run_days([("2026-01-05", [trade(profit=20, samples=(600,))])], Rules(commission_rt=0, profit_action="block_new"))
        self.assertEqual(r.net, 20)

    def test_consistency_blocks_one_big_day(self):
        r = run_days([("2026-01-05", [trade(profit=1250)])], Rules(commission_rt=0, daily_profit=None))
        self.assertEqual(r.status, "ALIVE")

    def test_consistency_denominator_includes_losses(self):
        r = run_days([("2026-01-05", [trade(profit=700)]), ("2026-01-06", [trade("2026-01-06", 700, ident="2")]), ("2026-01-07", [trade("2026-01-07", -200, ident="3")])], Rules(commission_rt=0, target=1600, daily_profit=None))
        self.assertEqual((r.status, r.net), ("ALIVE", 1200))

    def test_pass_three_balanced_days(self):
        r = run_days([(f"2026-01-0{d}", [trade(f"2026-01-0{d}", 450, ident=str(d))]) for d in (5, 6, 7)])
        self.assertEqual((r.status, r.days, r.net), ("PASS", 3, 1350))

    def test_integer_sizing_rounds_down(self):
        self.assertEqual(contracts_for(trade(stop=10), Rules(), 20, 100), 4)

    def test_size_below_one_skips_not_rounds_up(self):
        t = trade(profit=200, stop=100)
        r = simulate([(date(2026, 1, 5), [t])], Rules(), 20, 100)
        self.assertEqual(r.events[0]["event"], "SKIP_SIZE_BELOW_ONE")
        self.assertEqual(r.net, 0)

    def test_sizing_requires_entry_stop(self):
        with self.assertRaises(ValueError):
            contracts_for(trade(), Rules(), 2, 100)

    def test_max_contract_limit(self):
        with self.assertRaises(ValueError):
            simulate([(date(2026, 1, 5), [])], Rules(), 21)

    def test_full_round_trip_cost(self):
        rules = Rules(commission_rt=1, additional_slippage_ticks_side=1)
        r = simulate([(date(2026, 1, 5), [trade(profit=10)])], rules, 3)
        self.assertEqual(r.net, 24)

    def test_short_price_direction(self):
        t = replace(trade(profit=-50), side=-1)
        self.assertEqual(t.points * 2, 50)

    def test_mae_proxy_can_find_breach(self):
        t = replace(trade(profit=100), mae_points=510)
        r = run_days([("2026-01-05", [t])])
        self.assertEqual(r.failure, "MLL")
        self.assertIn("MAE_ADVERSE_FIRST_UNKNOWN_TIME", r.quality)

    def test_overlaps_rejected(self):
        with self.assertRaises(ValueError):
            validate_trades([trade(), trade(ident="2")], Rules())

    def test_overnight_rejected(self):
        t = trade()
        with self.assertRaises(ValueError):
            validate_trades([replace(t, exit=t.exit + timedelta(days=1))], Rules())

    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            validate_trades([replace(trade(), entry_price=math.nan)], Rules())

    def test_offtick_rejected(self):
        with self.assertRaises(ValueError):
            validate_trades([replace(trade(), entry_price=20000.13)], Rules())

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):
            validate_trades([trade(), trade(hour=11)], Rules())

    def test_invalid_sample_order_rejected(self):
        t = trade()
        with self.assertRaises(ValueError):
            validate_trades([replace(t, samples=(Sample(t.exit, 0), Sample(t.entry, 0)))], Rules())

    def test_sunday_reopen_is_monday_session(self):
        at = datetime(2026, 1, 4, 18, tzinfo=ZONE)
        self.assertEqual(session_day(at, Rules()), date(2026, 1, 5))
        self.assertTrue(allowed(at, Rules()))

    def test_friday_evening_and_saturday_blocked(self):
        for at in (datetime(2026, 1, 9, 18, tzinfo=ZONE), datetime(2026, 1, 10, 10, tzinfo=ZONE)):
            self.assertFalse(allowed(at, Rules()))

    def test_cutoff_entry_blocked_exit_allowed(self):
        at = datetime(2026, 1, 5, 16, 45, tzinfo=ZONE)
        self.assertFalse(allowed(at, Rules()))
        self.assertTrue(allowed(at, Rules(), exit_event=True))

    def test_calendar_counts_zero_trade_days(self):
        calendar = [date(2026, 1, 5) + timedelta(days=i) for i in range(5)]
        results = rolling([trade(profit=100)], calendar, Rules(), horizon=5)
        self.assertEqual(results[0].days, 5)
        self.assertEqual(summarize(results)["alive_pct"], 100)

    def test_no_partial_rolling_windows(self):
        calendar = [date(2026, 1, 5) + timedelta(days=i) for i in range(5)]
        self.assertEqual(len(rolling([], calendar, Rules(), horizon=3)), 3)

    def test_calendar_missing_trade_fails(self):
        with self.assertRaises(ValueError):
            rolling([trade()], [date(2026, 1, 6)], Rules(), horizon=1)

    def test_insufficient_bootstrap_fails(self):
        with self.assertRaises(ValueError):
            bootstrap([trade()], [date(2026, 1, 5)], Rules())

    def test_bootstrap_seed_reproducible(self):
        days, cursor = [], date(2026, 1, 5)
        while len(days) < 40:
            if cursor.weekday() < 5:
                days.append(cursor)
            cursor += timedelta(days=1)
        trades = [trade(str(d), 100 if i % 3 else -150, ident=str(i)) for i, d in enumerate(days)]
        a = bootstrap(trades, days, Rules(), iterations=20)
        b = bootstrap(trades, days, Rules(), iterations=20)
        self.assertEqual(a, b)

    def test_configuration_rejects_negative_costs(self):
        with self.assertRaises(ValueError):
            Rules(commission_rt=-1)


if __name__ == "__main__":
    unittest.main()
