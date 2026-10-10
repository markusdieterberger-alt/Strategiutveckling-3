from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from zoneinfo import ZoneInfo

from eaa.io import attach_paths, load_trades, number, timestamp
from eaa.ohlcv import attach_ohlcv
from eaa.funded import Rules, validate_trades


class ImportTests(unittest.TestCase):
    def file(self, text):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "trades.csv"
        path.write_text(text)
        return path

    def test_paired_tv_rows_reverse_order(self):
        path = self.file("Trade #,Type,Date and time,Price USD,Position size (qty),Net P&L USD\n1,Exit long,2026-01-05 10:05:00,20010,1,999999\n1,Entry long,2026-01-05 10:00:00,20000,1,999999\n")
        trades = load_trades(path, "America/New_York")
        self.assertEqual(trades[0].points, 10)
        validate_trades(trades, Rules())

    def test_native_schema(self):
        path = self.file("trade_id,entry_time,exit_time,side,entry_price,exit_price,contracts,stop_points\n1,2026-01-05T10:00:00-05:00,2026-01-05T10:05:00-05:00,long,20000,20001,1,10\n")
        self.assertEqual(load_trades(path)[0].stop_points, 10)

    def test_open_trade_rejected(self):
        path = self.file("Trade #,Type,Date and time,Price USD,Position size (qty)\n1,Entry long,2026-01-05 10:00:00,20000,1\n")
        with self.assertRaises(ValueError):
            load_trades(path, "UTC")

    def test_timezone_required(self):
        with self.assertRaises(ValueError):
            timestamp("2026-01-05 10:00:00")

    def test_dst_fall_ambiguous_rejected(self):
        with self.assertRaises(ValueError):
            timestamp("2026-11-01 01:30:00", "America/New_York")

    def test_dst_spring_missing_rejected(self):
        with self.assertRaises(ValueError):
            timestamp("2026-03-08 02:30:00", "America/New_York")

    def test_explicit_offset_supported(self):
        self.assertIsNotNone(timestamp("2026-11-01T01:30:00-04:00").tzinfo)

    def test_locale_not_guessed(self):
        with self.assertRaises(ValueError):
            number("20.000,25")
        self.assertEqual(number("20,000.25"), 20000.25)

    def test_paths_require_all_ids(self):
        source = self.file("trade_id,entry_time,exit_time,side,entry_price,exit_price\n1,2026-01-05T10:00:00-05:00,2026-01-05T10:05:00-05:00,long,20000,20001\n")
        path = self.file("trade_id,time,unrealized_points\n2,2026-01-05T10:01:00-05:00,-5\n")
        with self.assertRaises(ValueError):
            attach_paths(load_trades(source), path)

    def test_ohlc_adverse_before_favorable(self):
        source = self.file("trade_id,entry_time,exit_time,side,entry_price,exit_price\n1,2026-01-05T10:00:00-05:00,2026-01-05T10:00:00-05:00,long,20000,20001\n")
        bars = self.file("time,open,high,low,close\n2026-01-05T10:00:00-05:00,20000,20010,19990,20001\n")
        t = attach_ohlcv(load_trades(source), bars)[0]
        self.assertEqual([s.points for s in t.samples], [0, -10, 10, 1])
        self.assertIn("AMBIGUOUS", t.quality)

    def test_ohlc_gap_fails(self):
        source = self.file("trade_id,entry_time,exit_time,side,entry_price,exit_price\n1,2026-01-05T10:00:00-05:00,2026-01-05T10:05:00-05:00,long,20000,20001\n")
        bars = self.file("time,open,high,low,close\n2026-01-05T10:00:00-05:00,20000,20010,19990,20001\n")
        with self.assertRaises(ValueError):
            attach_ohlcv(load_trades(source), bars)


if __name__ == "__main__":
    unittest.main()
