from __future__ import annotations
import math


def summary(state):
    trades = state.closed_trades
    gp = sum(max(t.net_pnl, 0.0) for t in trades)
    gl = -sum(min(t.net_pnl, 0.0) for t in trades)
    pf = gp / gl if gl > 0 else math.nan
    wins = sum(t.net_pnl > 0 for t in trades)

    return {
        "closed_trades": len(trades),
        "gross_profit": gp,
        "gross_loss_abs": gl,
        "profit_factor": pf,
        "win_rate": wins / len(trades) if trades else math.nan,
        "cash": state.cash,
    }
