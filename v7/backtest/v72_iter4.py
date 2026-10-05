import data_load, phase5
from data_load import key_fixed
from simple_engine import run, ctx, T, N, MB, B1
from v72_final import V72
from v72_iter import yearly
PIV = ('PIVOT_RESISTANCE', 'PIVOT_SUPPORT'); LIQ = ('EQH', 'EQL', '4H_SWING_HIGH', '4H_SWING_LOW')
Q = dict(V72, clean_room=PIV + LIQ)
bars = data_load.build()
st15 = phase5.structure_states(bars['m15'])
idx = {b[0]: j for j, b in enumerate(bars['m15'])}
kf = key_fixed(15 * 60000)
B15 = [None] * N
for i in range(N):
    k = idx.get(kf(T[i]))
    B15[i] = st15[k - 1][0] if k is not None and k >= 1 else None
def v(lab, **kw):
    r = run(dict(Q, **kw), lab); print('    ', yearly(r)); return r
v('Q (4H+1H)')
v('Q + 15m bias agrees', filter=lambda i, s: B15[i] == s)
v('Q, 4H + 15m instead of 4H + 1H', htf='4h', filter=lambda i, s: B15[i] == s)
v('Q, 1H + 15m instead of 4H + 1H', htf='none', filter=lambda i, s: B1[i] == s and B15[i] == s)
