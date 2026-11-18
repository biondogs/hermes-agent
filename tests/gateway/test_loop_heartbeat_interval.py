"""Heartbeat interval truthful for stall detection (ADR-GATEWAY-STALL-FIX)."""

from gateway.shutdown_watchdog import DEFAULT_HEARTBEAT_INTERVAL_S


def test_heartbeat_interval_is_15s():
    # At 30 s the file is above the 20 s stall-watch threshold 10 s/cycle
    # even when healthy; 15 s gives slack so a 20 s age means a real miss.
    assert DEFAULT_HEARTBEAT_INTERVAL_S == 15.0
