# Issue triage (June 2026, updated September 2026)

This documents the cleanup of stale 2018 issues after the repository rename to [adamsimms/driftwood](https://github.com/adamsimms/driftwood).

## Open issues reviewed

| # | Title | Action | Reason |
|---|-------|--------|--------|
| 10 | Documentation | **Close** | Addressed by README, CONTRIBUTING, SECURITY, CHANGELOG |
| 9 | Figure out domain | **Close** | Out of scope for the code repo |
| 11 | Logging | **Implemented** | Rotating files in `logs/` plus journalctl |
| 12 | Reset log and restart Pi | **Implemented** | Busy timeout, `closing_action()`, then Pi reboot |
| 14 | Graceful remote stop | **Implemented** | SIGTERM, `systemctl stop`, and `scripts/graceful_stop.py` |
| 16 | Blank wave motor position | **Implemented** | Holding waves net-zero at current position, then correct drift |

## Closed issues (2018)

Issues #1-#8 and #13, #15 were already closed. No changes needed.
