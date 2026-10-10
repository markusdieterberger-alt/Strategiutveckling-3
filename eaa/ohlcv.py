"""Conservative OHLC envelopes for exported trades, not tick-order reconstruction."""

from dataclasses import replace
from datetime import timedelta

from .funded import Sample
from .io import number, read_rows, timestamp


def attach_ohlcv(trades, path):
    bars = {}
    previous = None
    for r in read_rows(path):
        at = timestamp(r["time"])
        o, h, l, c = [number(r[k]) for k in ("open", "high", "low", "close")]
        if at.second or at.microsecond or at in bars or (previous and at <= previous):
            raise ValueError("OHLCV must be ordered unique minute-open timestamps")
        if not 0 < l <= min(o, c) <= max(o, c) <= h:
            raise ValueError("Invalid OHLC bar")
        bars[at], previous = (o, h, l, c), at
    result = []
    for t in trades:
        if t.entry.second or t.exit.second or t.entry.microsecond or t.exit.microsecond:
            raise ValueError("OHLC envelope requires minute-aligned export timestamps")
        at, samples = t.entry, []
        while at <= t.exit:
            if at not in bars:
                raise ValueError(f"Missing OHLC minute {at} for trade {t.id}")
            o, h, l, c = bars[at]
            adverse, favorable = (l, h) if t.side == 1 else (h, l)
            # Include the complete boundary bars as adverse envelopes. Extremes
            # may precede entry/follow exit: deliberately marked approximative.
            for price in (o, adverse, favorable, c):
                samples.append(Sample(at, (price - t.entry_price) * t.side))
            at += timedelta(minutes=1)
        result.append(replace(t, samples=tuple(samples), quality="OHLC_ENVELOPE_ADVERSE_FIRST_BOUNDARY_AMBIGUOUS"))
    return result
