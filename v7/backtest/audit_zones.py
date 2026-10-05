"""Audit the 15m Supply/Demand zones against how a trader draws them, and test
whether 'trader-style' zones hold better at first touch (1.5R, stop beyond the zone)."""
import datetime, statistics, pickle, os
import data_load, phase5
from data_load import key_fixed
from simple_engine import ctx, T, H, L, C, O, A, N, MB, B1
from phase5 import range_location
UTC = datetime.timezone.utc
SPLIT = int(datetime.datetime(2025, 7, 1, tzinfo=UTC).timestamp() * 1000)
bars = data_load.build()
idx15 = {b[0]: j for j, b in enumerate(bars['m15'])}
kf = key_fixed(15 * 60000)
K15 = [idx15.get(kf(T[i])) for i in range(N)]
def packets(cfg, tag):
    fn = 'data/pk15_%s.pkl' % tag
    if os.path.exists(fn): return pickle.load(open(fn, 'rb'))
    pk = phase5.setup_packets(bars['m15'], cfg); pickle.dump(pk, open(fn, 'wb')); return pk
def study(pk, fams, label, flt=None):
    seen = set(); res = [[0, 0], [0, 0]]; heights = []
    for i in range(1, N - 300):
        k = K15[i]
        if k is None or k < 1 or A[i] is None: continue
        p = pk[k - 1]
        for fam, side in fams:
            for z in p[fam]:
                if z is None: continue
                key = (fam, z[2])
                if key in seen: continue
                if not z[4]: seen.add(key); continue
                top, bot = z[0], z[1]
                if (side == 1 and C[i - 1] < bot) or (side == -1 and C[i - 1] > top): seen.add(key); continue
                if L[i] <= top and H[i] >= bot:
                    seen.add(key)
                    if flt and not flt(i, side, top, bot, p): continue
                    near = top if side == 1 else bot; far = bot if side == 1 else top
                    stop = far - 0.3 * A[i] if side == 1 else far + 0.3 * A[i]
                    risk = abs(near - stop); tp = near + side * 1.5 * risk; w = None
                    if (L[i] <= stop) if side == 1 else (H[i] >= stop): w = 0
                    else:
                        for j in range(i + 1, min(N, i + 576)):
                            if (L[j] <= stop) if side == 1 else (H[j] >= stop): w = 0; break
                            if (H[j] >= tp) if side == 1 else (L[j] <= tp): w = 1; break
                    if w is None: continue
                    heights.append((top - bot) / A[i])
                    q = 0 if T[i] < SPLIT else 1
                    res[q][0] += 1; res[q][1] += w
    n = res[0][0] + res[1][0]; w = res[0][1] + res[1][1]
    print('%-58s n=%5d hold %4.1f%% (IS %4.1f%% / OOS %4.1f%%) | zone height median %.2f ATR' % (
        label, n, 100 * w / max(n, 1), 100 * res[0][1] / max(res[0][0], 1), 100 * res[1][1] / max(res[1][0], 1), statistics.median(heights) if heights else 0))
DS = (('demand', 1), ('supply', -1))
cur = packets({}, 'cur')                                         # current: min move 0.2%, height capped at 0.05%
unc = packets(dict(ds_max_pc_zone=5.0), 'uncapped')               # full base candle range (how a trader draws it)
strong = packets(dict(ds_max_pc_zone=5.0, ds_min_pc_change=0.5), 'strong')   # only strong departures (~2.5x)
print('Zone geometry and first-touch hold rate at 1.5R (a level with no edge ≈ 40%):')
study(cur, DS, 'Current D/S (height capped at 0.05% ≈ $2)')
study(unc, DS, 'Trader-style D/S: full base, no height cap')
study(strong, DS, 'Trader-style + strong departure (move >= 0.5%)')
trend = lambda i, s, top, bot, p: MB[i] == s and B1[i] == s
disc = lambda i, s, top, bot, p: MB[i] == s and B1[i] == s and range_location((top + bot) / 2, p['swingHigh'], p['swingLow']) * s in (-1, -2)
study(strong, DS, 'Strong departure + with 4H/1H trend', trend)
study(strong, DS, 'Strong departure + trend + discount/premium side', disc)
study(cur, (('bullOb', 1), ('bearOb', -1)), 'Order Block that caused a 15m BOS (current OB logic)')
