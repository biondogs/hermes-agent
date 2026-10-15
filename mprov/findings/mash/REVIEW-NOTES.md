# mash (mProv Admin Shell) — Review Notes (SW-MPROV-R4-MASH)

Register: ../mash.issues.yaml (28 findings: 6 x S2, 16 x S3, 6 x S4; 23 bugs, 5 enhancements)
Reviewed commit: master @ d8871d44c7c754198d825b32984fbc99fbd3d1f7 ("Merge pull request #6
from mprov-ng:jhujasonw/issue4", 2023-11-16). Working tree verified clean (git status empty),
so reviewed lines == commit lines.
Date: 2026-10-15. Reviewer: sw-reviewer. Method: full-tree read — 18/18 tracked files,
every line. No code changes, no commits, no issues filed.

## Method beyond reading

Suspected defects were grounded by executing the real CLI (PYTHONPATH=src, python3 -m
mash.main) against unit probes of the exact primitives and a mock control center
implementing the current CC contract (root 200, /datamodel/ + ?model=, /systems/,
/power/<action>/?hostname=, Api-Key auth, 401/500/403/hang variants). Probes:
- Primitive checks: base64.b64encode(str) TypeError; connect arg indexing ('user' ==
  args[2] false for real input; IndexError on 2-token forms); shlex.split(arg, 2)
  dropping tokens after '#'; csv.reader("foo,bar") yielding single-char rows; the
  args.replace(pluginName,"") corruption ('bmc power on bmc001' -> 'power on 001');
  mapping-shaped config crash in the load_config flatten loop.
- End-to-end: raw-traceback crashes (let without '=', seq with non-numeric, update with
  '='-less token); nonexistent script file -> exit 0, no output; errors + "OK" streams;
  pvar foo,bar printing nothing; stale MPROV_RESULT after a 500 delete; connect to
  403-root -> silence then "Unknown Model"; bmc power without trailing slash ->
  'Failed to parse: 127.0.0.1:<port>power is not a valid host or port' vs silent
  success with slash; dict-arg sys.exit killing the session (script's later lines never
  run); hung endpoint + SIGINT + SIGTERM both swallowed (SIGKILL required); positive
  controls (apikey connect, retrieve, create required-field validation all work).
Refuted or weakened hypotheses (per R10 discipline) are listed below; they are not in
the register.

## API-drift check vs mprov_control_center @98d4579 (cross-repo)

Current CC URL surface (mprov_control_center/urls.py) still contains everything mash
depends on:
- 'datamodel/' (DataTypeView) — present, same response shape mash parses:
  {'datamodels': [...]} and getJSONDataStructure's {'endpoint': ..., 'fields': {...}}
  (fields carry a 'required' flag; common/views.py:175-196). Model 'endpoint' values
  have a LEADING slash (e.g. '/systems/', systems/models.py:71) — this is what makes
  MASH-003 (bmc URL composition) a real divergence between the two mash code paths.
- 'power/<str:action>/' (SystemPowerAPIView) — present; accepts ?hostname=, matching
  bmc.py's call; also accepts ?id= which mash does not use.
- Auth header 'Api-Key <key>' matches CC's rest_framework_api_key setup (settings.py,
  common/views.py permission_classes HasAPIKey|IsAuthenticated).
- Root URL '/' is IndexAPIView with auth/permission disabled — so mash's connect
  health-check GET on mprovURL works against current CC.
Conclusion: no breaking drift — the 2023 client still speaks the 2026 API surface for
everything it calls. Non-breaking drift found: CC's power endpoint supports additional
actions ('pxe', 'pxeefi' — systems/views.py _doPowerCmd) that mash's help does not
document (register MASH-022, S4). Enhancement-class gaps a future mash could target
(observation, not register items): CC routes mash cannot reach with existing verbs —
'networks/<pk>/update-with-confirmation/' and 'preview-subnet-changes/', 'jobqueue/
status-changes/', 'systems/register'. These need only generic verb support or minor
endpoint-model additions once CC exposes them in the datamodel.

CROSS-REPO ROUTING ITEM for adjudication (charter section 5 — files against the repo
owning the PRIMARY evidence; primary evidence here is in control_center, noted so it
is not lost and not misfiled against mash):
- bmc power / ?hostname= is a SUBSTRING match on the CC side:
  mprov_control_center systems/views.py:816-818 filters
  System.objects.filter(hostname__contains=request.query_params['hostname']) and
  silently truncates to 10 BMCs at lines 821-822. mash (bmc.py:49) sends what the
  operator believes is an exact hostname, so 'bmc power off compute001' can power off
  compute001 AND compute0010..compute0019 (any system whose hostname contains the
  string), capped at 10 BMCs, with results the CLI then discards (MASH-004). Named
  scenario: unsaved-work loss / forced power-off of up to 10 wrong nodes from a single
  targeted power command. This is S1-class material but its fix (exact/hostname
  lookup or documented match semantics) belongs in mprov_control_center; recommend
  the R1/adjudication lane evaluate it for the control_center register. mash-side
  mitigations (per-node result display, use of ?id=) would only paper over it.

