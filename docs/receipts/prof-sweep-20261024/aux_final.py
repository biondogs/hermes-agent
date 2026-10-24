import os

def section_norm(path, key='auxiliary'):
    lines = open(path).read().split('\n')
    idxs = [i for i, ln in enumerate(lines) if ln.startswith(key + ':')]
    assert len(idxs) == 1, path
    start = idxs[0]
    end = start + 1
    while end < len(lines):
        ln = lines[end]
        if ln.strip() == '' or ln[0] in ' \t' or ln.lstrip().startswith('#'):
            end += 1
        else:
            break
    block = lines[start:end]
    while block and block[-1].strip() == '':
        block.pop()
    return '\n'.join(block)

root = section_norm('/home/arch/.hermes/config.yaml')
bad = []
for d in sorted(os.listdir('/home/arch/.hermes/profiles')):
    f = f'/home/arch/.hermes/profiles/{d}/config.yaml'
    if not os.path.isfile(f):
        continue
    if section_norm(f) != root:
        bad.append(d)
print('normalized byte-diff profiles:', bad or 'NONE — all 59 byte-identical modulo EOF newline')
