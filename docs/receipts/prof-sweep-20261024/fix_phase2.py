#!/usr/bin/env python3
"""PROF-SWEEP-OPT phase 2: surgical fixes with triple guards.
Backups -> ~/.hermes/config-backups/prof-sweep-20261024T024500Z/
Fixes:
  F1: aux raw-text splice to byte-identical root `auxiliary:` (59 profiles, only where raw differs)
  F2: strip dead `skills: always_load: []` from 5 butlers
  F3: context_length repins (9x 1000000->262144, sw-architect/sw-reviewer 262144->1000000)
NO credential/bank/plugin/_config_version mutations (escalated instead).
"""
import os, re, yaml, shutil

HOME = '/home/arch/.hermes'
PROF = os.path.join(HOME, 'profiles')
SRC = os.path.join(HOME, 'config.yaml')
BAK = os.path.join(HOME, 'config-backups', 'prof-sweep-20261024T024500Z')
os.makedirs(BAK, exist_ok=True)

def extract(text, key):
    lines = text.split('\n')
    idxs = [i for i, ln in enumerate(lines) if ln.startswith(key + ':')]
    assert len(idxs) == 1, f'{key} appears {len(idxs)}x'
    start = idxs[0]
    out = [lines[start]]
    for ln in lines[start + 1:]:
        if ln.startswith(' ') or ln.startswith('\t') or ln.strip() == '' or ln.startswith('#'):
            out.append(ln)
        else:
            break
    return '\n'.join(out)

def splice_raw(raw, key, block_lines):
    lines = raw.split('\n')
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(key + ':'):
            start = i
            break
    assert start is not None
    end = start + 1
    while end < len(lines):
        ln = lines[end]
        if ln.strip() == '' or ln[0] in ' \t' or ln.lstrip().startswith('#'):
            end += 1
            continue
        break
    return '\n'.join(lines[:start] + block_lines + lines[end:])

def guarded_write(profile, raw, new_raw, reason, expect=None):
    before = yaml.safe_load(raw)
    after = yaml.safe_load(new_raw)
    if after is None:
        print(f'  FAIL {profile} {reason}: parse')
        return False
    if expect is not None:
        if not expect(before, after):
            print(f'  FAIL {profile} {reason}: expectation check failed')
            return False
    else:
        if before != after:
            print(f'  FAIL {profile} {reason}: PARSED-DIFFERS-BEYOND-TARGET')
            return False
    if not new_raw.endswith('\n'):
        new_raw += '\n'
    cfg = os.path.join(PROF, profile, 'config.yaml')
    tmp = f'/tmp/prof-sweep-{profile}.yaml'
    with open(tmp, 'w') as f:
        f.write(new_raw)
    yaml.safe_load(open(tmp))
    shutil.copy(cfg, os.path.join(BAK, f'{profile}.config.yaml'))
    shutil.move(tmp, cfg)
    return True

root_raw = open(SRC).read()
root_aux = extract(root_raw, 'auxiliary')
root_aux_block = root_aux.split('\n')
root_aux_dict = yaml.safe_load(root_aux)['auxiliary']

def f1_aux():
    fixed = skipped = 0
    for d in sorted(os.listdir(PROF)):
        cfg = os.path.join(PROF, d, 'config.yaml')
        if not os.path.isfile(cfg):
            continue
        raw = open(cfg).read()
        try:
            pa = extract(raw, 'auxiliary')
        except AssertionError as e:
            print(f'  F1 SKIP {d}: {e}')
            continue
        if pa == root_aux:
            skipped += 1
            continue
        # guards: dict already equal (semantics unchanged), then splice raw text
        dprof = yaml.safe_load(raw) or {}
        if dprof.get('auxiliary') != root_aux_dict:
            print(f'  F1 SKIP {d}: aux dict NOT equal — refusing raw splice (investigate)')
            continue
        new_raw = splice_raw(raw, 'auxiliary', root_aux_block)
        # post: raw-extracted aux must equal root raw exactly
        if extract(new_raw, 'auxiliary') != root_aux:
            print(f'  FAIL {d}: post-splice aux not byte-identical (untouched)')
            continue
        if guarded_write(d, raw, new_raw, 'aux-splice'):
            fixed += 1
    print(f'F1 aux byte-identity: fixed={fixed} already-ok={skipped}')

