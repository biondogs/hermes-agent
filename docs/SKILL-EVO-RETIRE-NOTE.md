# SKILL-EVO-RETIRE — nightly GEPA skill evolution retired (2026-10-24)

**Why:** operator GO 2026-10-24, option 1 (Telegram DM, verbatim: *"Option 1 retire the
Cron and do the split"*), card `t_985fdc6c`. Basis: `docs/SKILL-EVO-AUDIT.md`
(commit `ebaceda`, card `t_ba7a5ab9`) — 97 nightly batches, **0 promotions ever**
(all 10 completed runs byte-identical to baseline; 92 all-fail nights), upstream
`NousResearch/hermes-agent-self-evolution` effectively unmaintained (last commit
2026-06-17, 101 open PRs).

**What was retired** (2026-10-24 ~23:05 EDT, run 180 of `t_985fdc6c`):

- Root-registry cron **`8feacb98cfb3` "nightly-skill-evolution"** (`0 3 * * *`,
  no-agent, script `nightly-skill-evolution.sh`, workdir
  `/home/arch/.hermes/hermes-agent-self-evolution`, deliver `local`; created
  2026-07-20, 99 completions, last run 2026-10-24 05:45 all-fail).
- Sequence: `hermes cron pause 8feacb98cfb3` → `hermes cron remove 8feacb98cfb3`
  (with `HERMES_HOME=/home/arch/.hermes` — root registry). Post-check:
  `hermes cron list` has no `8feacb98cfb3` entry and `jobs.json` contains 0
  references. Run **history is preserved** in `~/.hermes/cron/executions.db`
  (the job's 99 executions remain queryable there; only the schedule is gone).

**Nothing was deleted.** Everything is kept in place, dormant:

| Piece | Path | Notes |
|---|---|---|
| Orchestrator script | `~/.hermes/scripts/nightly_skill_evolution.py` | Includes the per-skill override config from `t_ef0304ab` (plan + hermes-agent-skill-authoring: 8 iterations / 3700 s; default 10 / 3300 s) and the all-fail batch ALARM logic — all now dormant. Also carries R4 changes (`t_95ee18df`): `LITELLM_BASE_URL`/`ORB_API` resolved from `.env`, no hardcoded endpoint, mtime-fallback ranking. |
| Cron wrapper | `~/.hermes/scripts/nightly-skill-evolution.sh` | `$HOME`-relative paths (R4 path scrub). |
| Evo repo + venv | `~/.hermes/hermes-agent-self-evolution/` (~345 MB incl. venv) | Branch `main`, **ahead 2 of origin/main** — the two local-only fixes that made the pipeline run at all (`4755417` 2026-10-18 DSPy 3.2.1/GEPA repair + one more). `datasets/`, `output/`, `reports/`, `.evolution-state.json` all preserved. |
| Batch log | `~/.hermes/logs/evolution.log` | 97 batch summaries — the audit's primary source. |
| Config/capitulation backups | `~/.hermes/skill-backups/curator-go-2a-2026-10-24/` | Script revisions, diffs, timed verification runs, and `jobs.json.pre-update` (contains the **full pre-retirement job definition** as a JSON entry). |

**Still live, untouched** (per the same GO): curator cron **`a4f3a5577b55`
"nightly-skill-curator"** (05:00 daily) and lintlang guardrails. The curator
prompt's §1 (review evolution candidates) will simply find zero new candidates
forever — harmless no-op; do not remove it, it is the re-arm interface.

**No other system fed the evo batch**: the alarm, timeout wrappers, and
per-skill caps all live inside the script above; no separate alarm cron,
watchdog, or board card depends on the batch. The `LITELLM_BASE_URL`/`ORB_API`
env entries for selfevolution (R4, `t_95ee18df`) remain — they only matter if
the batch is re-armed.

## How to re-arm (if ever)

1. **Prerequisites**: evo venv present (`~/.hermes/hermes-agent-self-evolution/.venv`),
   `LITELLM_BASE_URL` (or `ORB_API`) + `LITELLM_API_KEY` in `~/.hermes/.env`, orb/LiteLLM
   serving pod up, and the 2 local commits still on `main` (or upstream finally merged
   the community fixes — check first).
2. **Dry-run once manually** (no cron): the script runs standalone thanks to R4 —
   `bash ~/.hermes/scripts/nightly-skill-evolution.sh` from any shell. The audit's
   timing caveat still applies: `plan` and other >10 KB skills need ~4,200–5,200 s
   per skill; a 3-skill night cannot fit a 10,800 s window at those sizes (cap
   2 skills/night ≈ 6,600 s at the default 3,300 s budget).
3. **Re-create the cron** (root registry — the `HERMES_HOME` override is required
   from any profile session):

   ```bash
   HERMES_HOME=/home/arch/.hermes hermes cron create '0 3 * * *' \
     --name nightly-skill-evolution \
     --script ~/.hermes/scripts/nightly-skill-evolution.sh \
     --no-agent --deliver local \
     --workdir /home/arch/.hermes/hermes-agent-self-evolution
   ```

   (Original prompt text, for reference: "Nightly LLM-orchestrated skill evolution.
   The script auto-discovers all installed skills, queries the Hermes session DB for
   usage data, asks an LLM to pick the top 3 most worthwhile skills to evolve, runs
   DSPy+GEPA optimization on each, and runs lintlang guardrails. Runs at 3 AM.")
4. **Verify** with `hermes cron list` (new id will differ; the old `8feacb98cfb3`
   id is retired) and the curator's next 05:00 report (§1 should again see candidates).

Also retired in the same GO (this card, item 3): the `hermes-profile-management`
oversize split — see `SKILL-EVO-RETIRE-NOTE.md` §below / the card receipt; the
16,085 B → 12,890 B CURATE-4 split was executed by `t_4694614d` (CURATOR-GO-2B,
2026-10-24 17:37 EDT) and independently re-verified by this card.

— kanban-board-architect, card `t_985fdc6c`, 2026-10-24. Internal repo: no
public writes, no gateway restart.
