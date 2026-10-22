import shutil
from pathlib import Path

pairs = [
    "kanban-worker", "g01-scribe", "g02-scribe", "sw-docs",
    "sw-dev-a", "sw-dev-b", "sw-qa", "sw-devops",
]
for p in pairs:
    backup = Path(f"/tmp/muse-wiring-v2/profile-backups/{p}.config.yaml.pre-muse")
    cfg = Path(f"/home/arch/.hermes/profiles/{p}/config.yaml")
    cfg.write_text(backup.read_text())
    ok = backup.read_bytes() == cfg.read_bytes()
    print(p, "restored-ok" if ok else "RESTORE-MISMATCH")
