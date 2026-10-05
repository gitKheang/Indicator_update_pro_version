from v76_lab import setups, stats, fmt
from v75_lab import features, sequential
def F(cfg, pred, lab, seq=True):
    rows, _ = setups(cfg)
    for r in rows: r['f'] = features(r)
    sel = [r for r in rows if pred(r)]
    s = stats(sequential(sel) if seq else sel)
    print('%-52s %s' % (lab, fmt(s)))
g = lambda r, k, d=99: r['f'].get(k) if r['f'].get(k) is not None else d
nochop = dict(chop_max=0)
F({}, lambda r: True, 'V7.5 deployed')
F(nochop, lambda r: True, 'V7.5 without chop filter')
for k in (1.5, 1.75, 2.0, 2.5):
    F(nochop, lambda r, k=k: g(r, 'impulse_atr') < k, 'no chop + impulse < %.2f ATR' % k)
for k in (1.5, 2.0, 2.5):
    F(nochop, lambda r, k=k: r['f']['sl_atr89'] < k, 'no chop + SL < %.1f ATR89' % k)
F(nochop, lambda r: g(r, 'impulse_atr') < 2.0 and g(r, 'pb_bars') <= 8, 'no chop + impulse < 2 ATR + pb <= 8')
F(nochop, lambda r: g(r, 'impulse_atr') < 2.0 and g(r, 'ext_ema20_atr', 9) < 1.5, 'no chop + impulse < 2 ATR + not extended')
F(dict(chop_max=0, pb_max=0, use_st=False), lambda r: g(r, 'impulse_atr') < 2.0, 'V7.3 base + impulse < 2 ATR')
F(dict(chop_max=0, pb_max=0, use_st=False), lambda r: g(r, 'impulse_atr') < 2.0, 'V7.3 base + impulse < 2 ATR (overlap allowed)', seq=False)
F(dict(chop_max=0, pb_max=0, use_st=False, clean=False), lambda r: g(r, 'impulse_atr') < 2.0, 'V7.3 base, no clean room + impulse < 2 (overlap)', seq=False)
