#!/usr/bin/env python3
"""Mechanical circumscription/schema validator for mProv findings registers.

Usage:
  validate_register.py REGISTER --repo-path <local clone> [--skip-evidence]

Enforces the structural half of ../CIRCUMSCRIPTION.md + FILE-PLAN.md §3.
Judgment checks (S1 scenario naming, causal-path tracing, obvious-bar,
dedupe, severity calibration) remain adjudication's job.
Exit 0 = all checks pass; 1 = violations listed on stdout.
Requires PyYAML.
"""
import argparse
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required (pip install --user pyyaml)")
    sys.exit(2)

REPO_PREFIX = {
    "mprov_control_center": "CC",
    "mprov_jobserver": "JS",
    "mprov_scripts": "SCR",
    "mash": "MASH",
}
HEADER_KEYS = {"repo", "branch", "commit", "reviewed_at", "reviewer", "coverage"}
COVERAGE_KEYS = {"files_reviewed", "files_total", "method"}
FINDING_KEYS = {
    "id", "type", "severity", "title", "user_value",
    "evidence", "repro", "fix_idea", "blast_radius", "regression_test",
}
EVIDENCE_KEYS = {"path", "lines", "excerpt"}
TITLE_RE = re.compile(r"^[A-Z].{2,78}$")
ID_RE = re.compile(r"^[A-Z]{2,4}-\d{3}$")
CODE_LINE_RE = re.compile(r"[;{}]$")

errors = []


def err(rule, fid, msg):
    errors.append(f"[{rule}] {fid}: {msg}")


def norm(s):
    return " ".join(str(s).split())


