"""Deterministic, single-position MNQ challenge replay with explicit data quality.

All amounts are USD relative to the initial balance. An EOD high-water mark
sets tomorrow's floor; today's open equity is checked against yesterday's floor.
This is a conditional replay of exported trades, not a new signal backtest.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta
import math
import random
import statistics
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Rules:
    name: str = "EAA_PROJECT_550_V1"
    target: float = 1250.0
    drawdown: float = 1000.0
    trail_lock_profit: float = 100.0
    daily_loss: float | None = 600.0
    dll_action: str = "lock_day"
    daily_profit: float | None = 550.0
    profit_action: str = "liquidate"
    consistency: float = 0.5
    max_contracts: int = 20
    point_value: float = 2.0
    tick_size: float = 0.25
    commission_rt: float = 1.0
    additional_slippage_ticks_side: float = 0.0
    other_cost_rt: float = 0.0
    timezone: str = "America/New_York"
    reopen: str = "18:00"
    cutoff: str = "16:45"

    def __post_init__(self):
        positive = [self.target, self.drawdown, self.point_value, self.tick_size]
        if not all(math.isfinite(v) and v > 0 for v in positive):
            raise ValueError("Target, drawdown, point value and tick size must be positive")
        if not math.isfinite(self.trail_lock_profit) or self.trail_lock_profit < 0:
            raise ValueError("Invalid trail lock")
        for v in (self.daily_loss, self.daily_profit):
            if v is not None and (not math.isfinite(v) or v <= 0):
                raise ValueError("Daily limits must be positive or null")
        if not 0 < self.consistency <= 1:
            raise ValueError("Consistency must be in (0, 1]")
        if type(self.max_contracts) is not int or not 1 <= self.max_contracts <= 20:
            raise ValueError("MNQ max_contracts must be an integer in 1..20")
        if self.dll_action not in {"lock_day", "fail"}:
            raise ValueError("dll_action must be lock_day or fail")
        if self.profit_action not in {"liquidate", "block_new"}:
            raise ValueError("profit_action must be liquidate or block_new")
        costs = (self.commission_rt, self.additional_slippage_ticks_side, self.other_cost_rt)
        if not all(math.isfinite(v) and v >= 0 for v in costs):
            raise ValueError("Costs must be finite and nonnegative")
        ZoneInfo(self.timezone)
        if time.fromisoformat(self.reopen) <= time.fromisoformat(self.cutoff):
            raise ValueError("This intraday futures model requires reopen after cutoff")

    @property
    def cost_side(self):
        return (self.commission_rt + self.other_cost_rt) / 2 + self.additional_slippage_ticks_side * self.tick_size * self.point_value


@dataclass(frozen=True)
class Sample:
    at: datetime
    points: float


@dataclass(frozen=True)
class Trade:
    id: str
    entry: datetime
    exit: datetime
    side: int
    entry_price: float
    exit_price: float
    source_qty: int = 1
    stop_points: float | None = None
    mae_points: float | None = None
    samples: tuple[Sample, ...] = ()
    quality: str = "CLOSED_TRADES_ONLY"

    @property
    def points(self):
        return (self.exit_price - self.entry_price) * self.side


def session_day(at: datetime, rules: Rules) -> date:
    if at.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    local = at.astimezone(ZoneInfo(rules.timezone))
    return local.date() + timedelta(days=local.time().replace(tzinfo=None) >= time.fromisoformat(rules.reopen))


def allowed(at: datetime, rules: Rules, *, exit_event=False) -> bool:
    local = at.astimezone(ZoneInfo(rules.timezone))
    clock = local.time().replace(tzinfo=None)
    cut, reopen = time.fromisoformat(rules.cutoff), time.fromisoformat(rules.reopen)
    morning = clock <= cut if exit_event else clock < cut
    return (local.weekday() < 5 and morning) or (local.weekday() in {6, 0, 1, 2, 3} and clock >= reopen)


def validate_trades(trades: list[Trade], rules: Rules) -> None:
    ids, previous = set(), None
    for t in trades:
        if not t.id or t.id in ids:
            raise ValueError("Empty or duplicate trade id")
        ids.add(t.id)
        if t.entry.tzinfo is None or t.exit.tzinfo is None or t.exit < t.entry:
            raise ValueError(f"{t.id}: invalid timestamps")
        if previous and t.entry < previous.exit:
            raise ValueError("Overlapping/partial trades unsupported; consolidate positions before replay")
        previous = t
        if t.side not in {-1, 1} or type(t.source_qty) is not int or t.source_qty < 1:
            raise ValueError(f"{t.id}: invalid side or quantity")
        if not all(math.isfinite(p) and p > 0 for p in (t.entry_price, t.exit_price)):
            raise ValueError(f"{t.id}: invalid prices")
        if any(abs(p / rules.tick_size - round(p / rules.tick_size)) > 1e-6 for p in (t.entry_price, t.exit_price)):
            raise ValueError(f"{t.id}: off-tick prices")
        if session_day(t.entry, rules) != session_day(t.exit, rules):
            raise ValueError(f"{t.id}: overnight trade; this release requires session-flat input")
        if not allowed(t.entry, rules) or not allowed(t.exit, rules, exit_event=True):
            raise ValueError(f"{t.id}: outside configured trading hours; no silent truncation")
        for value in (t.stop_points, t.mae_points):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError(f"{t.id}: invalid stop/MAE")
        last = t.entry
        for s in t.samples:
            if s.at.tzinfo is None or s.at < last or s.at > t.exit or not math.isfinite(s.points):
                raise ValueError(f"{t.id}: invalid or unordered intraday path")
            last = s.at


def contracts_for(t: Trade, rules: Rules, contracts: int, risk_budget: float | None):
    if type(contracts) is not int or not 1 <= contracts <= rules.max_contracts:
        raise ValueError("Requested contracts outside permitted integer range")
    if risk_budget is None:
        return contracts
    if not math.isfinite(risk_budget) or risk_budget <= 0:
        raise ValueError("Risk budget must be positive")
    if t.stop_points is None or t.stop_points <= 0:
        raise ValueError("Risk sizing requires known-at-entry stop_points, not ex-post MAE")
    stop = math.ceil(t.stop_points / rules.tick_size - 1e-9) * rules.tick_size
    return min(contracts, int(risk_budget // (stop * rules.point_value + 2 * rules.cost_side)))


@dataclass
class Result:
    status: str
    days: int
    net: float
    floor: float
    failure: str | None = None
    events: list[dict] = field(default_factory=list)
    quality: list[str] = field(default_factory=list)
    approximate: bool = True
    rules_verified: bool = False


def simulate(days: list[tuple[date, list[Trade]]], rules: Rules, contracts=1, risk_budget=None) -> Result:
    cash, floor, high_eod, largest_day = 0.0, -rules.drawdown, 0.0, 0.0
    events, quality = [], set()
    if type(contracts) is not int or not 1 <= contracts <= rules.max_contracts:
        raise ValueError("Invalid contracts")
    if risk_budget is not None and (not math.isfinite(risk_budget) or risk_budget <= 0):
        raise ValueError("Risk budget must be positive")
    if not days or any(days[i][0] >= days[i + 1][0] for i in range(len(days) - 1)):
        raise ValueError("Session calendar must be nonempty, ordered and unique")
    validate_trades([t for _, rows in days for t in rows], rules)

    def finish(status, n, failure=None):
        return Result(status, n, round(cash, 8), round(floor, 8), failure, events, sorted(quality))

    for day_index, (day, rows) in enumerate(days, 1):
        day_start, locked = cash, False
        for t in rows:
            if session_day(t.entry, rules) != day:
                raise ValueError("Trade assigned to wrong session")
            quality.add(t.quality)
            if locked:
                events.append({"day": str(day), "id": t.id, "event": "SKIP_DAY_LOCK"})
                continue
            qty = contracts_for(t, rules, contracts, risk_budget)
            if qty == 0:
                events.append({"day": str(day), "id": t.id, "event": "SKIP_SIZE_BELOW_ONE"})
                continue
            # No clamping of losses at a threshold: liquidate at the observed mark,
            # including adverse costs. Gaps may breach both DLL and MLL.
            entry_cash = cash - qty * rules.cost_side
            marks = [Sample(t.entry, 0.0)] + list(t.samples)
            if not t.samples and t.mae_points is not None:
                quality.add("MAE_ADVERSE_FIRST_UNKNOWN_TIME")
                marks.append(Sample(t.entry, -t.mae_points))
            marks.append(Sample(t.exit, t.points))
            reason = "EXIT"
            for i, s in enumerate(marks):
                equity = entry_cash + qty * s.points * rules.point_value
                liquidation = equity - qty * rules.cost_side
                last = i == len(marks) - 1
                mll = equity <= floor or (last and liquidation <= floor)
                dll = rules.daily_loss is not None and (equity - day_start <= -rules.daily_loss or (last and liquidation - day_start <= -rules.daily_loss))
                cap = rules.daily_profit is not None and liquidation - day_start >= rules.daily_profit
                if mll or dll or (cap and rules.profit_action == "liquidate") or last:
                    cash = liquidation
                    reason = "MLL" if mll or cash <= floor else "DLL" if dll else "PROFIT_STOP" if cap else "EXIT"
                    events.append({"day": str(day), "id": t.id, "time": s.at.isoformat(), "event": reason, "contracts": qty, "net": round(cash, 8), "floor": round(floor, 8)})
                    if reason == "MLL":
                        return finish("FAIL", day_index, "MLL")
                    if reason == "DLL":
                        if rules.dll_action == "fail":
                            return finish("FAIL", day_index, "DLL_PROJECT_HARD_FAIL")
                        locked = True
                    if cap:
                        locked = True
                    break
        profit = cash - day_start
        largest_day = max(largest_day, profit)
        high_eod = max(high_eod, cash)
        floor = min(rules.trail_lock_profit, max(floor, high_eod - rules.drawdown))
        events.append({"day": str(day), "event": "EOD", "day_net": round(profit, 8), "net": round(cash, 8), "floor": round(floor, 8)})
        if cash <= floor:
            return finish("FAIL", day_index, "MLL")
        # EOD-only pass assessment is intentional: no intraday target cherry-picking.
        if cash >= rules.target and largest_day <= rules.consistency * cash + 1e-8:
            return finish("PASS", day_index)
    return finish("ALIVE", len(days))


def rolling(trades: list[Trade], calendar: list[date], rules: Rules, horizon=15, contracts=1, risk_budget=None):
    if horizon < 1 or len(calendar) < horizon or calendar != sorted(set(calendar)):
        raise ValueError("Need an ordered, unique session calendar covering the full horizon")
    validate_trades(trades, rules)
    grouped = {d: [] for d in calendar}
    for t in trades:
        day = session_day(t.entry, rules)
        if day not in grouped:
            raise ValueError(f"Trade session {day} missing from calendar")
        grouped[day].append(t)
    return [simulate([(d, grouped[d]) for d in calendar[i:i + horizon]], rules, contracts, risk_budget) for i in range(len(calendar) - horizon + 1)]


def summarize(results: list[Result]):
    if not results:
        raise ValueError("No complete windows")
    n = len(results)
    passed = [r.days for r in results if r.status == "PASS"]
    counts = Counter(r.status for r in results)
    return {
        "windows": n,
        "pass_pct": 100 * counts["PASS"] / n,
        "fail_pct": 100 * counts["FAIL"] / n,
        "alive_pct": 100 * counts["ALIVE"] / n,
        "median_days_to_pass": statistics.median(passed) if passed else None,
        "pass_within": {str(d): 100 * sum(v <= d for v in passed) / n for d in (5, 10, 15)},
        "failures": dict(Counter(r.failure for r in results if r.failure)),
        "dll_lock_events": sum(e["event"] == "DLL" for r in results for e in r.events),
        "quality": sorted({q for r in results for q in r.quality}),
        "approximate": True,
        "rules_verified": False,
        "warning": "Overlapping windows are dependent. Conditional trade replay; no live probability or signal-regeneration claim.",
    }


def bootstrap(trades, calendar, rules, *, horizon=15, iterations=1000, block=5, seed=20261009, contracts=1, risk_budget=None):
    if iterations < 1 or block < 1 or block > len(calendar) or horizon < 1:
        raise ValueError("Invalid bootstrap dimensions")
    if len(calendar) < max(30, 2 * horizon) or len({session_day(t.entry, rules) for t in trades}) < 10:
        raise ValueError("Bootstrap requires >=30 sessions and >=10 trade-bearing sessions")
    validate_trades(trades, rules)
    if calendar != sorted(set(calendar)):
        raise ValueError("Invalid calendar")
    grouped = {d: [] for d in calendar}
    for t in trades:
        grouped[session_day(t.entry, rules)].append(t)
    rng, results = random.Random(seed), []
    # Replay each sampled day's intraday ordering intact. Shift only dates, then
    # assign synthetic monotonically increasing session dates for validation.
    from dataclasses import replace
    for _ in range(iterations):
        indices = []
        while len(indices) < horizon:
            start = rng.randrange(len(calendar) - block + 1)
            indices.extend(range(start, start + block))
        synthetic, target = [], date(2030, 1, 7)
        zone = ZoneInfo(rules.timezone)
        for j, idx in enumerate(indices[:horizon]):
            while target.weekday() >= 5:
                target += timedelta(days=1)
            source = calendar[idx]
            def shift(at):
                local = at.astimezone(zone)
                return datetime.combine(target + (local.date() - source), local.time(), zone)
            copied = [replace(t, id=f"{j}:{t.id}", entry=shift(t.entry), exit=shift(t.exit), samples=tuple(Sample(shift(s.at), s.points) for s in t.samples)) for t in grouped[source]]
            synthetic.append((target, copied))
            target += timedelta(days=1)
        results.append(simulate(synthetic, rules, contracts, risk_budget))
    return results
