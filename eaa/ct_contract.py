"""Synthetic execution-contract oracle; not a Pine engine or signal backtest.

No historical strategy metrics can be inferred from this module's tests.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
import math
from zoneinfo import ZoneInfo

MODELS = ('FADE', 'DIV', 'TRAP', 'AGG', 'ABSORB', 'VRZ')


def audit_exposure(submitted_bar, current_bar, side, position_size=0, closed_exit_bar=None):
    """Exclude rejected orders and bars after a delayed immediate-exit report."""
    return (side != 0 and submitted_bar is not None and current_bar > submitted_bar
            and (closed_exit_bar is None or closed_exit_bar == current_bar)
            and (position_size != 0 or closed_exit_bar is not None))


def session_open(stamp: datetime, cutoff=1004):
    if stamp.tzinfo is None:
        raise ValueError('Timezone-aware timestamp required')
    local = stamp.astimezone(ZoneInfo('America/New_York'))
    minute = local.hour * 60 + local.minute
    return (local.weekday() <= 4 and minute < cutoff) or (local.weekday() in (6, 0, 1, 2, 3) and minute >= 1080)


def levels(side, close, sl, tp, min_distance, tick=.25):
    if side not in (-1, 1) or not all(map(math.isfinite, (close, sl, tp, min_distance, tick))) or tick <= 0 or min_distance <= 0:
        raise ValueError('Invalid level input')
    safe = min(sl, close - min_distance) if side == 1 else max(sl, close + min_distance)
    def rounded(price, up):
        ratio = Decimal(str(price)) / Decimal(str(tick))
        return float(ratio.to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR) * Decimal(str(tick)))
    stop, target = rounded(safe, side == -1), rounded(tp, side == 1)
    if side * (close - stop) <= 0 or side * (target - close) <= 0:
        raise ValueError('Wrong-sided bracket')
    return stop, target


@dataclass(frozen=True)
class Bar:
    index: int
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        if not all(map(math.isfinite, (self.open, self.high, self.low, self.close))) or not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError('Invalid OHLC')


def stop_first_exit(side, stop, target, bar, slip_ticks=1, tick=.25):
    """Adverse OHLC contract for an ALREADY ACTIVE bracket, not TV fills."""
    if side not in (-1, 1) or side * (target - stop) <= 0 or slip_ticks < 0:
        raise ValueError('Invalid exit contract')
    stop_hit = bar.low <= stop if side == 1 else bar.high >= stop
    tp_hit = bar.high >= target if side == 1 else bar.low <= target
    if stop_hit:
        price = min(bar.open, stop) if side == 1 else max(bar.open, stop)
        return 'SL', price - side * slip_ticks * tick, bool(tp_hit)
    if tp_hit:
        # Deliberately no beneficial gap improvement in this conservative oracle.
        return 'TP', target, False
    return None


def stress_net(side, entry, actual_exit, adverse_exit, qty=1, pointvalue=2, fees=1):
    if side not in (-1, 1) or not isinstance(qty, int) or qty < 1 or fees < 0:
        raise ValueError('Invalid stress input')
    actual = side * (actual_exit-entry) * pointvalue * qty - fees
    return actual if adverse_exit is None else min(actual, side * (adverse_exit-entry) * pointvalue * qty - fees)


class Slot:
    """Small state-machine contract to test submission timing and collisions."""
    def __init__(self):
        self.pending = None
        self.active = None
        self.last_exit_bar = None

    def submit(self, bar, candidates, allowed=True, data_ok=True):
        if not allowed or not data_ok or self.pending or self.active or self.last_exit_bar == bar:
            return None
        directions = {c[0] for c in candidates}
        if len(directions) != 1:
            return None
        chosen = min(candidates, key=lambda c: MODELS.index(c[1]))
        self.pending = (bar, *chosen)
        return chosen

    def next_bar(self, bar, force_flat=False):
        if self.pending and bar.index > self.pending[0]:
            _, side, model, stop, target = self.pending
            self.pending = None
            self.active = (side, model, stop, target, bar.open)
        if self.active:
            side, model, stop, target, entry = self.active
            result = stop_first_exit(side, stop, target, bar)
            if result or force_flat:
                self.active = None
                self.last_exit_bar = bar.index
                return result or ('SESSION', bar.close, False)
        return None

    def cancel(self):
        self.pending = None
