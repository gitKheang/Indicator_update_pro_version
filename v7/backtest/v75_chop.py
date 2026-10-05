from v75_lab import setups, sequential, stats, fmt, features, HTF, K1H, N, chop
rows = setups()
for r in rows: r['f'] = features(r)
# Pine-style non-repainting: inside hour H use the 1H bar H-1 (expr[1] with lookahead_on)
h1 = HTF['1h']; strict = [None] * N; cur = None; idx = -1
for i in range(N):
    if K1H[i] != cur: cur = K1H[i]; idx += 1
    strict[i] = idx - 1 if idx >= 1 else None
for r in rows:
    d = strict[r['i']]; r['f']['chop_1h_strict'] = h1['chop'][d] if d is not None else None
g = lambda f, k: f.get(k) if f.get(k) is not None else 99
for key in ('chop_1h', 'chop_1h_strict'):
    for c in (40, 45, 50, 55, 60):
        sel = [r for r in rows if r['f']['pb_bars'] < 12 and g(r['f'], key) < c]
        print('fast + %-15s < %d SEQ %s' % (key, c, fmt(stats(sequential(sel)))))
