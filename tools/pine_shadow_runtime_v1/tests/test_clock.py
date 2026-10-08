from datetime import datetime
from zoneinfo import ZoneInfo

from pine_shadow import SessionAlignedClock


def ms(s):
    return int(
        datetime.fromisoformat(s)
        .astimezone(ZoneInfo("UTC"))
        .timestamp() * 1000
    )


def test_4h_session_anchor_dst_safe():
    c = SessionAlignedClock("America/Chicago", 17, 0)
    x = ms("2026-10-08T18:10:00-05:00")
    y = c.bucket_open_ms(x, 240)
    dt = datetime.fromtimestamp(
        y / 1000,
        ZoneInfo("UTC"),
    ).astimezone(ZoneInfo("America/Chicago"))
    assert (dt.hour, dt.minute) == (17, 0)
