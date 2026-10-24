#!/usr/bin/env python3
"""F14 fence-bounce watchdog: prints a restart alert ONLY when (a) the running
gateway predates hotfix 602ea0a874 (board-fence not live) AND (b) every active
board has zero running tasks AND (c) we haven't already alerted for this epoch.
Empty stdout = silence (cron delivers nothing). Self-silences after bounce."""
import json, os, sqlite3, subprocess, sys

HOME = os.path.expanduser("~")
BOARDS = [
    ("default", f"{HOME}/.hermes/kanban.db"),
    ("gargantua01", f"{HOME}/.hermes/kanban/boards/gargantua01/kanban.db"),
    ("gargantua02", f"{HOME}/.hermes/kanban/boards/gargantua02/kanban.db"),
    ("gaudi", f"{HOME}/.hermes/kanban/boards/gaudi/kanban.db"),
    ("skipjack", f"{HOME}/.hermes/kanban/boards/skipjack/kanban.db"),
    ("skipjack-prototype", f"{HOME}/.hermes/kanban/boards/skipjack-prototype/kanban.db"),
    ("software-co", f"{HOME}/.hermes/kanban/boards/software-co/kanban.db"),
]
MARKER = f"{HOME}/.hermes/cache/fence-bounce-alerted.json"

def hotfix_epoch():
    out = subprocess.run(
        ["git", "-C", f"{HOME}/.hermes/hermes-agent", "log", "-1", "--format=%ct", "602ea0a874"],
        capture_output=True, text=True)
    return int(out.stdout.strip()) if out.returncode == 0 and out.stdout.strip() else None

def gateway_info():
    # gateway runs unmanaged (no systemd unit): scan /proc for hermes 'gateway run'
    pid = None
    for p in os.listdir("/proc"):
        if not p.isdigit():
            continue
        try:
            cl = open(f"/proc/{p}/cmdline", "rb").read().decode(errors="replace")
        except OSError:
            continue
        if ("gateway" in cl and "run" in cl and "hermes-agent" in cl
                and "tui_gateway" not in cl and "metatron" not in cl):
            pid = int(p)
            break
    if pid is None:
        return None, None
    try:
        with open(f"/proc/{pid}/stat") as f:
            fields = f.read().rsplit(")", 1)[1].split()
        starttime_ticks = int(fields[19])
        clk = os.sysconf("SC_CLK_TCK")
        with open("/proc/stat") as f:
            btime = next(int(l.split()[1]) for l in f if l.startswith("btime"))
        return pid, btime + starttime_ticks / clk
    except Exception:
        return None, None

def main():
    hf = hotfix_epoch()
    pid, start = gateway_info()
    if hf is None or pid is None:
        sys.exit(0)  # can't determine -> stay silent, don't nag
    if start > hf:
        # fence is live; clear any marker and go quiet forever
        try: os.remove(MARKER)
        except OSError: pass
        return
    running = 0
    for slug, db in BOARDS:
        try:
            c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=2)
            running += c.execute("select count(*) from tasks where status='running'").fetchone()[0]
            c.close()
        except Exception:
            running += 1  # unreadable board counts as busy; never alert on missing data
    if running > 0:
        return
    try:
        with open(MARKER) as f:
            if json.load(f).get("hotfix_epoch") == hf:
                return  # already alerted for this pre-bounce epoch
    except Exception:
        pass
    os.makedirs(os.path.dirname(MARKER), exist_ok=True)
    with open(MARKER, "w") as f:
        json.dump({"hotfix_epoch": hf, "gateway_pid": pid}, f)
    print("FLEET ALERT — gateway state needs a bounce: "
          "agents may now run the canonical graceful bounce themselves (operator ruling 2026-10-24, t_d2f0a30f): "
          "bash ~/.hermes/scripts/gateway-graceful-bounce.sh --reason \"<why>\" "
          "(skill hermes-gateway-graceful-bounce, owned by kanban-board-architect). "
          "All 7 boards report zero running tasks; gateway PID %d." % pid)

if __name__ == "__main__":
    main()
