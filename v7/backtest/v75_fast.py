import pickle, datetime, collections
from v75_lab import setups, sequential, stats, fmt, features, T, L, H, C, A, NYD
UTC = datetime.timezone.utc
rows = pickle.load(open('data/v75_inter_rows.pkl', 'rb'))
for r in rows:
    i, s, pb = r['i'], r['s'], r['pbar']
    seg = range(pb, i + 1)
    k = min(seg, key=lambda j: L[j]) if s == 1 else max(seg, key=lambda j: H[j])
    r['f']['rec_bars'] = i - k
    r['f']['pb_len'] = k - pb          # bars from the pivot to the pullback extreme
print('-- pb_bars threshold (sequential)')
for c in (8, 9, 10, 11, 12, 13, 14, 16, 20):
    print('pb_bars < %2d' % c, fmt(stats(sequential([r for r in rows if r['f']['pb_bars'] < c]))))
print('-- recovery bars (pullback extreme -> trigger)')
for c in (3, 4, 5, 6, 8, 10):
    print('rec_bars <= %2d' % c, fmt(stats(sequential([r for r in rows if r['f']['rec_bars'] <= c]))))
print('-- pullback length (pivot -> extreme)')
for c in (2, 3, 4, 5, 6, 8):
    print('pb_len <= %2d' % c, fmt(stats(sequential([r for r in rows if r['f']['pb_len'] <= c]))))
print('-- yearly, fast (pb_bars < 10) vs V7.4')
for lab, sel in (('V7.4', rows), ('fast', [r for r in rows if r['f']['pb_bars'] < 10])):
    seq = sequential(sel); g = collections.defaultdict(list)
    for r in seq: g[datetime.datetime.fromtimestamp(T[r['i']] / 1000, UTC).year].append(r)
    for y in sorted(g): print('  %-5s %d' % (lab, y), fmt(stats(g[y], days=1)))
