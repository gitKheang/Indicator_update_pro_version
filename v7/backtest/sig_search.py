"""Raw edge of candidate signal families under the user's rules:
entry = signal close, stop = protected extreme of the setup + 0.3 ATR (<= $15, >= $2),
TP = 1.5R exactly (the minimum allowed), stop-first. One trade at a time."""
import datetime, collections
from r2_common import ctx, SPLIT, TWO_Y, DAYS_ALL
H, L, C, O, T, A = ctx['H'], ctx['L'], ctx['C'], ctx['O'], ctx['T'], ctx['atr']
N = ctx['N']; ev = ctx['ev']; mb, b1 = ctx['macroBias'], ctx['bias1H']
def bracket(i, s, entry, stop, k=1.5, maxbars=288):
    risk = abs(entry - stop); tp = entry + s * k * risk
    for j in range(i + 1, min(N, i + maxbars)):
        if (L[j] <= stop) if s == 1 else (H[j] >= stop): return 0, j
        if (H[j] >= tp) if s == 1 else (L[j] <= tp): return 1, j
    return None, i + maxbars
def evaluate(label, sigs, lb=12, buf=0.3, k=1.5, maxsl=15.0, minsl=2.0):
    res = [[0, 0], [0, 0]]; busy = -1; n = 0
    for i, s, ext in sigs:
        if i <= busy or A[i] is None: continue
        if ext is None:
            ext = min(L[i - lb:i + 1]) if s == 1 else max(H[i - lb:i + 1])
        stop = ext - buf * A[i] if s == 1 else ext + buf * A[i]
        risk = (C[i] - stop) * s
        if risk <= 0 or risk > maxsl or risk < minsl: continue
        w, j = bracket(i, s, C[i], stop, k)
        if w is None: continue
        busy = j; p = 0 if T[i] < SPLIT else 1
        res[p][0] += 1; res[p][1] += w; n += 1
    tot = res[0][0] + res[1][0]; wins = res[0][1] + res[1][1]
    print('%-52s n=%4d (%.2f/d) WR %4.1f%% | IS %4.1f%% OOS %4.1f%%' % (label, tot, tot / DAYS_ALL, 100 * wins / max(tot, 1),
          100 * res[0][1] / max(res[0][0], 1), 100 * res[1][1] / max(res[1][0], 1)))
rng = range(300, N - 300)
up_ich = [(i, 1, None) for i in rng if ev['bull_ichoch'][i]]; dn_ich = [(i, -1, None) for i in rng if ev['bear_ichoch'][i]]
up_ib = [(i, 1, None) for i in rng if ev['bull_ibreak'][i]]; dn_ib = [(i, -1, None) for i in rng if ev['bear_ibreak'][i]]
allich = sorted(up_ich + dn_ich); allib = sorted(up_ib + dn_ib)
evaluate('5m internal CHoCH, any', allich)
evaluate('5m internal CHoCH with 4H+1H', [x for x in allich if mb[x[0]] == x[1] and b1[x[0]] == x[1]])
evaluate('5m internal break with 4H+1H', [x for x in allib if mb[x[0]] == x[1] and b1[x[0]] == x[1]])
body = lambda x, th: (C[x[0]] - O[x[0]]) * x[1] >= th * A[x[0]]
evaluate('  + displacement body >= 0.5 ATR', [x for x in allich if mb[x[0]] == x[1] and b1[x[0]] == x[1] and A[x[0]] and body(x, 0.5)])
# liquidity sweep + CHoCH: within 12 bars before the CHoCH, price swept PDL/15m swing low/EQL and the CHoCH close is back above it
def sweep_sigs(side, levels_fn, win=12):
    out = []
    src = up_ich if side == 1 else dn_ich
    for i, s, _ in src:
        lv = [v for v in levels_fn(i) if v is not None]
        ext = min(L[i - win:i + 1]) if s == 1 else max(H[i - win:i + 1])
        ok = any((ext < v < C[i]) if s == 1 else (ext > v > C[i]) for v in lv)
        if ok: out.append((i, s, ext))
    return out
lq_dn = lambda i: [ctx['pdl'][i], ctx['pk'][i]['swingLow']] + list(ctx['pk'][i]['eql'])
lq_up = lambda i: [ctx['pdh'][i], ctx['pk'][i]['swingHigh']] + list(ctx['pk'][i]['eqh'])
sw = sorted(sweep_sigs(1, lq_dn) + sweep_sigs(-1, lq_up))
evaluate('sweep of PDH/PDL/15m swing/EQ + CHoCH back inside', sw)
evaluate('  same, with 4H bias', [x for x in sw if mb[x[0]] == x[1]])
# Asia range sweep at London (07-10 UTC) then CHoCH
def asia_range(i):
    d = datetime.datetime.fromtimestamp(T[i] / 1000, datetime.timezone.utc)
    return d
print('-- TP multiple sensitivity on CHoCH with 4H+1H')
base = [x for x in allich if mb[x[0]] == x[1] and b1[x[0]] == x[1]]
for k in (1.0, 1.5, 2.0):
    evaluate('   TP %.1fR' % k, base, k=k)
for buf in (0.1, 0.5, 1.0):
    evaluate('   buffer %.1f ATR' % buf, base, buf=buf)
