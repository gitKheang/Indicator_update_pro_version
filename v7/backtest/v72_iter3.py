from simple_engine import run
from v72_final import V72
from v72_iter import yearly
PIV = ('PIVOT_RESISTANCE', 'PIVOT_SUPPORT')
LIQ = ('EQH', 'EQL', '4H_SWING_HIGH', '4H_SWING_LOW')
def v(lab, **kw):
    r = run(dict(V72, **kw), lab); print('    ', yearly(r), '| rej', {k: r['rej'][k] for k in r['rej'] if k.startswith('sl')}); return r
v('Q: pivots + EQH/EQL + 4H swing', clean_room=PIV + LIQ)
for k in (1.5, 2.0, 2.5, 3.0):
    v('Q + risk <= %.1f ATR' % k, clean_room=PIV + LIQ, max_sl_atr=k)
v('P + risk <= 2.0 ATR', clean_room=PIV, max_sl_atr=2.0)
