#!/usr/bin/env python3
"""Acceptance grep for t_1a66c496 (mirrors gw_accept_grep of t_0d825d76):
python-literal check that the amended converge script carries BOTH exact
card-quoted texts, plus a live census count. Prints True/True/<n>."""
import importlib.util
from pathlib import Path

SCRIPT = Path("/local/projects/softwarecco" if False else "/local/projects/software-co/scripts/route_by_default_converge.py")
LIVE = Path("/home/arch/.hermes/profiles")

CARD_NSG_BULLET = ("- NO-SELF-GATE (fleet law since 2026-10-28; "
                   "doc: software-co `docs/gate-wait-pattern-2026-10-28.md` R6): "
                   "a card whose title/body declares it a text/review GATE must "
                   "be assigned to an INDEPENDENT gate profile — `distiller` "
                   "for text gates, `sw-reviewer` for code review — never to the "
                   "creating lane or the author of the bytes under review. "
                   "A gate may not weaken its own check set: check sets come "
                   "from policy + operator directives; a deviation is a finding "
                   "to escalate, not to absorb. A PASS discovered to be "
                   "self-issued is void — stop the apply leg, annotate the "
                   "record, re-gate independently and make the new gate card "
                   "the apply card's true parent.")
CARD_NSG_SENTENCE = (" Gate cards are never assigned to the creating lane or "
                     "the bytes' author — assign text gates to `distiller`, "
                     "code-review gates to `sw-reviewer` (NO-SELF-GATE, same doc R6).")

src = SCRIPT.read_text()
# carrier 1 (worker bullet) + carrier 2 (butler sentence) in the SCRIPT BODY
has_bullet_lit = CARD_NSG_BULLET in src
has_sentence_lit = CARD_NSG_SENTENCE.strip() in src

spec = importlib.util.spec_from_file_location("converge", SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
has_bullet_sec = m.worker_discipline_section().rstrip("\n").endswith(m.NSG_WORKER_BULLET)
has_item3_sec = m.ITEM3_NSGLAW.endswith(CARD_NSG_SENTENCE) and m.ITEM3_NSGLAW in m.intake_section("x", "y")

# live census
workers = sorted(d.name for d in LIVE.iterdir()
                 if d.is_dir() and (d / "SOUL.md").exists() and d.name not in m.WORKER_EXCLUDE)
live_workers = sum(1 for p in workers
                   if m.NSG_WORKER_GUARD in (LIVE / p / "SOUL.md").read_text())
live_butlers = sum(1 for _, _, _ in m.BUTLERS
                   if m.NSG_BUTLER_GUARD in (LIVE / _ / "SOUL.md").read_text()) if False else sum(
    1 for b in m.BUTLERS if m.NSG_BUTLER_GUARD in (LIVE / b[0] / "SOUL.md").read_text())
live_distiller = "NO-SELF-GATE precondition (R6.4)" in (LIVE / "distiller" / "SOUL.md").read_text()

print(f"carrier1_bullet_literal={has_bullet_lit} carrier2_sentence_literal={has_sentence_lit}")
print(f"sections_carry_texts={has_bullet_sec and has_item3_sec}")
print(f"live: workers={live_workers}/52 butlers={live_butlers}/5 distiller_r64={live_distiller}")
ok = has_bullet_lit and has_sentence_lit and has_bullet_sec and has_item3_sec \
     and live_workers == 52 and live_butlers == 5 and live_distiller
print(f"ACCEPTANCE: {ok}")
raise SystemExit(0 if ok else 1)