def f2_butlers():
    for p in ['g01-butler', 'g02-butler', 'gaudi-butler', 'sjproto-butler', 'swco-butler']:
        cfg = os.path.join(PROF, p, 'config.yaml')
        raw = open(cfg).read()
        m = re.search(r'^skills:\n(?:  [^\n]*\n)*?  always_load: \[\]\n(?:  [^\n]*\n)*', raw, re.M)
        if not m:
            print(f'  F2 {p}: pattern not found — inspect manually')
            continue
        block = m.group(0)
        rem = block.replace('always_load: []\n', '')
        # if only 'skills:\n' remains, drop the whole block
        if rem.strip() == 'skills:':
            new_raw = raw.replace(block, '')
        else:
            new_raw = raw.replace(block, rem)
        before = yaml.safe_load(raw) or {}
        if isinstance(before.get('skills'), dict) and list(before['skills'].keys()) != ['always_load']:
            print(f'  F2 {p}: skills has other keys {list(before["skills"].keys())} — remove only the one line')
            new_raw = raw.replace('  always_load: []\n', '', 1)
        def _exp2(b, a, _p=p):
            exp = {k: v for k, v in (b or {}).items() if k != 'skills'}
            sk = (b or {}).get('skills')
            if isinstance(sk, dict) and list(sk.keys()) != ['always_load']:
                exp['skills'] = {k: v for k, v in sk.items() if k != 'always_load'}
            return a == exp
        ok = guarded_write(p, raw, new_raw, 'always_load-strip', expect=_exp2)
        print(f'  F2 {p}: {"done" if ok else "FAILED"}')

CTX_FIX = {
    'g01-ops': ('1000000', '262144'), 'g01-watcher': ('1000000', '262144'),
    'g02-ops': ('1000000', '262144'), 'g02-watcher': ('1000000', '262144'),
    'gaudi-watcher': ('1000000', '262144'), 'sj-ops': ('1000000', '262144'),
    'sj-watcher': ('1000000', '262144'), 'sjp-ops': ('1000000', '262144'),
    'sjp-watcher': ('1000000', '262144'),
    'sw-architect': ('262144', '1000000'), 'sw-reviewer': ('262144', '1000000'),
}

def f3_ctx():
    for p, (old, new) in CTX_FIX.items():
        cfg = os.path.join(PROF, p, 'config.yaml')
        raw = open(cfg).read()
        # find the model: section and its context_length line
        lines = raw.split('\n')
        mi = next(i for i, ln in enumerate(lines) if ln == 'model:')
        ci = None
        for j in range(mi + 1, len(lines)):
            if lines[j].startswith('  context_length:') and lines[j].rstrip().endswith(old):
                ci = j
                break
            if lines[j] and not lines[j].startswith(' '):
                break
        if ci is None:
            print(f'  F3 {p}: context_length line w/ {old} not found')
            continue
        lines[ci] = lines[ci].replace(old, new)
        new_raw = '\n'.join(lines)
        def _exp3(b, a, _p=p, _new=int(new), _old=int(old)):
            b2, a2 = dict(b), dict(a)
            bm, am = dict(b2.get('model') or {}), dict(a2.get('model') or {})
            if bm.get('context_length') != _old:
                return False
            bm['context_length'] = _new
            b2['model'], a2['model'] = bm, am
            return a2 == b2
        ok = guarded_write(p, raw, new_raw, 'ctx-repin', expect=_exp3)
        print(f'  F3 {p}: {old}->{new} {"done" if ok else "FAILED"}')

f1_aux()
f2_butlers()
f3_ctx()
print('DONE. Backups at', BAK)
