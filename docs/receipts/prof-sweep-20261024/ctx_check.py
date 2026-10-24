import os, yaml

PROF = '/home/arch/.hermes/profiles'
EXPECT = {'qwen38': 1000000, 'qwen38-flash-fp8': 262144, 'glm53': 1000000,
          'qwen36-fast': 131072, 'muse': 262144}
findings = []
for d in sorted(os.listdir(PROF)):
    cp = os.path.join(PROF, d, 'config.yaml')
    if not os.path.exists(cp):
        continue
    cfg = yaml.safe_load(open(cp)) or {}
    m = cfg.get('model') or {}
    dflt = m.get('default')
    ctx = m.get('context_length')
    if dflt is None:
        findings.append((d, 'model.default MISSING', None))
        continue
    if ctx is None:
        findings.append((d, f'context_length MISSING for {dflt}', None))
    elif dflt in EXPECT and int(ctx) != EXPECT[dflt]:
        findings.append((d, f'context_length={ctx} for {dflt}, expected {EXPECT[dflt]}', ctx))
    elif dflt not in EXPECT:
        findings.append((d, f'unknown default model {dflt} (ctx={ctx}) — manual check', ctx))

print('context_length findings:')
if not findings:
    print('  NONE — all pinned correctly')
for f in findings:
    print(' ', f)
