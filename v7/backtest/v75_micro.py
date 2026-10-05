from v75_lab import setups, sequential, stats, fmt, features, micro_context, EV, N
c5 = micro_context(5)
print('sanity: n=5 events equal to port:', all(c5[0]['bull_ibreak'][i] == EV['bull_ibreak'][i] and c5[0]['bear_ibreak'][i] == EV['bear_ibreak'][i] for i in range(N)))
g = lambda f, k, d=None: f.get(k) if f.get(k) is not None else d
ALL = {}
for n in (3, 4, 5, 7):
    ctxn = c5 if n == 5 else micro_context(n)
    rows = setups(sctx=ctxn)
    for r in rows: r['f'] = features(r); r['n'] = n
    ALL[n] = rows
    for pb in (n + 4, n + 5, n + 6, n + 7, n + 9, 999):
        sel = [r for r in rows if r['f']['pb_bars'] < pb]
        print('len %d pb<%-3d SEQ %s' % (n, pb, fmt(stats(sequential(sel)))))
    sel = [r for r in rows if r['f']['pb_bars'] < n + 7 and g(r['f'], 'chop_1h', 99) < 50]
    print('len %d pb<%-3d+calm1h SEQ %s' % (n, n + 7, fmt(stats(sequential(sel)))))
import pickle; pickle.dump(ALL, open('data/v75_micro.pkl', 'wb'))
