#!/usr/bin/env python3
"""PROF-SWEEP-OPT phase 1: read-only fleet audit against 2026-10-23 canon.
No mutations. Outputs JSON drift report + human drift table.
"""
import os, re, json, hashlib, glob

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML missing")

HOME = '/home/arch/.hermes'
PROFILES = os.path.join(HOME, 'profiles')
ROOT_CFG = os.path.join(HOME, 'config.yaml')
OUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit-drift.json')

def sha12(v):
    return hashlib.sha256(v.encode()).hexdigest()[:12]

def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()

def parse_yaml(text):
    try:
        return yaml.safe_load(text), None
    except Exception as e:
        return None, str(e)

def extract_top_section(text, key):
    """Line-scanner extraction of a column-0 top-level YAML section. Returns raw text."""
    lines = text.split('\n')
    start = None
    for i, ln in enumerate(lines):
        if ln.rstrip() == f'{key}:' or ln.startswith(f'{key}:'):
            if ln.startswith(key + ':'):
                start = i
                break
    if start is None:
        return None
    out = [lines[start]]
    for ln in lines[start + 1:]:
        if ln.startswith(' ') or ln.startswith('\t') or ln.strip() == '' or ln.startswith('#'):
            out.append(ln)
        else:
            break
    return '\n'.join(out)

def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    for ln in read(path).split('\n'):
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=(.*)$', ln)
        if m:
            env[m.group(1)] = m.group(2)
    return env

def env_keys(path):
    ks = set()
    if not os.path.exists(path):
        return ks
    for ln in read(path).split('\n'):
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=', ln)
        if m:
            ks.add(m.group(1))
        m2 = re.match(r'^#\s*([A-Za-z_][A-Za-z0-9_]*)=', ln)
        if m2:
            ks.add('#' + m2.group(1))  # commented-out marker
    return ks

# ---------- canon definitions ----------
BUTLER_BOARD = {
    'g01-butler': 'gargantua01',
    'g02-butler': 'gargantua02',
    'gaudi-butler': 'gaudi',
    'sjproto-butler': 'skipjack-prototype',
    'swco-butler': 'software-co',
}
BUTLERS = list(BUTLER_BOARD)

# BANK-MAP.md expected effective banks (hindsight/config.json bank_id)
BANK_MAP = {
    # env banks
    'g01-orchestrator': 'g01-infra', 'g01-planner': 'g01-infra', 'g01-auditor': 'g01-infra',
    'g01-scribe': 'g01-infra', 'g01-ops': 'g01-infra', 'g01-watcher': 'g01-infra',
    'g02-orchestrator': 'g02-infra', 'g02-planner': 'g02-infra', 'g02-auditor': 'g02-infra',
    'g02-scribe': 'g02-infra', 'g02-ops': 'g02-infra', 'g02-watcher': 'g02-infra',
    'sj-orchestrator': 'skipjack-infra', 'sj-planner': 'skipjack-infra', 'sj-auditor': 'skipjack-infra',
    'sj-scribe': 'skipjack-infra', 'sj-ops': 'skipjack-infra', 'sj-watcher': 'skipjack-infra',
    'sjp-orchestrator': 'skipjack-prototype-infra', 'sjp-planner': 'skipjack-prototype-infra',
    'sjp-auditor': 'skipjack-prototype-infra', 'sjp-scribe': 'skipjack-prototype-infra',
    'sjp-ops': 'skipjack-prototype-infra', 'sjp-watcher': 'skipjack-prototype-infra',
    'gaudi-orchestrator': 'gaudi-hpu', 'gaudi-planner': 'gaudi-hpu', 'gaudi-auditor': 'gaudi-hpu',
    'gaudi-scribe': 'gaudi-hpu', 'gaudi-deployer': 'gaudi-hpu',
    # gaudi role banks
    'gaudi-analyst': 'gaudi-hpu-perf', 'gaudi-benchrunner': 'gaudi-hpu-perf', 'gaudi-watcher': 'gaudi-hpu-perf',
    'gaudi-arch': 'gaudi-hpu-sdk', 'gaudi-perfeng': 'gaudi-hpu-sdk', 'gaudi-synapse': 'gaudi-hpu-sdk',
    'gaudi-dockerops': 'gaudi-hpu-hostops', 'gaudi-sysadmin': 'gaudi-hpu-hostops',
    'gaudi-liaison': 'gaudi-hpu-upstream',
    # kanban/specialist lanes
    'kanban-orchestrator': 'hb-orchestrator',
    'kanban-board-architect': 'hb-architect',
    'kanban-worker': 'hb-kanban-worker',
    'research': 'hb-research',
    'distiller': 'hb-distiller',
    'sampling-test': 'hb-sampling-test',
    # software-co fleet
    'sw-architect': 'software-co', 'sw-dev-a': 'software-co', 'sw-dev-b': 'software-co',
    'sw-devops': 'software-co', 'sw-docs': 'software-co', 'sw-pm': 'software-co',
    'sw-qa': 'software-co', 'sw-reviewer': 'software-co', 'sw-ux': 'software-co',
    # butlers (own banks)
    'g01-butler': 'g01-butler', 'g02-butler': 'g02-butler', 'gaudi-butler': 'gaudi-butler',
    'sjproto-butler': 'sjproto-butler', 'swco-butler': 'swco-butler',
    # root
    '__root__': 'hermes',
}
HUSKS = {'coding', 'kworker-muse-probe', 'plugin-ab'}  # no hindsight wiring per BANK-MAP rule 3

