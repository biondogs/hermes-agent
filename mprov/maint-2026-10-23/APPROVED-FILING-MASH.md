# APPROVED-FILING — biondogs/mash (MPROV-M wave, 2026-10-23)

Adjudication: sw-architect, t_43e4e008, 2026-10-23. Register: `mash-maint.issues.yaml`
(t_1ee1e0e4) — 3 NEW findings; the 28 Oct-15 issues are dispositioned in that wave's
REVIEW-NOTES (24 STILL-LIVE/STILL-RELEVANT, 4 FIXED-UPSTREAM).
Pins: reviewed at upstream 36b6a5e (12 commits past Oct-15 pin d8871d4); fork f9bb463
is docs-only — no product divergence. Upstream tests 33/33 in fresh venv; 8 execution
probes at pin.
Status: **all 3 NEW findings APPROVED** (MASH-101 held at S2 with a recorded escalation
condition).
Gate: distiller PASS required before the filing card (t_31448dcb) runs. Issues only (Rule D).
Open-PR check (operator requirement): biondogs/mash has two open PRs — #29 covers the
ALREADY-FILED MASH-013 (fork issue #13), #30 touches only do_foreach (line 362) and
touches none of the NEW findings' evidence. No NEW finding is covered; upstream's only
open PR (#17) is docs.

## A. New issues to file (3)

### MASH-101 — labels: `bug,s2-functional,review-found`
Title: `[S2] Script text is compiled as an unsandboxed Jinja2 template`

```text
symptom: A .mash script executes arbitrary Python with the invoking user's full
permissions while reading as a plain command script: every command line, foreach
body and backtick expression renders as a template, invisibly — the API key in the
config is readable from the payload.
evidence: src/mash/app.py:467-473 — renderString builds a plain jinja2
Environment(loader=BaseLoader, autoescape=False) and calls from_string().render();
used by precmd (:648) and do_endforeach (:430). Execution-verified at the pin: a
__class__/__mro__ payload returned 513 reachable subclasses; a __globals__ payload
returned the platform string.
root cause: Untrusted script text treated as a trusted template; Jinja2 is
Turing-complete and walks object graphs unless sandboxed.
proposed fix: Render with jinja2.sandbox.SandboxedEnvironment (safe filters, no
attribute-walking into unsafe internals) and document that let/foreach only
interpolate variables.
severity: S2 — silent full-privilege execution from the shared script format;
escalates to S1 if mash scripts are ever fetched or executed remotely (SCR-009
conditional-severity precedent).
```

### MASH-102 — labels: `bug,s3-robustness,review-found`
Title: `[S3] GET and DELETE query values are concatenated unencoded into the query string`

```text
symptom: retrieve/delete silently issue a different query than the one typed when a
value contains a reserved character: 'retrieve systems hostname=a&ipaddress=1.2.3.4'
sends an extra ipaddress filter; a value with a space or '#' becomes a second bogus
parameter. Values rendered from MPROV_RESULT server data via foreach hit the same
path, so response text corrupts the next request with no warning — which can feed a
destructive foreach.
evidence: src/mash/app.py:572-580 — each whole token including its value is appended
verbatim to queryString (:580); nothing URL-encodes it.
root cause: Hand-built query string instead of passing a mapping to requests.
proposed fix: Parse tokens into a key-value mapping and pass it as the params
argument of session.get/session.delete (or urlencode each value with urllib.parse),
rejecting tokens that are not key=value before building the request. Independent of
issue #16's validation gap.
severity: S3 — silent request corruption under ordinary-but-special inputs.
```

### MASH-103 — labels: `bug,s4-hygiene,review-found`
Title: `[S4] Plugin output and plugin help bypass the shell's redirectable stdout`

```text
symptom: Plugin output and plugin help cannot be captured: backtick capture
(`let x=`bmc help power``) yields an empty variable, and quiet script mode still emits
plugin help to the terminal. Execution-verified at the pin: do_help put the connect
docstring on the shell's stdout but echoed the argument to process stdout; plugin
help bypasses the shell's stream entirely.
evidence: src/mash/app.py:132-146 (do_help prints directly);
src/mash/plugins/bmc.py:9-14 (PluginCMD constructed without stdin/stdout, so cmd.Cmd
binds the plugin's stdout to the process stdout).
root cause: The plugin's cmd.Cmd never receives the owning shell's streams.
proposed fix: Pass the shell's stdin/stdout into the plugin's cmd.Cmd constructor
(super().__init__(stdin=…, stdout=…)) or make plugins print through the shell's print
helper, and replace do_help's print calls with self.print.
severity: S4 — lost captures and non-quiet script mode; no destructive risk.
```

## B. Verdicts — no other new filings

All 3 NEW findings approved. MASH-102 stays separate from issue #16 (different defect
class: encoding vs validation). No cross-repo dedupes: MASH-101/102/103 have no
counterpart in the other three registers.

## C. Existing fork issue actions (MASH #1–#28)

- **Close by comment (4, fixed upstream at 36b6a5e)**:
  - #1 (MASH-001 connect username/password form) — upstream 413d39c "Fix connect's
    username/password form" (refs mprov-ng/mash#15); forms parse correctly at head,
    tests/test_connect.py added; probe clean.
  - #12 (MASH-012 argv script preference / missing file) — upstream ccfe0a9 (refs
    mprov-ng/mash#9); argv script wins over piped stdin, missing file now
    `mash: <path>: <reason>` exit 1.
  - #19 (MASH-019 help/config lookup messaging) — upstream c9608f6 (refs
    mprov-ng/mash#7); help lists the three real files, load_config reports each path.
  - #23 (MASH-023 CI modernization) — ci.yml modernized by 20a4069 (checkout@v7,
    setup-python@v7), $GITHUB_ENV conversion, SHA-pinned publish + dry-run (76f1d2),
    dependabot.yml (98c5e8c).
- **COVERED-BY-OPEN-PR — do not comment as still-live**:
  - #13 (MASH-013 mapping-shaped config crash): fork PR **biondogs/mash#29** is open
    and explicitly fixes this mechanism (PR test file cites MASH-013; accepts
    mapping-shaped configs and reports config errors cleanly). Per the standing
    operator requirement: drop the planned "still-live" comment; instead optionally
    leave a pointer-comment on PR #29 noting issue #13 tracks the same defect and can
    close when the PR merges.
- **Still-live / still-relevant (24)**: #2–#11, #14–#18, #20–#22, #24–#28 — no new
  filing; optionally a one-line "still present at 36b6a5e" comment each (probe
  receipts in the sweep's REVIEW-NOTES status table).
