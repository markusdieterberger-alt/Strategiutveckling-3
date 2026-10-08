from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class SessionAlignedClock:
    """Configurable approximation of TradingView time(tf) boundaries.

    TradingView aligns timeframe bars to the symbol session. The anchor is
    configurable and must ultimately be calibrated to TradingView timestamps
    for the exact chart symbol/session.

    For CME equity-index futures, 17:00 America/Chicago is the natural
    electronic-session anchor used by the ZAC calibration profile.
    """

    timezone: str = "America/Chicago"
    session_anchor_hour: int = 17
    session_anchor_minute: int = 0

    def bucket_open_ms(self, ts_ms: int, minutes: int) -> int:
        tz = ZoneInfo(self.timezone)
        utc = ZoneInfo("UTC")
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=utc).astimezone(tz)

        anchor = datetime.combine(
            dt.date(),
            dtime(self.session_anchor_hour, self.session_anchor_minute),
            tzinfo=tz,
        )
        if dt < anchor:
            anchor -= timedelta(days=1)

        delta_min = int((dt - anchor).total_seconds() // 60)
        bucket = (delta_min // minutes) * minutes
        out = anchor + timedelta(minutes=bucket)

        return int(out.astimezone(utc).timestamp() * 1000)
