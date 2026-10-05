import datetime, collections
import data_load, phase5
from data_load import key_fixed
from simple_engine import run, metrics, fmt, ctx, N, T, MB, B1
from v72_final import V72
UTC = datetime.timezone.utc
def yearly(r):
    g = collections.defaultdict(list)
    for t in r['trades']: g[datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).year].append(t)
    return ' | '.join('%d n=%d PF %.2f WR %.0f%%' % (y, m['n'], m['pf'], 100 * m['wr']) for y in sorted(g) for m in [metrics(g[y], r['cfg'])])
def v(lab, **kw):
    r = run(dict(V72, **kw), lab); print('    ', yearly(r)); return r
v('V7.2 baseline')
# which obstacle families matter for the clean room?
v('clean: Supply/Demand only', clean_room=('SUPPLY', 'DEMAND'))
v('clean: Order Blocks only', clean_room=('BEAR_OB', 'BULL_OB'))
v('clean: Pivot S/R only', clean_room=('PIVOT_RESISTANCE', 'PIVOT_SUPPORT'))
v('clean: D/S + OB (no pivots)', clean_room=('SUPPLY', 'DEMAND', 'BEAR_OB', 'BULL_OB'))
# stop cap variants
v('no $ cap', max_sl=999.0)
v('cap 3 ATR instead of $15', max_sl=999.0, filter=None) if False else None
