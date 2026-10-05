"""Replace the slow swings(50) HTF bias with more responsive, chart-like trend readings
and re-test V7.3. Every HTF value uses the last COMPLETED HTF bar (no lookahead)."""
import datetime
import data_load, phase5
from data_load import key_fixed, key_4h
from simple_engine import run, metrics, fmt, ctx, T, C, N, MB, B1
from v72_final import V73
from v72_iter import yearly
bars = data_load.build()
def mapper(tf, keyfn):
    idx = {b[0]: j for j, b in enumerate(bars[tf])}
    return [idx.get(keyfn(T[i])) for i in range(N)]
K4 = mapper('h4', key_4h); K1 = mapper('h1', key_fixed(3600000)); K15 = mapper('m15', key_fixed(15 * 60000))
def align(series, K):
    return [series[k - 1] if k is not None and k >= 1 else None for k in K]
def struct_bias(tf, K, length):
    st = phase5.structure_states(bars[tf], length)
    return align([s[0] for s in st], K)
def ema(vals, n):
    out = []; e = None; a = 2 / (n + 1)
    for v in vals:
        e = v if e is None else e + a * (v - e); out.append(e)
    return out
def ema_bias(tf, K, n, slope_bars=3):
    cl = [b[4] for b in bars[tf]]; e = ema(cl, n)
    raw = []
    for k in range(len(cl)):
        if k < n or k < slope_bars: raw.append(0); continue
        up = cl[k] > e[k] and e[k] > e[k - slope_bars]
        dn = cl[k] < e[k] and e[k] < e[k - slope_bars]
        raw.append(1 if up else -1 if dn else 0)
    return align(raw, K)
def accuracy(b):
    ok = n = 0
    for i in range(2000, N - 300, 12):
        if b[i] in (1, -1):
            mv = C[min(N - 1, i + 288)] - C[i]
            if mv != 0: n += 1; ok += (b[i] * mv > 0)
    return 100 * ok / max(n, 1), n
variants = {
    '4H swings(50) [current]': MB, '1H swings(50) [current]': B1,
    '4H swings(20)': struct_bias('h4', K4, 20), '4H swings(10)': struct_bias('h4', K4, 10),
    '1H swings(20)': struct_bias('h1', K1, 20), '1H swings(10)': struct_bias('h1', K1, 10),
    '4H EMA50 pos+slope': ema_bias('h4', K4, 50), '1H EMA50 pos+slope': ema_bias('h1', K1, 50),
    '4H EMA20 pos+slope': ema_bias('h4', K4, 20), '1H EMA20 pos+slope': ema_bias('h1', K1, 20),
}
print('Agreement with the next-24h move (hourly samples):')
for k, b in variants.items():
    acc, n = accuracy(b); print('  %-26s %.1f%% (n=%d)' % (k, acc, n))
V = variants
def test(lab, b4, b1):
    r = run(dict(V73, htf='none', filter=lambda i, s, b4=b4, b1=b1: b4[i] == s and b1[i] == s), lab, show=False)
    m = metrics(r['trades'], r['cfg'], 719)
    from r2_common import SPLIT
    mi = metrics([t for t in r['trades'] if t['readyTime'] < SPLIT], r['cfg']); mo = metrics([t for t in r['trades'] if t['readyTime'] >= SPLIT], r['cfg'])
    print('%-44s %s | PF IS %.2f OOS %.2f' % (lab, fmt(m), mi['pf'], mo['pf']))
    print('     ', yearly(r))
print()
test('V7.3 current: 4H s50 + 1H s50', V['4H swings(50) [current]'], V['1H swings(50) [current]'])
test('4H s20 + 1H s20', V['4H swings(20)'], V['1H swings(20)'])
test('4H s50 + 1H s20', V['4H swings(50) [current]'], V['1H swings(20)'])
test('4H s20 + 1H s10', V['4H swings(20)'], V['1H swings(10)'])
test('4H EMA50 + 1H EMA50', V['4H EMA50 pos+slope'], V['1H EMA50 pos+slope'])
test('4H EMA20 + 1H EMA20', V['4H EMA20 pos+slope'], V['1H EMA20 pos+slope'])
test('4H EMA50 + 1H s50', V['4H EMA50 pos+slope'], V['1H swings(50) [current]'])
