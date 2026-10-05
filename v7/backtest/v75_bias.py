"""Faster / chart-like 4H and 1H trend readings inside V7.5 (fast pullback + calm 1H + 5m ST)."""
import data_load, phase5
from data_load import key_fixed, key_4h
from v75_lab import setups, sequential, stats, fmt, features, supertrend, T, N, MB, B1, CHOP1H_PINE
bars = data_load.build()
def mapper(tf, keyfn):
    idx = {b[0]: j for j, b in enumerate(bars[tf])}
    return [idx.get(keyfn(T[i])) for i in range(N)]
K4 = mapper('h4', key_4h); K1 = mapper('h1', key_fixed(3600000))
def align(series, K):
    return [series[k - 1] if k is not None and k >= 1 else None for k in K]
def struct_bias(tf, K, length):
    return align([s[0] for s in phase5.structure_states(bars[tf], length)], K)
def st_bias(tf, K):
    b = bars[tf]; return align(supertrend([x[2] for x in b], [x[3] for x in b], [x[4] for x in b], 10, 3.0)[1], K)
def ema_bias(tf, K, n, slope=3):
    cl = [b[4] for b in bars[tf]]; e = []; v = None; a = 2 / (n + 1)
    for c in cl: v = c if v is None else v + a * (c - v); e.append(v)
    raw = [0 if k < max(n, slope) else (1 if cl[k] > e[k] > e[k - slope] else -1 if cl[k] < e[k] < e[k - slope] else 0) for k in range(len(cl))]
    return align(raw, K)
B = {'4H s50': MB, '1H s50': B1, '4H s20': struct_bias('h4', K4, 20), '4H s10': struct_bias('h4', K4, 10),
     '1H s20': struct_bias('h1', K1, 20), '1H s10': struct_bias('h1', K1, 10), '4H ST': st_bias('h4', K4), '1H ST': st_bias('h1', K1),
     '4H EMA50': ema_bias('h4', K4, 50), '1H EMA50': ema_bias('h1', K1, 50)}
combos = [('4H s50', '1H s50'), ('4H s20', '1H s50'), ('4H s10', '1H s50'), ('4H ST', '1H s50'), ('4H EMA50', '1H s50'),
          ('4H s20', '1H s20'), ('4H s10', '1H s20'), ('4H ST', '1H ST'), ('4H s50', '1H s20'), ('4H s50', '1H ST'),
          ('4H EMA50', '1H EMA50'), ('4H s20', '1H ST')]
for b4n, b1n in combos:
    b4, b1 = B[b4n], B[b1n]
    rows = setups(htf_mode='none', trigger_filter=lambda i, s, b4=b4, b1=b1: b4[i] == s and b1[i] == s)
    for r in rows: r['f'] = features(r)
    v75 = [r for r in rows if r['f']['pb_bars'] < 12 and CHOP1H_PINE[r['i']] is not None and CHOP1H_PINE[r['i']] < 50]
    fast = [r for r in rows if r['f']['pb_bars'] < 12]
    print('%-9s + %-8s V7.5 SEQ %s' % (b4n, b1n, fmt(stats(sequential(v75)))))
    print('%-20s fast SEQ %s' % ('', fmt(stats(sequential(fast)))))
