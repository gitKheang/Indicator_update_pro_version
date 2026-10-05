"""Every Phase-5 zone at its first 5m touch: does it hold?
Trade model: limit at the near edge on the touch, stop beyond the far edge + 0.3 ATR,
target 1.5R; stop-first on the touch bar. A level with no edge wins ~40%."""
import collections, datetime
from r2_common import ctx, SPLIT
from phase5 import range_location
H, L, C, O, T, A = ctx['H'], ctx['L'], ctx['C'], ctx['O'], ctx['T'], ctx['atr']
N = ctx['N']
FAM = (('demand', 1), ('bullOb', 1), ('pSup', 1), ('supply', -1), ('bearOb', -1), ('pRes', -1), ('bullFvg', 1), ('bearFvg', -1))
seen = set()
events = []
prev_pub = {}
for i in range(1, N - 300):
    pk = ctx['pk'][i]
    if pk['swingHigh'] is None or A[i] is None:
        continue
    for fam, side in FAM:
        for z in pk[fam]:
            if z is None:
                continue
            top, bot = z[0], z[1]
            key = (fam, z[2] if z[2] is not None else (round(top, 2), round(bot, 2)))
            if key in seen:
                continue
            if not z[4]:
                seen.add(key); continue  # already non-fresh when we first see it
            # first overlap with a 5m bar, zone must be on the correct side at the prior close
            if (side == 1 and C[i - 1] < bot) or (side == -1 and C[i - 1] > top):
                seen.add(key); continue
            if L[i] <= top and H[i] >= bot:
                seen.add(key)
                events.append(dict(i=i, fam=fam, side=side, top=top, bot=bot, conf=z[3], origin=z[2], pk=pk))
print('first touches:', len(events))
def outcome(ev, buf=0.3, k=1.5, maxbars=288):
    i, s, a = ev['i'], ev['side'], A[ev['i']]
    near = ev['top'] if s == 1 else ev['bot']
    far = ev['bot'] if s == 1 else ev['top']
    entry = near
    stop = far - buf * a if s == 1 else far + buf * a
    risk = abs(entry - stop)
    tp = entry + s * k * risk
    if (L[i] <= stop) if s == 1 else (H[i] >= stop):
        return 0, risk
    for j in range(i + 1, min(N, i + maxbars)):
        if (L[j] <= stop) if s == 1 else (H[j] >= stop):
            return 0, risk
        if (H[j] >= tp) if s == 1 else (L[j] <= tp):
            return 1, risk
    return None, risk
for ev in events:
    ev['win'], ev['risk'] = outcome(ev)
    ev['riskATR'] = ev['risk'] / A[ev['i']]
    m = ctx['macroBias'][ev['i']]; b = ctx['bias1H'][ev['i']]
    ev['htf'] = (m == ev['side']) + (b == ev['side'])
    ev['loc'] = range_location((ev['top'] + ev['bot']) / 2, ev['pk']['swingHigh'], ev['pk']['swingLow'])
    ev['age_h'] = (T[ev['i']] - ev['conf']) / 3600000 if ev['conf'] else None
def show(name, keyf):
    g = collections.defaultdict(lambda: [[0, 0], [0, 0]])
    for ev in events:
        if ev['win'] is None: continue
        p = 0 if T[ev['i']] < SPLIT else 1
        k = keyf(ev); g[k][p][0] += 1; g[k][p][1] += ev['win']
    print('==', name)
    for k in sorted(g, key=str):
        (n0, w0), (n1, w1) = g[k]
        print('  %-18s IS n=%4d WR %4.1f%% | OOS n=%4d WR %4.1f%%' % (k, n0, 100 * w0 / max(n0, 1), n1, 100 * w1 / max(n1, 1)))
show('all', lambda e: 'all')
show('family', lambda e: e['fam'])
show('4H+1H agree count', lambda e: e['htf'])
show('location of zone', lambda e: e['loc'] * e['side'])
show('zone height ATR', lambda e: '<0.5' if e['riskATR'] < 0.8 else '<1.5' if e['riskATR'] < 1.8 else '<3' if e['riskATR'] < 3.3 else '>=3')
show('age hours', lambda e: None if e['age_h'] is None else '<4' if e['age_h'] < 4 else '<24' if e['age_h'] < 24 else '<96' if e['age_h'] < 96 else '>=96')
