from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Iterable
import math


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderKind(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderRole(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    CLOSE = "close"


@dataclass(frozen=True)
class Bar:
    index: int
    ts_open_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def historical_path(self) -> List[float]:
        """TradingView historical broker-emulator price-path assumption.

        If high is closer to open than low: O-H-L-C.
        Otherwise: O-L-H-C.

        Tie behavior is an explicit calibration item. v1 uses O-L-H-C
        deterministically until TradingView calibration locks the edge case.
        """
        dh = abs(self.high - self.open)
        dl = abs(self.open - self.low)
        if dh < dl:
            return [self.open, self.high, self.low, self.close]
        return [self.open, self.low, self.high, self.close]


@dataclass
class RuntimeConfig:
    mintick: float = 0.25
    point_value: float = 2.0
    slippage_ticks: int = 1
    commission_cash_per_contract_per_side: float = 0.50
    pyramiding: int = 0
    process_orders_on_close: bool = False
    calc_on_order_fills: bool = False
    calc_on_every_tick: bool = False
    backtest_fill_limits_assumption_ticks: int = 0
    initial_capital: float = 25_000.0


@dataclass
class Order:
    order_id: str
    side: Side
    kind: OrderKind
    qty: int
    role: OrderRole
    created_bar: int
    eligible_bar: int
    limit: Optional[float] = None
    stop: Optional[float] = None
    from_entry: Optional[str] = None
    active: bool = True
    comment: str = ""


@dataclass
class ExitBracket:
    exit_id: str
    from_entry: str
    created_bar: int
    eligible_bar: int
    stop: Optional[float]
    limit: Optional[float]
    active: bool = True


@dataclass
class OpenTrade:
    entry_id: str
    side: Side
    qty: int
    entry_price: float
    entry_bar: int
    entry_time_ms: int
    entry_commission: float


@dataclass
class ClosedTrade:
    entry_id: str
    exit_id: str
    side: Side
    qty: int
    entry_price: float
    exit_price: float
    entry_bar: int
    exit_bar: int
    entry_time_ms: int
    exit_time_ms: int
    gross_pnl: float
    commission: float
    net_pnl: float
    reason: str


@dataclass
class Fill:
    order_id: str
    role: OrderRole
    side: Side
    qty: int
    price: float
    bar_index: int
    tick_label: str
    reason: str


@dataclass
class BrokerState:
    cash: float
    position_size: int = 0
    position_avg_price: float = math.nan
    open_trade: Optional[OpenTrade] = None
    orders: Dict[str, Order] = field(default_factory=dict)
    exits: Dict[str, ExitBracket] = field(default_factory=dict)
    closed_trades: List[ClosedTrade] = field(default_factory=list)
    fills: List[Fill] = field(default_factory=list)


class PineShadowBroker:
    """Contract-focused emulation of TradingView historical strategy fills."""

    def __init__(self, config: RuntimeConfig):
        self.cfg = config
        self.state = BrokerState(cash=config.initial_capital)
        self.current_bar: Optional[Bar] = None

    def entry(self, order_id: str, side: Side, qty: int,
              limit: Optional[float] = None, stop: Optional[float] = None,
              comment: str = "") -> None:
        if qty <= 0:
            return
        if limit is not None and stop is not None:
            raise NotImplementedError("stop-limit is outside ZAC v1 scope")
        kind = OrderKind.MARKET if limit is None and stop is None else (
            OrderKind.LIMIT if limit is not None else OrderKind.STOP
        )
        created = self.current_bar.index
        eligible = created if self.cfg.process_orders_on_close else created + 1
        self.state.orders[order_id] = Order(
            order_id=order_id, side=side, kind=kind, qty=int(qty),
            role=OrderRole.ENTRY, created_bar=created, eligible_bar=eligible,
            limit=limit, stop=stop, comment=comment
        )

    def exit(self, exit_id: str, from_entry: str,
             stop: Optional[float] = None, limit: Optional[float] = None) -> None:
        if stop is None and limit is None:
            return
        created = self.current_bar.index
        eligible = created if self.cfg.process_orders_on_close else created + 1
        self.state.exits[exit_id] = ExitBracket(
            exit_id=exit_id, from_entry=from_entry, created_bar=created,
            eligible_bar=eligible, stop=stop, limit=limit, active=True
        )

    def cancel(self, order_id: str) -> None:
        if order_id in self.state.orders:
            self.state.orders[order_id].active = False

    def close(self, entry_id: str, comment: str = "", immediately: bool = False) -> None:
        ot = self.state.open_trade
        if ot is None or ot.entry_id != entry_id:
            return
        side = Side.SELL if ot.side == Side.BUY else Side.BUY
        if immediately:
            fill = self._apply_slippage(self.current_bar.close, side)
            self._close_position(fill, self.current_bar, f"close:{comment}", entry_id + "-CLOSE", "close")
            return
        created = self.current_bar.index
        eligible = created if self.cfg.process_orders_on_close else created + 1
        oid = entry_id + "__CLOSE"
        self.state.orders[oid] = Order(
            order_id=oid, side=side, kind=OrderKind.MARKET,
            qty=abs(self.state.position_size), role=OrderRole.CLOSE,
            created_bar=created, eligible_bar=eligible,
            from_entry=entry_id, comment=comment
        )

    def close_all(self, comment: str = "", immediately: bool = False) -> None:
        if self.state.open_trade is not None:
            self.close(self.state.open_trade.entry_id, comment=comment, immediately=immediately)

    def process_bar_before_close(self, bar: Bar) -> None:
        self.current_bar = bar
        path = bar.historical_path()
        self._process_open_tick(bar, path[0])
        for label, a, b in [
            ("leg1", path[0], path[1]),
            ("leg2", path[1], path[2]),
            ("leg3", path[2], path[3]),
        ]:
            self._process_segment(bar, a, b, label)

    def begin_close_execution(self, bar: Bar) -> None:
        self.current_bar = bar

    def _eligible_orders(self, bar_index: int) -> Iterable[Order]:
        for o in list(self.state.orders.values()):
            if not o.active or o.eligible_bar > bar_index:
                continue
            if o.role == OrderRole.ENTRY:
                if self.cfg.pyramiding == 0 and self.state.position_size != 0:
                    continue
                yield o
            elif o.role == OrderRole.CLOSE:
                if self.state.open_trade is not None and o.from_entry == self.state.open_trade.entry_id:
                    yield o

    def _active_exit_events(self, bar_index: int) -> Iterable[Tuple[ExitBracket, str, Side, float]]:
        ot = self.state.open_trade
        if ot is None:
            return
        for ex in list(self.state.exits.values()):
            if not ex.active or ex.eligible_bar > bar_index or ex.from_entry != ot.entry_id:
                continue
            side = Side.SELL if ot.side == Side.BUY else Side.BUY
            if ex.stop is not None:
                yield ex, "stop", side, ex.stop
            if ex.limit is not None:
                yield ex, "limit", side, ex.limit

    def _process_open_tick(self, bar: Bar, px: float) -> None:
        for o in list(self._eligible_orders(bar.index)):
            if o.active and o.kind == OrderKind.MARKET:
                self._fill_order(o, self._apply_slippage(px, o.side), bar, "open", "market")

        changed = True
        safety = 0
        while changed and safety < 20:
            safety += 1
            changed = False
            events = self._events_at_price(bar, px)
            if events:
                _, event = events[0]
                self._execute_event(event, bar, "open")
                changed = True

    def _process_segment(self, bar: Bar, start: float, end: float, label: str) -> None:
        if start == end:
            return
        cur = start
        direction = 1 if end > start else -1
        safety = 0
        while safety < 100:
            safety += 1
            events = self._events_on_segment(bar, cur, end, direction)
            if not events:
                break
            events.sort(key=lambda x: x[0])
            _, event = events[0]
            event_px = event["event_px"]
            self._execute_event(event, bar, label)
            cur = event_px + direction * self.cfg.mintick * 1e-9
            if (direction > 0 and cur > end) or (direction < 0 and cur < end):
                break

    def _events_at_price(self, bar: Bar, px: float):
        out = []
        for o in self._eligible_orders(bar.index):
            ev = self._order_event_at_price(o, px)
            if ev:
                out.append((0.0, ev))
        for ex, which, side, level in self._active_exit_events(bar.index) or []:
            ev = self._exit_event_at_price(ex, which, side, level, px)
            if ev:
                out.append((0.0, ev))
        return out

    def _events_on_segment(self, bar: Bar, cur: float, end: float, direction: int):
        out = []
        for o in self._eligible_orders(bar.index):
            ev = self._order_event_on_segment(o, cur, end, direction)
            if ev:
                out.append((abs(ev["event_px"] - cur), ev))
        for ex, which, side, level in self._active_exit_events(bar.index) or []:
            ev = self._exit_event_on_segment(ex, which, side, level, cur, end, direction)
            if ev:
                out.append((abs(ev["event_px"] - cur), ev))
        return out

    def _order_event_at_price(self, o: Order, px: float):
        if o.kind == OrderKind.LIMIT:
            threshold = self._limit_verification_threshold(o.side, o.limit)
            ok = px <= threshold if o.side == Side.BUY else px >= threshold
            if ok:
                fill = o.limit if self.cfg.backtest_fill_limits_assumption_ticks > 0 else self._better_limit_fill(o.side, px, o.limit)
                return {"kind":"order","order":o,"event_px":px,"fill_px":fill,"reason":"limit-open"}
        elif o.kind == OrderKind.STOP:
            ok = px >= o.stop if o.side == Side.BUY else px <= o.stop
            if ok:
                return {"kind":"order","order":o,"event_px":px,"fill_px":self._apply_slippage(px,o.side),"reason":"stop-gap"}
        return None

    def _order_event_on_segment(self, o: Order, cur: float, end: float, direction: int):
        if o.kind == OrderKind.LIMIT:
            threshold = self._limit_verification_threshold(o.side, o.limit)
            if o.side == Side.BUY and direction < 0 and end <= threshold < cur:
                return {"kind":"order","order":o,"event_px":threshold,"fill_px":o.limit,"reason":"limit-touch"}
            if o.side == Side.SELL and direction > 0 and end >= threshold > cur:
                return {"kind":"order","order":o,"event_px":threshold,"fill_px":o.limit,"reason":"limit-touch"}
        elif o.kind == OrderKind.STOP:
            if o.side == Side.BUY and direction > 0 and end >= o.stop > cur:
                return {"kind":"order","order":o,"event_px":o.stop,"fill_px":self._apply_slippage(o.stop,o.side),"reason":"stop-touch"}
            if o.side == Side.SELL and direction < 0 and end <= o.stop < cur:
                return {"kind":"order","order":o,"event_px":o.stop,"fill_px":self._apply_slippage(o.stop,o.side),"reason":"stop-touch"}
        return None

    def _exit_event_at_price(self, ex: ExitBracket, which: str, side: Side, level: float, px: float):
        if which == "limit":
            threshold = self._limit_verification_threshold(side, level)
            ok = px <= threshold if side == Side.BUY else px >= threshold
            if ok:
                fill = level if self.cfg.backtest_fill_limits_assumption_ticks > 0 else self._better_limit_fill(side, px, level)
                return {"kind":"exit","exit":ex,"which":which,"side":side,"event_px":px,"fill_px":fill}
        else:
            ok = px >= level if side == Side.BUY else px <= level
            if ok:
                return {"kind":"exit","exit":ex,"which":which,"side":side,"event_px":px,"fill_px":self._apply_slippage(px,side)}
        return None

    def _exit_event_on_segment(self, ex: ExitBracket, which: str, side: Side, level: float, cur: float, end: float, direction: int):
        if which == "limit":
            threshold = self._limit_verification_threshold(side, level)
            if side == Side.BUY and direction < 0 and end <= threshold < cur:
                return {"kind":"exit","exit":ex,"which":which,"side":side,"event_px":threshold,"fill_px":level}
            if side == Side.SELL and direction > 0 and end >= threshold > cur:
                return {"kind":"exit","exit":ex,"which":which,"side":side,"event_px":threshold,"fill_px":level}
        else:
            if side == Side.BUY and direction > 0 and end >= level > cur:
                return {"kind":"exit","exit":ex,"which":which,"side":side,"event_px":level,"fill_px":self._apply_slippage(level,side)}
            if side == Side.SELL and direction < 0 and end <= level < cur:
                return {"kind":"exit","exit":ex,"which":which,"side":side,"event_px":level,"fill_px":self._apply_slippage(level,side)}
        return None

    def _execute_event(self, event, bar: Bar, tick_label: str) -> None:
        if event["kind"] == "order":
            self._fill_order(event["order"], event["fill_px"], bar, tick_label, event["reason"])
        else:
            ex = event["exit"]
            self._close_position(event["fill_px"], bar, f"exit:{event['which']}", ex.exit_id, tick_label)
            ex.active = False

    def _fill_order(self, o: Order, fill_px: float, bar: Bar, tick_label: str, reason: str) -> None:
        if not o.active:
            return
        o.active = False
        if o.role == OrderRole.ENTRY:
            if self.cfg.pyramiding == 0 and self.state.position_size != 0:
                return
            signed = o.qty if o.side == Side.BUY else -o.qty
            comm = o.qty * self.cfg.commission_cash_per_contract_per_side
            self.state.cash -= comm
            self.state.position_size = signed
            self.state.position_avg_price = fill_px
            self.state.open_trade = OpenTrade(
                entry_id=o.order_id, side=o.side, qty=o.qty, entry_price=fill_px,
                entry_bar=bar.index, entry_time_ms=bar.ts_open_ms, entry_commission=comm
            )
        else:
            self._close_position(fill_px, bar, reason, o.order_id, tick_label)
        self.state.fills.append(Fill(o.order_id,o.role,o.side,o.qty,fill_px,bar.index,tick_label,reason))

    def _close_position(self, exit_px: float, bar: Bar, reason: str, exit_id: str, tick_label: str) -> None:
        ot = self.state.open_trade
        if ot is None:
            return
        mult = 1.0 if ot.side == Side.BUY else -1.0
        gross = (exit_px - ot.entry_price) * mult * self.cfg.point_value * ot.qty
        exit_comm = ot.qty * self.cfg.commission_cash_per_contract_per_side
        total_comm = ot.entry_commission + exit_comm
        net = gross - total_comm
        self.state.cash += gross - exit_comm
        self.state.closed_trades.append(ClosedTrade(
            entry_id=ot.entry_id, exit_id=exit_id, side=ot.side, qty=ot.qty,
            entry_price=ot.entry_price, exit_price=exit_px,
            entry_bar=ot.entry_bar, exit_bar=bar.index,
            entry_time_ms=ot.entry_time_ms, exit_time_ms=bar.ts_open_ms,
            gross_pnl=gross, commission=total_comm, net_pnl=net, reason=reason
        ))
        side = Side.SELL if ot.side == Side.BUY else Side.BUY
        self.state.fills.append(Fill(exit_id,OrderRole.EXIT,side,ot.qty,exit_px,bar.index,tick_label,reason))
        self.state.position_size = 0
        self.state.position_avg_price = math.nan
        self.state.open_trade = None
        for ex in self.state.exits.values():
            if ex.from_entry == ot.entry_id:
                ex.active = False

    def _apply_slippage(self, px: float, side: Side) -> float:
        slip = self.cfg.slippage_ticks * self.cfg.mintick
        return px + slip if side == Side.BUY else px - slip

    def _limit_verification_threshold(self, side: Side, limit: float) -> float:
        d = self.cfg.backtest_fill_limits_assumption_ticks * self.cfg.mintick
        return limit - d if side == Side.BUY else limit + d

    @staticmethod
    def _better_limit_fill(side: Side, px: float, limit: float) -> float:
        return min(px, limit) if side == Side.BUY else max(px, limit)


class PineShadowEngine:
    """Bar-by-bar orchestrator for ZAC historical strategy semantics."""

    def __init__(self, config: RuntimeConfig, strategy):
        self.config = config
        self.broker = PineShadowBroker(config)
        self.strategy = strategy

    def run(self, bars: Iterable[Bar]) -> BrokerState:
        for bar in bars:
            self.broker.process_bar_before_close(bar)
            self.broker.begin_close_execution(bar)
            self.strategy.on_bar_close(self, bar)
        return self.broker.state

    def entry(self, *args, **kwargs):
        return self.broker.entry(*args, **kwargs)

    def exit(self, *args, **kwargs):
        return self.broker.exit(*args, **kwargs)

    def cancel(self, *args, **kwargs):
        return self.broker.cancel(*args, **kwargs)

    def close(self, *args, **kwargs):
        return self.broker.close(*args, **kwargs)

    def close_all(self, *args, **kwargs):
        return self.broker.close_all(*args, **kwargs)

    @property
    def position_size(self) -> int:
        return self.broker.state.position_size

    @property
    def position_avg_price(self) -> float:
        return self.broker.state.position_avg_price

    @property
    def closedtrades(self) -> int:
        return len(self.broker.state.closed_trades)
