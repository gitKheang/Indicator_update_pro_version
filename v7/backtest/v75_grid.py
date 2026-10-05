from v75_lab import setups, sequential, stats, fmt, features
g = lambda k, f, d=None: f.get(k) if f.get(k) is not None else d
FILT = {
    'none': lambda f: True,
    'calm1h': lambda f: g('chop_1h', f, 99) < 50,
    'tight': lambda f: g('impulse_atr', f, 99) < 2.0,
    'tight+calm1h': lambda f: g('impulse_atr', f, 99) < 2.0 and g('chop_1h', f, 99) < 50,
    'fast+tight+calm1h': lambda f: g('pb_bars', f, 99) < 10 and g('impulse_atr', f, 99) < 2.0 and g('chop_1h', f, 99) < 50,
}
for htf_mode in ('both', '1h', '4h', 'none'):
    for use_st in (True, False):
        rows = setups(htf_mode=htf_mode, use_st=use_st)
        for r in rows: r['f'] = features(r)
        for name, fl in FILT.items():
            sel = [r for r in rows if fl(r['f'])]
            print('%-5s ST=%-5s %-18s IND %s' % (htf_mode, use_st, name, fmt(stats(sel))))
            print('%-5s ST=%-5s %-18s SEQ %s' % ('', '', '', fmt(stats(sequential(sel)))))
