import datetime, collections
from simple_engine import run, metrics, fmt, A
from v72_final import V72
from v72_iter import yearly
UTC = datetime.timezone.utc
PIV = ('PIVOT_RESISTANCE', 'PIVOT_SUPPORT')
def v(lab, **kw):
    r = run(dict(V72, **kw), lab); print('    ', yearly(r)); return r
v('P: pivots only (candidate)', clean_room=PIV)
v('P + PDH/PDL', clean_room=PIV + ('PDH', 'PDL'))
v('P + 15m swing H/L', clean_room=PIV + ('15M_SWING_HIGH', '15M_SWING_LOW'))
v('P + EQH/EQL', clean_room=PIV + ('EQH', 'EQL'))
v('P + 4H swing', clean_room=PIV + ('4H_SWING_HIGH', '4H_SWING_LOW'))
v('P, buffer 0.5 ATR', clean_room=PIV, buf=0.5)
v('P, buffer 0.2 ATR', clean_room=PIV, buf=0.2)
v('P, TP2 max 3R', clean_room=PIV, fixed_tp2=3.0)
v('P, TP2 max 2R', clean_room=PIV, fixed_tp2=2.0)
v('P, max SL $12', clean_room=PIV, max_sl=12.0)
v('P, max SL $10', clean_room=PIV, max_sl=10.0)
