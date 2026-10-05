import pickle, itertools
from v75_lab import T, SPLIT, wr, pf
rows = pickle.load(open('data/v75_setups.pkl', 'rb'))
DAYS = 719
def show(lab, sel):
    a = [r for r in rows if sel(r['f'])]
    i = [r for r in a if T[r['i']] < SPLIT]; o = [r for r in a if T[r['i']] >= SPLIT]
    print('%-58s n=%4d (%.2f/d) WR %5.1f%% PF %.2f | IS n=%3d %5.1f%% | OOS n=%3d %5.1f%%' % (lab, len(a), len(a) / DAYS, 100 * wr(a), pf(a), len(i), 100 * wr(i), len(o), 100 * wr(o)))
g = lambda k, f, d=None: f.get(k) if f.get(k) is not None else d
print('-- single features, finer cuts')
for c in (5, 6, 7, 8, 10, 12, 15): show('pb_bars < %d' % c, lambda f, c=c: g('pb_bars', f, 99) < c)
for c in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5): show('impulse_atr < %.2f' % c, lambda f, c=c: g('impulse_atr', f, 99) < c)
for c in (1.5, 2.0, 2.5, 3.0): show('sl_atr89 < %.1f' % c, lambda f, c=c: f['sl_atr89'] < c)
for c in (40, 45, 50, 55, 60): show('chop_1h < %d' % c, lambda f, c=c: g('chop_1h', f, 99) < c)
for c in (2, 3, 4, 5, 6): show('room_R >= %d' % c, lambda f, c=c: f['room_R'] >= c)
print('-- combinations')
P = {'fast': lambda f: g('pb_bars', f, 99) < 10, 'tight': lambda f: g('impulse_atr', f, 99) < 2.0,
     'calm1h': lambda f: g('chop_1h', f, 99) < 50, 'room3': lambda f: f['room_R'] >= 3, 'st1h': lambda f: g('st_1h', f, 0) == 1,
     'long': lambda f: f['side'] == 1, 'shallow': lambda f: g('pb_depth', f, 9) < 0.8}
for k in range(1, 5):
    for combo in itertools.combinations(P, k):
        show(' + '.join(combo), lambda f, combo=combo: all(P[c](f) for c in combo))
