#!/usr/bin/env python3
"""Classify mixed-bank memories by hardware environment (read-only).

Attribution precedence:
  1. metadata.agent_identity prefix (g01-/g02-/sj-/sjp-/gaudi-/q38p-)
  2. keyword regex over text+entities (env names, hostnames, hardware)
  3. 'unknown'
"""
import json
import re
import urllib.request
import urllib.parse
from collections import Counter

API = "http://ga01:8888/v1/default/banks"

ENV_BY_ID = {
    "g01": "g01", "g02": "g02", "sj": "sj", "sjp": "sjp",
    "gaudi": "gaudi", "q38p": "q38p-legacy",
}

KEYWORDS = {
    "g01": r"gargantua01|garg-01|\bg01\b|gh-?01|prototype k8s",
    "g02": r"gargantua02|\bg02\b|azure vm[s ]|vm[- ]?(413|414|415|416|417|418)|\bq38-nothink\b|orb\.arch",
    "sj": r"skipjack(?![- ]proto)|\bsj[- ]|mgmt02",
    "sjp": r"skipjack[- ]proto|sjp|gh-?20[78]",
    "gaudi": r"gaudi|habana|hpu|synapse|hl-?\d{3}|ga01",
    "q38p-legacy": r"q38p|qwen38[- ]perf|qwen[- ]?38|flashnext",
}
KW = {k: re.compile(rx, re.I) for k, rx in KEYWORDS.items()}


def fetch(bank, offset):
    url = f"{API}/{urllib.parse.quote(bank)}/memories/list?limit=1000&offset={offset}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r).get("items", [])


for bank in ["hb-infra-release", "hb-inference-bench", "Hermes q38"]:
    by_id = Counter()
    by_kw = {}
    unknown_kw_hits = Counter()
    total = 0
    offset = 0
    while True:
        items = fetch(bank, offset)
        if not items:
            break
        for m in items:
            total += 1
            ident = (m.get("metadata") or {}).get("agent_identity") or ""
            if ident:
                for pfx, env in ENV_BY_ID.items():
                    if ident.startswith(pfx + "-") or ident == pfx:
                        by_id[env] += 1
                        break
                else:
                    by_id["id:" + ident] += 1
                continue
            # unknown identity -> keyword classify
            text = (m.get("text", "") + " " + (m.get("entities") or ""))
            hits = [e for e, rx in KW.items() if rx.search(text)]
            if len(hits) == 1:
                by_id["unknown-id->" + hits[0]] += 1
            elif len(hits) == 0:
                by_id["unknown-id->none"] += 1
            else:
                by_id["unknown-id->ambiguous:" + "+".join(sorted(hits))] += 1
        offset += 1000
        if len(items) < 1000:
            break
    print(f"=== {bank} (total {total})")
    for k, c in by_id.most_common():
        print(f"  {k}: {c}")