## Staleness / dependency currency

- Repo untouched since 2023-11-16; VERSION 0.0.9; still functionally compatible with
  current CC (above). The critical currency problem is not API drift but tooling:
  the release/publish workflow is built on removed/deprecated runner components
  (MASH-023), and dependency specs are entirely unbounded (MASH-027).
- Runtime deps today: pyyaml/jinja2/requests — all unpinned, all currently install
  and run cleanly (verified: mash ran against current PyPI versions in a fresh venv).
- Python floor 3.8 declared (setup.cfg) — upstream EOL since 2024-10; folded into
  MASH-023's repro rather than a separate finding (same workflow/metadata surface).

## Observations (NOT register findings; R8/R10/R11 exclusions)

- API-key handling: the key never enters OS argv — mash commands are read from
  stdin/file, and `ps` shows only `python -m mash.main` (verified). So no /proc
  cmdline exposure. Plaintext ~/.mprov-mash.yaml is standard CLI practice; no
  evidence of world-readable files created by mash (mash never writes config).
  Possible future enhancement (below obvious-bar, kept out of register): an env-var
  fallback (e.g. MPROV_APIKEY) would keep keys out of dotfiles; left as observation
  because it needs a product decision, not a one-line obvious win.
- connect accepts http:// URLs without warning: TLS verification itself is requests'
  default (verify=True) — no verify=False anywhere, good. A cleartext URL sends the
  API key unencrypted; warning on http would be reasonable, but it is an advisory
  nicety, so observation.
- Refuted: renderString's `e.message` (app.py:448-449) — jinja2 exceptions carry a
  valid `.message`, so the error path does not AttributeError (verified by execution:
  clean "Error trying to template..." message). The real defect there is the stream,
  counted in MASH-010.
- The initial-connect GET is wrapped in a bare `except:` (app.py:463) that also
  swallows KeyboardInterrupt; folded conceptually into MASH-009's signal finding, not
  counted twice.
- do_disconnect's os.wait()/processes bookkeeping (app.py:207-216) can raise
  ChildProcessError/ValueError in edge interleavings (child reaped elsewhere, pid not
  in list); no concrete interleaving traced in normal use, so per R10 it stays an
  observation, not a finding.
- do_help echoes the raw argument after plugin help (app.py:121,135 uses print not
  self.print, and line 135 prints the arg again) — cosmetic noise, S4-lint-class,
  covered by the one-per-repo lint recommendation (MASH-028).
- README documents install only, no usage/commands; the in-shell help (docstrings)
  is the only user documentation and itself has drift (MASH-019, MASH-022). Docs
  expansion is a redesign-sized ask — REVIEW-NOTES only per R11.
- load_config also falls back to /etc/mprov/jobserver.yaml (app.py:62) — evidently
  intentional config sharing with the jobserver; undocumented (same doc-gap cluster
  as MASH-019).
- Unused `__main__()` wrapper in main.py:35-36 and the never-None branch main.py:28-30
  (open() raises rather than returning None) — dead-code trivia folded under MASH-012's
  repro; not separate issues.
- CI has no test job at all (release-trigger only) — covered by MASH-028's lint step
  recommendation; a full test-suite ask would exceed the obvious-bar.

## Open-issue collision check (R13)

`gh issue list -R biondogs/mash --state open` returns: "the 'biondogs/mash' repository
has disabled issues". So there are no open issues to collide with — but the FORK HAS
ISSUES DISABLED, which blocks the filing lane for this repo entirely. The filing card
(t_290a32eb / program owner) must enable issues on biondogs/mash before any filing,
or route mash findings elsewhere. Same check should be repeated for the other three
forks at adjudication time. No upstream (mprov-ng/mash) open-issue scan was possible
from this environment beyond the fork; adjudication's R13 re-check should also scan
the upstream repo to avoid duplicates of long-standing known issues.

## Coverage statement

18/18 tracked files, line-by-line: src/mash/{__init__,app,main,utils}.py,
src/mash/mash, src/mash/plugins/{__init__,bmc}.py, .github/workflows/ci.yml,
.gitignore, LICENSE, MANIFEST.in, README.md, VERSION, gen_changelog.sh,
pyproject.toml, requirements.txt, setup.cfg, setup.py. Evidence excerpts verified
verbatim at the pinned commit by scripts/validate_register.py (PASS; tally S2=6,
S3=16, S4=6). Behavior claims in repro fields were reproduced by execution unless
explicitly marked as mechanism-traced; negative results (refutations) are recorded
above rather than as findings.
