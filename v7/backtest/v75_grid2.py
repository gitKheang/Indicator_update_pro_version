from v75_lab import setups, sequential, stats, fmt, features
g = lambda f, k, d=None: f.get(k) if f.get(k) is not None else d
for htf_mode in ('both', '1h', '4h', 'none'):
    rows = setups(htf_mode=htf_mode, use_st=True)
    for r in rows: r['f'] = features(r)
    for pb in (11, 12, 14):
        for lab, fl in (('', lambda f: True), ('calm1h', lambda f: g(f, 'chop_1h', 99) < 50), ('tight', lambda f: g(f, 'impulse_atr', 99) < 2.0)):
            sel = [r for r in rows if r['f']['pb_bars'] < pb and fl(r['f'])]
            print('%-4s pb<%d %-7s SEQ %s' % (htf_mode, pb, lab, fmt(stats(sequential(sel)))))
            print('%-4s %-12s IND %s' % ('', '', fmt(stats(sel))))