MUSE_PROFILES = ['kanban-worker', 'g01-scribe', 'g02-scribe', 'sw-dev-a', 'sw-dev-b',
                 'sw-devops', 'sw-docs', 'sw-qa']

EXPECT_WINDOW = {'qwen38': 1000000, 'qwen38-flash-fp8': 262144, 'glm53': 1000000, 'qwen36-fast': 131072}

root_text = read(ROOT_CFG)
root_cfg, root_err = parse_yaml(root_text)
root_aux_raw = extract_top_section(root_text, 'auxiliary')
root_aux_dict = (root_cfg or {}).get('auxiliary')

report = {'root': [], 'profiles': {}}
drift_rows = []  # (profile, check, detail, severity)

def add(profile, check, detail, severity='WARN'):
    drift_rows.append({'profile': profile, 'check': check, 'detail': detail, 'severity': severity})
    target = report if profile == '__root__' else None
    report['root' if profile == '__root__' else 'profiles'].setdefault(
        profile if profile != '__root__' else 'root', []).append(
        {'check': check, 'detail': detail, 'severity': severity})

# ---------- root checks ----------
if root_err:
    add('__root__', 'yaml.parse', root_err, 'CRIT')
root_prov = (root_cfg or {}).get('providers')
if not isinstance(root_prov, dict) or not root_prov.get('litellm'):
    add('__root__', 'providers', 'root providers.litellm missing/malformed', 'CRIT')
else:
    models = root_prov['litellm'].get('models', {}) or {}
    exp = {'qwen36-fast': ('131072', '32768'), 'qwen38-flash-fp8': ('262144', None), 'glm53': ('1000000', None)}
    for m, (ctx, mt) in exp.items():
        pin = models.get(m)
        if pin is None:
            add('__root__', 'providers.pins', f'root pin for {m} MISSING', 'CRIT')
        else:
            if str(pin.get('context_length')) != ctx:
                add('__root__', 'providers.pins', f'root {m} context_length={pin.get("context_length")} expected={ctx}', 'CRIT')
            if mt and str(pin.get('max_tokens')) != mt:
                add('__root__', 'providers.pins', f'root {m} max_tokens={pin.get("max_tokens")} expected={mt}', 'CRIT')
if (root_cfg or {}).get('custom_providers'):
    add('__root__', 'providers', 'legacy custom_providers: present', 'CRIT')
if (root_cfg or {}).get('fallback_providers'):
    add('__root__', 'fallback', 'fallback_providers present', 'CRIT')
if (root_cfg or {}).get('timezone') != 'America/New_York':
    add('__root__', 'timezone', f"root timezone={ (root_cfg or {}).get('timezone')!r}", 'WARN')

# root aux compression
comp = ((root_cfg or {}).get('auxiliary') or {}).get('compression') or {}
if (comp.get('model'), comp.get('provider'), comp.get('reasoning_effort')) != ('qwen36-fast', 'litellm', 'none'):
    add('__root__', 'aux.compression', f'root compression={comp}', 'CRIT')

# no other aux task may have a wrong shape — record root aux dict for byte compare
EXPECT_AUX = {t: (v.get('provider'), v.get('model'), v.get('reasoning_effort'))
              for t, v in root_aux_dict.items()}

# ---------- cred inventory (read-only) ----------
def audit_creds(scope, env_path, cfg, cfg_env_present):
    """Returns findings for one .env + its config."""
    f = []
    env = load_env(env_path)
    has_tg = 'TELEGRAM_BOT_TOKEN' in env
    has_slack = ('SLACK_BOT_TOKEN' in env) or ('SLACK_APP_TOKEN' in env)
    is_root = scope == '__root__'
    is_butler = scope in BUTLERS
    if has_slack and not is_root:
        f.append(('creds.slack', f'{scope}: SLACK creds present outside default', 'CRIT'))
    if has_tg and not (is_root or is_butler):
        f.append(('creds.telegram', f'{scope}: TELEGRAM_BOT_TOKEN outside default+butlers', 'CRIT'))
    return f, env

