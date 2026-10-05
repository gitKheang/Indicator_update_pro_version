import datetime, collections
from r2_common import ctx, SPLIT
from phase5 import range_location
from sig_search import bracket, H, L, C, O, T, A, N, ev, mb, b1
UTC = datetime.timezone.utc
rng = range(600, N - 300)
sigs = [(i, 1) for i in rng if ev['bull_ibreak'][i] and mb[i] == 1 and b1[i] == 1] + \
       [(i, -1) for i in rng if ev['bear_ibreak'][i] and mb[i] == -1 and b1[i] == -1]
sigs.sort()
# bars since 1H bias last changed
since = [0] * N
for i in range(1, N):
    since[i] = since[i - 1] + 1 if b1[i] == b1[i - 1] else 0
rows = []
busy = -1
for i, s in sigs:
    if A[i] is None or i <= busy: continue
    ext = min(L[i - 12:i + 1]) if s == 1 else max(H[i - 12:i + 1])
    stop = ext - 0.3 * A[i] if s == 1 else ext + 0.3 * A[i]
    risk = (C[i] - stop) * s
    if risk <= 0 or risk > 15 or risk < 2: continue
    w, j = bracket(i, s, C[i], stop, 1.5)
    if w is None: continue
    busy = j
    pk = ctx['pk'][i]
    d = datetime.datetime.fromtimestamp(T[i] / 1000, UTC)
    # day open (17:00 NY session) approx: use 24h ago close as reference momentum
    mom24 = (C[i] - C[i - 288]) * s / A[i] if i >= 288 else 0
    mom4h = (C[i] - C[i - 48]) * s / A[i]
    hi12 = max(H[i - 48:i]); lo12 = min(L[i - 48:i])
    pull = ((hi12 - ext) if s == 1 else (ext - lo12)) / A[i]
    j0 = max(0, i - 2880); past = [x for x in A[j0:i:96] if x]
    rows.append(dict(i=i, s=s, w=w, p=0 if T[i] < SPLIT else 1, hour=d.hour, riskATR=risk / A[i], risk=risk,
                     loc15=range_location(C[i], pk['swingHigh'], pk['swingLow']) * s,
                     loc4=range_location(C[i], ctx['macroHigh'][i], ctx['macroLow'][i]) * s,
                     body=(C[i] - O[i]) * s / A[i], mom24=mom24, mom4h=mom4h, pull=pull, since=since[i],
                     vol=A[i] / (sum(past) / len(past)) if past else 1, swingTrend=ctx['trend'][i] == s, dow=d.weekday()))
print('base trades', len(rows))
def show(name, kf):
    g = collections.defaultdict(lambda: [[0, 0], [0, 0]])
    for r in rows:
        k = kf(r); g[k][r['p']][0] += 1; g[k][r['p']][1] += r['w']
    print('==', name)
    for k in sorted(g, key=str):
        (n0, w0), (n1, w1) = g[k]
        print('  %-12s IS n=%4d WR %4.1f%% | OOS n=%4d WR %4.1f%%' % (k, n0, 100 * w0 / max(n0, 1), n1, 100 * w1 / max(n1, 1)))
B = lambda v, e: next(('<%s' % x for x in e if v < x), '>=%s' % e[-1])
show('hour UTC', lambda r: r['hour'] // 3 * 3)
show('risk ATR', lambda r: B(r['riskATR'], [1, 1.5, 2, 3]))
show('risk $', lambda r: B(r['risk'], [4, 6, 9, 12]))
show('loc15 (side-adj)', lambda r: r['loc15'])
show('loc4H (side-adj)', lambda r: r['loc4'])
show('body ATR', lambda r: B(r['body'], [0.25, 0.5, 1, 1.5]))
show('mom24 ATR', lambda r: B(r['mom24'], [-5, 0, 5, 10, 20]))
show('mom4h ATR', lambda r: B(r['mom4h'], [-3, 0, 3, 6]))
show('pullback ATR', lambda r: B(r['pull'], [1, 2, 3, 5, 8]))
show('bars since 1H flip', lambda r: B(r['since'], [12, 48, 144, 432]))
show('vol regime', lambda r: B(r['vol'], [0.8, 1, 1.25, 1.6]))
show('5m swing trend', lambda r: r['swingTrend'])
show('dow', lambda r: r['dow'])