def git_show(repo_path, commit, path):
    r = subprocess.run(
        ["git", "-C", repo_path, "show", f"{commit}:{path}"],
        capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def check_finding(f, idx, prefix, repo_path, commit, skip_evidence):
    fid = f.get("id") or f"FINDING#{idx}"
    if not isinstance(fid, str) or not ID_RE.match(fid):
        err("id-format", fid, f"id must match {ID_RE.pattern}")
    elif prefix and not fid.startswith(prefix + "-"):
        err("id-prefix", fid, f"id must use prefix {prefix}- for this repo")

    extra = set(f) - FINDING_KEYS
    missing = FINDING_KEYS - set(f)
    if extra:
        err("schema", fid, f"extra keys: {sorted(extra)}")
    if missing:
        err("schema", fid, f"missing keys: {sorted(missing)}")
        return  # can't check fields that don't exist

    if f["type"] not in ("bug", "enhancement"):
        err("R12", fid, "type must be bug|enhancement")
    if f["severity"] not in ("S1", "S2", "S3", "S4"):
        err("R12", fid, "severity must be S1..S4")

    title = str(f["title"])
    if not TITLE_RE.match(title):
        err("R2", fid, "title must start uppercase, be 3..79 chars")
    if title.startswith("[S"):
        err("R2", fid, "title must NOT carry the [Sx] prefix in the register")
    if title.endswith("."):
        err("R2", fid, "no trailing period in title")

    if f["type"] == "enhancement":
        uv = f["user_value"]
        if not isinstance(uv, str) or not norm(uv):
            err("R11", fid, "enhancement requires non-empty single-sentence user_value")
        elif "\n" in str(uv).strip() or len(re.findall(r"[.!?]\s", norm(uv))) > 0 and norm(uv).count(".") > 1:
            err("R11", fid, "user_value must be ONE sentence")
    elif f["user_value"] is not None:
        err("R11", fid, "user_value must be null for bugs")

    for field in ("repro", "fix_idea", "blast_radius", "regression_test"):
        v = f[field]
        if not isinstance(v, str) or not norm(v):
            err("R4-7", fid, f"field {field} must be non-empty prose")
    fix = str(f.get("fix_idea", ""))
    if "```" in fix:
        err("R5", fid, "fix_idea contains fenced code — prose only")
    for line in fix.splitlines():
        ls = line.strip()
        if ls.startswith(("--- ", "+++ ", "@@ ")):
            err("R5", fid, f"fix_idea contains diff marker: {ls[:40]}")
            break
        if ls and CODE_LINE_RE.search(ls):
            err("R5", fid, f"fix_idea contains code-looking line: {ls[:40]}")
            break

    ev = f["evidence"]
    if not isinstance(ev, list) or not ev:
        err("R8", fid, "evidence must be a non-empty list")
        return
    for site in ev:
        if not isinstance(site, dict):
            err("R8", fid, "evidence site must be a mapping")
            continue
        extra_e = set(site) - EVIDENCE_KEYS
        missing_e = EVIDENCE_KEYS - set(site)
        if extra_e or missing_e:
            err("R8", fid, f"evidence site keys wrong: extra={sorted(extra_e)} missing={sorted(missing_e)}")
            continue
        path, lines, excerpt = site["path"], site["lines"], site["excerpt"]
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", str(lines))
        if not m:
            err("R3", fid, f"{path}: lines must be N or N-N")
            continue
        if not isinstance(excerpt, str) or not norm(excerpt):
            err("R3", fid, f"{path}: excerpt must be non-empty verbatim source")
            continue
        if skip_evidence:
            continue
        if repo_path is None:
            err("R3", fid, "--repo-path required for evidence verification")
            continue
        src = git_show(repo_path, commit, path)
        if src is None:
            err("R3", fid, f"{path}: does not exist at commit {commit}")
            continue
        src_lines = src.splitlines()
        start = int(m.group(1))
        end = int(m.group(2) or m.group(1))
        if end < start:
            err("R3", fid, f"{path}: lines range inverted")
            continue
        if end > len(src_lines):
            err("R3", fid, f"{path}: lines end {end} beyond file ({len(src_lines)} lines)")
            continue
        lo, hi = max(0, start - 3), min(len(src_lines), end + 2)
        window = norm("\n".join(src_lines[lo:hi]))
        if norm(excerpt) not in window:
            err("R3", fid, f"{path}:{lines}: excerpt not found verbatim near cited lines")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("register")
    ap.add_argument("--repo-path")
    ap.add_argument("--skip-evidence", action="store_true",
                    help="skip git-based excerpt verification")
    args = ap.parse_args()

    with open(args.register) as fh:
        try:
            doc = yaml.safe_load(fh)
        except yaml.YAMLError as e:
            print(f"FAIL: register does not parse: {e}")
            sys.exit(1)

    if not isinstance(doc, dict) or set(doc) != {"review", "findings"}:
        print("FAIL: top level must be exactly keys: review, findings")
        sys.exit(1)

    review = doc["review"]
    if set(review) != HEADER_KEYS:
        print(f"FAIL: review header keys wrong: {sorted(review)}")
        sys.exit(1)
    cov = review["coverage"]
    if set(cov) != COVERAGE_KEYS or not all(
            isinstance(cov[k], int) for k in ("files_reviewed", "files_total")):
        print("FAIL: coverage needs int files_reviewed/files_total + method")
        sys.exit(1)

    findings = doc["findings"]
    if not isinstance(findings, list):
        print("FAIL: findings must be a list")
        sys.exit(1)

    prefix = REPO_PREFIX.get(review["repo"])
    seen = set()
    for i, f in enumerate(findings, 1):
        if f.get("id") in seen:
            err("R1", f.get("id"), "duplicate id")
        seen.add(f.get("id"))
        check_finding(f, i, prefix, args.repo_path, review["commit"], args.skip_evidence)

    tally = {}
    types = {}
    for f in findings:
        tally[f.get("severity")] = tally.get(f.get("severity"), 0) + 1
        types[f.get("type")] = types.get(f.get("type"), 0) + 1

    print(f"register: {args.register}")
    print(f"repo: {review['repo']} @ {review['commit']}  findings: {len(findings)}")
    print(f"tally: {dict(sorted(tally.items()))}  types: {dict(sorted(types.items()))}")
    if errors:
        print(f"\nVIOLATIONS ({len(errors)}):")
        for e in errors:
            print("  " + e)
        sys.exit(1)
    print("PASS: all mechanical checks clean")


if __name__ == "__main__":
    main()