tg_tokens = {}
telegram_holders = []
slack_holders = []

# ---------- iterate all profile dirs ----------
prof_names = sorted(d for d in os.listdir(PROFILES) if os.path.isdir(os.path.join(PROFILES, d)))
report['fleet_size'] = len(prof_names)

for name in prof_names:
    pdir = os.path.join(PROFILES, name)
    cfg_path = os.path.join(pdir, 'config.yaml')
    if not os.path.exists(cfg_path):
        drift_rows.append({'profile': name, 'check': 'orphan', 'detail': 'config.yaml MISSING', 'severity': 'CRIT'})
        report['profiles'][name] = [{'check': 'orphan', 'detail': 'config.yaml MISSING', 'severity': 'CRIT'}]
        continue
    text = read(cfg_path)
    cfg, err = parse_yaml(text)
    issues = []
    if err:
        issues.append({'check': 'yaml.parse', 'detail': err, 'severity': 'CRIT'})
        report['profiles'][name] = issues
        continue
    cfg = cfg or {}

    # --- hygiene: forbidden keys ---
    if isinstance(cfg.get('skills'), dict) and 'always_load' in cfg['skills']:
        issues.append({'check': 'skills.always_load', 'detail': 'dead key present', 'severity': 'WARN'})
    for key in ('_config_version', 'plugins'):
        if key in cfg:
            issues.append({'check': key, 'detail': f'{key}: present in profile (global-only)', 'severity': 'WARN'})
    if 'fallback_providers' in cfg:
        issues.append({'check': 'fallback_providers', 'detail': 'fallback_providers present', 'severity': 'CRIT'})
    if 'model' in cfg and 'ssl_verify' in cfg['model']:
        issues.append({'check': 'model.ssl_verify', 'detail': 'ignored in model:', 'severity': 'WARN'})
    if not cfg.get('agent', {}).get('description'):
        issues.append({'check': 'agent.description', 'detail': 'MISSING (kanban routing needs it)', 'severity': 'CRIT'})
    if not cfg.get('model', {}).get('default'):
        issues.append({'check': 'model.default', 'detail': 'MISSING', 'severity': 'WARN'})

    # --- kanban keys in profiles (superseded rule: kanban.board allowed on butlers only) ---
    kan = cfg.get('kanban')
    if kan is not None:
        if name in BUTLER_BOARD:
            if kan.get('board') != BUTLER_BOARD[name]:
                issues.append({'check': 'kanban.board', 'detail': f'butler pin={kan.get("board")!r} expected={BUTLER_BOARD[name]!r}', 'severity': 'CRIT'})
            extra = [k for k in kan if k != 'board']
            if extra:
                issues.append({'check': 'kanban.section', 'detail': f'extra kanban keys beyond board: {extra}', 'severity': 'WARN'})
        else:
            issues.append({'check': 'kanban.section', 'detail': f'NON-butler profile carries kanban: {json.dumps(kan, default=str)[:200]}', 'severity': 'CRIT' if (kan.get('board') or kan) else 'NOTE'})

    # --- providers ---
    prov = cfg.get('providers')
    if 'custom_providers' in cfg:
        issues.append({'check': 'custom_providers', 'detail': 'legacy list present (v46 wants providers: dict)', 'severity': 'CRIT'})
    if not isinstance(prov, dict) or not prov.get('litellm'):
        issues.append({'check': 'providers.litellm', 'detail': 'providers.litellm MISSING in profile', 'severity': 'CRIT'})
    else:
        lml = prov['litellm'] or {}
        if lml.get('api') and 'orb.arch.jhu.edu' not in str(lml.get('api')) and 'ga01' not in str(lml.get('api')):
            issues.append({'check': 'providers.litellm.api', 'detail': f'unexpected api={lml.get("api")}', 'severity': 'WARN'})
        for m, pin in (lml.get('models') or {}).items():
            if m in EXPECT_WINDOW:
                if str(pin.get('context_length')) != str(EXPECT_WINDOW[m]):
                    issues.append({'check': 'providers.pins', 'detail': f'{m} context_length={pin.get("context_length")} expected={EXPECT_WINDOW[m]}', 'severity': 'CRIT'})

    # --- aux block ---
    aux_raw = extract_top_section(text, 'auxiliary')
    aux = cfg.get('auxiliary')
    if aux is None:
        issues.append({'check': 'aux', 'detail': 'auxiliary block MISSING', 'severity': 'CRIT'})
    else:
        if aux != root_aux_dict:
            diff = {t: (EXPECT_AUX.get(t), (aux[t].get('provider'), aux[t].get('model'), aux[t].get('reasoning_effort')))
                    for t in set(EXPECT_AUX) | set(aux)
                    if (t not in aux) or (t not in EXPECT_AUX) or
                       (aux[t].get('provider'), aux[t].get('model'), aux[t].get('reasoning_effort')) != EXPECT_AUX[t]}
            issues.append({'check': 'aux.dict', 'detail': f'aux DICT differs from root: {json.dumps(diff, default=str)[:400]}', 'severity': 'CRIT'})
        def _norm(block):
            b = block.split('\n')
            while b and b[-1].strip() == '':
                b.pop()
            return '\n'.join(b)
        if _norm(aux_raw) != _norm(root_aux_raw):
            issues.append({'check': 'aux.bytes', 'detail': 'aux TEXT not byte-identical to root (dict equal)'if aux == root_aux_dict else 'aux TEXT not byte-identical', 'severity': 'CRIT' if aux != root_aux_dict else 'NOTE'})
        c = (aux.get('compression') or {})
        if (c.get('model'), c.get('provider'), c.get('reasoning_effort')) != ('qwen36-fast', 'litellm', 'none'):
            issues.append({'check': 'aux.compression', 'detail': f'compression={c}', 'severity': 'CRIT'})

    # --- muse lane ---
    model = cfg.get('model') or {}
    default = model.get('default')
    if name in MUSE_PROFILES:
        if default != 'muse':
            issues.append({'check': 'muse.wired', 'detail': f'muse-lane profile default={default!r}, expected muse', 'severity': 'CRIT'})
        if str(model.get('context_length')) != '262144':
            issues.append({'check': 'muse.wired', 'detail': f'context_length={model.get("context_length")!r}, expected 262144', 'severity': 'CRIT'})
        fm = cfg.get('fallback_model')
        fm_str = json.dumps(fm, default=str) if fm else ''
        if not fm or 'qwen38-flash-fp8' not in fm_str:
            issues.append({'check': 'muse.fallback', 'detail': f'fallback_model missing/wrong: {fm_str[:200]}', 'severity': 'CRIT'})
    else:
        if default == 'muse':
            issues.append({'check': 'muse.notwired', 'detail': 'NON muse-lane profile has default=muse', 'severity': 'CRIT'})
        if default and 'muse' in str(default):
            issues.append({'check': 'muse.notwired', 'detail': f'default references muse: {default}', 'severity': 'CRIT'})

    # --- env var resolution: ${VAR} refs in config.yaml must exist in profile .env or root .env ---
    prof_env = load_env(os.path.join(pdir, '.env'))
    root_env = load_env(os.path.join(HOME, '.env'))
    for var in set(re.findall(r'\$\{([A-Z0-9_]+)\}', text)):
        if var not in prof_env and var not in root_env:
            issues.append({'check': 'env.refs', 'detail': f'${{{var}}} unresolved (not in profile .env nor root .env)', 'severity': 'CRIT'})

    # --- creds (read-only inventory) ---
    env_path = os.path.join(pdir, '.env')
    penv = load_env(env_path)
    if penv.get('SLACK_BOT_TOKEN') or penv.get('SLACK_APP_TOKEN'):
        slack_holders.append(name)
        issues.append({'check': 'creds.slack', 'detail': 'SLACK creds present outside default', 'severity': 'CRIT'})
    if penv.get('TELEGRAM_BOT_TOKEN'):
        telegram_holders.append(name)
        tg_tokens[name] = sha12(penv['TELEGRAM_BOT_TOKEN'])
        if name not in BUTLERS:
            issues.append({'check': 'creds.telegram', 'detail': 'TELEGRAM_BOT_TOKEN outside default+butlers', 'severity': 'CRIT'})
    if name in BUTLERS and 'TELEGRAM_FALLBACK_IPS' not in penv:
        issues.append({'check': 'creds.fallback_ips', 'detail': 'TELEGRAM_FALLBACK_IPS MISSING in butler .env', 'severity': 'CRIT'})
    # slack listener disabled everywhere
    psl = ((cfg.get('platforms') or {}).get('slack') or {})
    if psl.get('enabled') is True:
        issues.append({'check': 'creds.slack_listener', 'detail': 'platforms.slack.enabled true', 'severity': 'CRIT'})

    # --- timezone ---
    tz = cfg.get('timezone')
    if tz is not None and tz != 'America/New_York':
        issues.append({'check': 'timezone', 'detail': f'timezone={tz!r}', 'severity': 'WARN'})

    # --- bank binding ---
    if name not in HUSKS:
        hb_env = os.path.join(pdir, '.env')
        ek = env_keys(hb_env)
        if 'HINDSIGHT_BANK_ID' in ek:
            issues.append({'check': 'bank.env_pin', 'detail': 'HINDSIGHT_BANK_ID SET in .env (would override config.json)', 'severity': 'CRIT'})
        hcj = os.path.join(pdir, 'hindsight', 'config.json')
        if not os.path.exists(hcj):
            issues.append({'check': 'bank.wiring', 'detail': 'hindsight/config.json missing', 'severity': 'WARN'})
        else:
            try:
                hc = json.loads(read(hcj))
                bank = hc.get('bank_id')
                exp = BANK_MAP.get(name)
                if exp is None:
                    issues.append({'check': 'bank.map', 'detail': f'profile not in BANK-MAP expectation; effective bank={bank!r}', 'severity': 'WARN'})
                elif bank != exp:
                    issues.append({'check': 'bank.binding', 'detail': f'bank_id={bank!r}, BANK-MAP expects {exp!r}', 'severity': 'CRIT'})
                banks = hc.get('banks') or {}
                if exp and exp in banks and banks[exp].get('bank_id') not in (None, exp):
                    issues.append({'check': 'bank.carrier', 'detail': f'banks[] carrier mismatch for {exp}: {json.dumps(banks.get(exp))[:150]}', 'severity': 'WARN'})
            except Exception as e:
                issues.append({'check': 'bank.parse', 'detail': str(e), 'severity': 'CRIT'})

    # --- SOUL.md title ---
    soul = os.path.join(pdir, 'SOUL.md')
    if os.path.exists(soul):
        first = read(soul).split('\n', 12)
        title = next((l for l in first if l.startswith('#')), '')
        m = re.match(r'#\s*(.*)', title)
        t = (m.group(1) if m else '').strip().lower()
        core = name.replace('butler', '').strip()
        words = [w for w in core.split('-') if w]
        if t and not (core in t or any(w in t for w in words if len(w) > 2)):
            issues.append({'check': 'soul.title', 'detail': f'SOUL title {title!r} does not mention profile name/role words {words}', 'severity': 'WARN'})
    else:
        issues.append({'check': 'soul.missing', 'detail': 'SOUL.md missing', 'severity': 'WARN'})

    report['profiles'][name] = issues
    drift_rows.extend({'profile': name, **i} for i in issues)

