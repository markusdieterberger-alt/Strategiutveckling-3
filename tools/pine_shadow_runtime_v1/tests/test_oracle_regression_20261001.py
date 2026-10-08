"""TradingView MNQ1! oracle observations, 2026-10-01.

These tests use controlled synthetic OHLC bars, NOT the original MNQ1! bars.
Passing these tests demonstrates rule coverage, not TV price/data parity.
Observed TV oracle:
v3 A/B normal/immediate closes, C/D same-bar brackets;
v4.2 I same-ID mutation, J pre-attached bracket, K same-bar target;
v4.4 Q/R verified buy/sell limits (1 tick).
"""
from pine_shadow import Bar, PineShadowEngine, RuntimeConfig, Side


def b(i, o, h, l, c):
    return Bar(i, i * 60000, o, h, l, c, 100)


def run(strategy, bars, **kwargs):
    cfg = RuntimeConfig(mintick=0.25, slippage_ticks=1, **kwargs)
    return PineShadowEngine(cfg, strategy).run(bars)


class NormalClose:
    def on_bar_close(self, e, bar):
        if bar.index == 0:
            e.entry("A", Side.BUY, 1)
        if bar.index == 1:
            e.close("A")


def test_oracle_a_normal_close_next_open():
    s = run(NormalClose(), [b(0,100,100,100,100),b(1,101,101,101,101),b(2,102,102,102,102)])
    assert len(s.closed_trades) == 1
    assert s.closed_trades[0].entry_price == 101.25
    assert s.closed_trades[0].exit_price == 101.75


class Mutate:
    def on_bar_close(self, e, bar):
        if bar.index == 0:
            e.entry("I", Side.BUY, 1, limit=90)
        if bar.index == 1:
            e.entry("I", Side.BUY, 1, limit=98)


def test_oracle_i_same_id_pending_mutation():
    s = run(Mutate(), [b(0,100,101,99,100), b(1,100,101,99,100), b(2,100,101,97,99)])
    assert s.position_size == 1
    assert s.position_avg_price == 98
    assert len([f for f in s.fills if f.role.value == "entry"]) == 1


class PreAttached:
    def on_bar_close(self, e, bar):
        if bar.index == 0:
            e.entry("J", Side.BUY, 1, limit=98)
            e.exit("J-X", "J", stop=96, limit=100)


def test_oracle_j_bracket_before_fill_same_bar():
    s = run(PreAttached(), [b(0,100,101,99,100), b(1,100,101,97,99)])
    assert len(s.closed_trades) == 1
    assert s.closed_trades[0].entry_id == "J"
    assert s.closed_trades[0].exit_id == "J-X"
    assert s.closed_trades[0].entry_bar == s.closed_trades[0].exit_bar


class PathTarget:
    def on_bar_close(self, e, bar):
        if bar.index == 0:
            e.entry("K", Side.BUY, 1, limit=99.75)
            e.exit("K-X", "K", stop=99.25, limit=100.25)


def test_oracle_k_target_wins_after_limit_entry():
    # O-L-H-C; limit entry on down leg, target on subsequent up leg.
    s = run(PathTarget(), [b(0,100,100,100,100), b(1,100,101,99,100)])
    assert len(s.closed_trades) == 1
    assert s.closed_trades[0].exit_price == 100.25


class VerifiedBuy:
    def on_bar_close(self, e, bar):
        if bar.index == 0:
            e.entry("Q", Side.BUY, 1, limit=98)


class VerifiedSell:
    def on_bar_close(self, e, bar):
        if bar.index == 0:
            e.entry("R", Side.SELL, 1, limit=102)


def test_oracle_q_limit_requires_one_tick_beyond():
    s = run(VerifiedBuy(), [b(0,100,100,100,100), b(1,100,101,98,100)], backtest_fill_limits_assumption_ticks=1)
    assert s.position_size == 0
    s = run(VerifiedBuy(), [b(0,100,100,100,100), b(1,100,101,97.75,100)], backtest_fill_limits_assumption_ticks=1)
    assert s.position_avg_price == 98


def test_oracle_r_limit_requires_one_tick_beyond():
    s = run(VerifiedSell(), [b(0,100,100,100,100), b(1,100,102,99,100)], backtest_fill_limits_assumption_ticks=1)
    assert s.position_size == 0
    s = run(VerifiedSell(), [b(0,100,100,100,100), b(1,100,102.25,99,100)], backtest_fill_limits_assumption_ticks=1)
    assert s.position_avg_price == 102


class Cancel:
    def on_bar_close(self, e, bar):
        if bar.index == 0:
            e.entry("H", Side.BUY, 1, limit=90)
        if bar.index == 1:
            e.cancel("H")


def test_oracle_h_cancel_prevents_later_touch():
    s = run(Cancel(), [b(0,100,101,99,100), b(1,100,101,95,100), b(2,100,101,85,90)])
    assert s.position_size == 0
    assert not s.fills
