import pickle, itertools
from v75_lab import sequential, stats, fmt
rows = pickle.load(open('data/v75_inter_rows.pkl', 'rb'))
g = lambda r, k, d=None: (r['f'].get(k) if k in r['f'] else r['g'].get(k)) if (r['f'].get(k) if k in r['f'] else r['g'].get(k)) is not None else d
P = {'tight': lambda r: g(r, 'impulse_atr', 99) < 2.0, 'calm1h': lambda r: g(r, 'chop_1h', 99) < 50, 'fast': lambda r: g(r, 'pb_bars', 99) < 10,
     'agbrk': lambda r: g(r, 'silver_break', 0) == 1, 'agst': lambda r: g(r, 'silver_st', 0) == 1, 'dxysame': lambda r: g(r, 'dxy_st_opp', 1) == 0}
res = []
for k in range(0, 5):
    for combo in itertools.combinations(P, k):
        sel = [r for r in rows if all(P[c](r) for c in combo)]
        s = stats(sequential(sel)); si = stats(sel)
        if s.get('n', 0) >= 60:
            res.append((s['wr'], ' + '.join(combo) or 'V7.4', s, si))
res.sort(key=lambda x: -x[0])
for wrv, lab, s, si in res[:40]:
    print('%-34s SEQ %s' % (lab, fmt(s)))
    print('%-34s IND n=%d %.2f/d WR %.1f%%' % ('', si['n'], si['perday'], 100 * si['wr']))