# root creds
renv = load_env(os.path.join(HOME, '.env'))
if renv.get('TELEGRAM_BOT_TOKEN'):
    telegram_holders.append('__root__')
    tg_tokens['__root__'] = sha12(renv['TELEGRAM_BOT_TOKEN'])
# token uniqueness
seen = {}
for name, h in sorted(tg_tokens.items()):
    seen.setdefault(h, []).append(name)
dups = {h: n for h, n in seen.items() if len(n) > 1}
report['cred_inventory'] = {
    'telegram_holders': sorted(telegram_holders),
    'duplicate_token_groups': dups,
    'slack_holders': sorted(slack_holders),
}

with open(OUT_JSON, 'w') as f:
    json.dump(report, f, indent=1, default=str)

# ---------- human drift table ----------
clean = [p for p, iss in report['profiles'].items() if not iss]
print(f"FLEET: {len(prof_names)} profile dirs scanned; clean={len(clean)}; with-findings={len(prof_names)-len(clean)}")
print(f"telegram holders: {sorted(telegram_holders)}")
print(f"duplicate token groups: {dups or 'NONE (all unique)'}")
print(f"slack holders outside root: {sorted(slack_holders) or 'NONE'}")
print()
sev_order = {'CRIT': 0, 'WARN': 1, 'NOTE': 2}
drift_rows.sort(key=lambda r: (sev_order.get(r['severity'], 3), r['profile']))
by_sev = {}
for r in drift_rows:
    by_sev.setdefault(r['severity'], []).append(r)
for sev in ('CRIT', 'WARN', 'NOTE'):
    rows = by_sev.get(sev, [])
    print(f"===== {sev} ({len(rows)}) =====")
    for r in rows:
        print(f"  [{r['profile']}] {r['check']}: {r['detail']}")
print()
print("CHECK-COUNTS per profile:")
for p in sorted(report['profiles']):
    n = len(report['profiles'][p])
    if n:
        print(f"  {p}: {n}")
print("CLEAN:", ', '.join(sorted(clean)))
