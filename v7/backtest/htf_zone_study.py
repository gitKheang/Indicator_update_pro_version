import collections, pickle, os
import data_load, phase5
from data_load import key_fixed, key_4h
from r2_common import ctx, SPLIT
H, L, C, T, A = ctx['H'], ctx['L'], ctx['C'], ctx['T'], ctx['atr']
N = ctx['N']
bars = data_load.build()
def study(tf, keyfn, label):
    fn = f'data/pk_{tf}.pkl'
    if os.path.exists(fn):
        pk = pickle.load(open(fn, 'rb'))
    else:
        pk = phase5.setup_packets(bars[tf], {}); pickle.dump(pk, open(fn, 'wb'))
    idx = {b[0]: j for j, b in enumerate(bars[tf])}
    seen = set(); res = collections.defaultdict(lambda: [[0, 0], [0, 0]])
    for i in range(1, N - 300):
        k = idx.get(keyfn(T[i]))
        if k is None or k < 1 or A[i] is None: continue
        p = pk[k - 1]
        for fam, side in (('demand', 1), ('bullOb', 1), ('pSup', 1), ('supply', -1), ('bearOb', -1), ('pRes', -1)):
            for z in p[fam]:
                if z is None: continue
                key = (fam, z[2])
                if key in seen: continue
                if not z[4]: seen.add(key); continue
                top, bot = z[0], z[1]
                if (side == 1 and C[i - 1] < bot) or (side == -1 and C[i - 1] > top): seen.add(key); continue
                if L[i] <= top and H[i] >= bot:
                    seen.add(key)
                    near = top if side == 1 else bot; far = bot if side == 1 else top
                    stop = far - 0.3 * A[i] if side == 1 else far + 0.3 * A[i]
                    risk = abs(near - stop); tp = near + side * 1.5 * risk
                    w = None
                    if (L[i] <= stop) if side == 1 else (H[i] >= stop): w = 0
                    else:
                        for j in range(i + 1, min(N, i + 576)):
                            if (L[j] <= stop) if side == 1 else (H[j] >= stop): w = 0; break
                            if (H[j] >= tp) if side == 1 else (L[j] <= tp): w = 1; break
                    if w is None: continue
                    pp = 0 if T[i] < SPLIT else 1
                    for kk in (fam, 'ALL'):
                        res[kk][pp][0] += 1; res[kk][pp][1] += w
    print('==', label)
    for kk in sorted(res):
        (n0, w0), (n1, w1) = res[kk]
        print('  %-8s IS n=%4d WR %4.1f%% | OOS n=%4d WR %4.1f%%' % (kk, n0, 100 * w0 / max(n0, 1), n1, 100 * w1 / max(n1, 1)))
study('h1', key_fixed(3600000), '1H zones, first 5m touch, 1.5R')
study('h4', key_4h, '4H zones, first 5m touch, 1.5R')
