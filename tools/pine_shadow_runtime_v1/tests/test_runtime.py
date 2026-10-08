from pine_shadow import Bar, RuntimeConfig, PineShadowEngine, Side


def B(i, o, h, l, c):
    return Bar(i, i * 60_000, o, h, l, c, 100)


class MarketNextOpen:
    def on_bar_close(self, e, b):
        if b.index == 0:
            e.entry("L", Side.BUY, 1)


def test_market_next_open_and_slippage():
    e = PineShadowEngine(
        RuntimeConfig(mintick=.25, slippage_ticks=1),
        MarketNextOpen(),
    )
    s = e.run([B(0,100,101,99,100), B(1,102,103,101,102)])
    assert s.position_size == 1
    assert s.position_avg_price == 102.25


class BuyLimitTouch:
    def on_bar_close(self, e, b):
        if b.index == 0:
            e.entry("L", Side.BUY, 1, limit=98)


def test_buy_limit_intrabar_touch_at_limit():
    e = PineShadowEngine(RuntimeConfig(slippage_ticks=1), BuyLimitTouch())
    s = e.run([B(0,100,101,99,100), B(1,100,101,97,99)])
    assert s.position_avg_price == 98


class BuyLimitGapBetter:
    def on_bar_close(self, e, b):
        if b.index == 0:
            e.entry("L", Side.BUY, 1, limit=98)


def test_buy_limit_gap_better_fills_open():
    e = PineShadowEngine(RuntimeConfig(), BuyLimitGapBetter())
    s = e.run([B(0,100,101,99,100), B(1,97,99,96,98)])
    assert s.position_avg_price == 97


class VerifiedLimit:
    def on_bar_close(self, e, b):
        if b.index == 0:
            e.entry("L", Side.BUY, 1, limit=98)


def test_limit_verification_one_tick():
    cfg = RuntimeConfig(
        mintick=.25,
        backtest_fill_limits_assumption_ticks=1,
    )
    e = PineShadowEngine(cfg, VerifiedLimit())
    s = e.run([B(0,100,101,99,100), B(1,100,100,97.75,99)])
    assert s.position_avg_price == 98


class SameBarStop:
    def on_bar_close(self, e, b):
        if b.index == 0:
            e.entry("L", Side.BUY, 1, limit=98)
            e.exit("LX", "L", stop=97, limit=105)


def test_same_bar_entry_then_stop_round_trip():
    # O-H-L-C because high is closer to open.
    e = PineShadowEngine(
        RuntimeConfig(mintick=.25, slippage_ticks=1),
        SameBarStop(),
    )
    s = e.run([B(0,100,101,99,100), B(1,100,101,96,98)])
    assert len(s.closed_trades) == 1
    t = s.closed_trades[0]
    assert t.entry_price == 98
    assert t.exit_price == 96.75


class SameBarTarget:
    def on_bar_close(self, e, b):
        if b.index == 0:
            e.entry("L", Side.BUY, 1, limit=98)
            e.exit("LX", "L", stop=94, limit=102)


def test_same_bar_entry_then_target_after_reversal():
    # Equal-distance tie uses OLHC in v1 calibration profile.
    e = PineShadowEngine(
        RuntimeConfig(mintick=.25, slippage_ticks=1),
        SameBarTarget(),
    )
    s = e.run([B(0,100,101,99,100), B(1,100,103,97,102)])
    assert len(s.closed_trades) == 1
    assert s.closed_trades[0].exit_price == 102


class ImmediateClose:
    def on_bar_close(self, e, b):
        if b.index == 0:
            e.entry("L", Side.BUY, 1)
        if b.index == 1 and e.position_size > 0:
            e.close("L", immediately=True)


def test_immediate_close_on_close_tick():
    e = PineShadowEngine(
        RuntimeConfig(mintick=.25, slippage_ticks=1),
        ImmediateClose(),
    )
    s = e.run([B(0,100,100,100,100), B(1,101,102,100,101.5)])
    assert len(s.closed_trades) == 1
    assert s.closed_trades[0].entry_price == 101.25
    assert s.closed_trades[0].exit_price == 101.25
