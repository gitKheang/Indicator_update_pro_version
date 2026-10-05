import pickle, os, time
from simple_engine import run, metrics, C
from r2_common import SPLIT
from v72_final import V73
import famous
fn = 'data/famous.pkl'
if os.path.exists(fn):
    F = pickle.load(open(fn, 'rb'))
else:
    t0 = time.time(); F = famous.build_all(); pickle.dump(F, open(fn, 'wb')); print('built in', round(time.time() - t0), 's')
def ok(v): return v is not None
filters = {
    'Supertrend(10,3) agrees': lambda i, s: F['st'][i] == s,
    'ADX(14) >= 20': lambda i, s: ok(F['adx'][i]) and F['adx'][i] >= 20,
    'ADX >= 25 and DI agrees': lambda i, s: ok(F['adx'][i]) and F['adx'][i] >= 25 and ok(F['pdi'][i]) and (F['pdi'][i] - F['mdi'][i]) * s > 0,
    'DI+/DI- agrees': lambda i, s: ok(F['pdi'][i]) and (F['pdi'][i] - F['mdi'][i]) * s > 0,
    'Session VWAP side (TWAP proxy)': lambda i, s: (C[i] - F['vwap'][i]) * s > 0,
    'Squeeze momentum sign agrees': lambda i, s: ok(F['sqzmom'][i]) and F['sqzmom'][i] * s > 0,
    'Squeeze released (not in squeeze)': lambda i, s: not F['sqz'][i],
    'WaveTrend wt1 > wt2 (side)': lambda i, s: ok(F['wt2'][i]) and (F['wt1'][i] - F['wt2'][i]) * s > 0,
    'WaveTrend not overextended (|wt1|<60)': lambda i, s: ok(F['wt1'][i]) and F['wt1'][i] * s < 60,
    'Range Filter(100,3) agrees': lambda i, s: F['rf'][i] == s,
    'UT Bot(1,10) agrees': lambda i, s: F['ut'][i] == s,
    'Ichimoku: price beyond cloud': lambda i, s: ok(F['ktop'][i]) and ((C[i] > F['ktop'][i]) if s == 1 else (C[i] < F['kbot'][i])),
    'Ichimoku: tenkan vs kijun agrees': lambda i, s: ok(F['kijun'][i]) and (F['tenkan'][i] - F['kijun'][i]) * s > 0,
    'Hull(55) slope agrees': lambda i, s: ok(F['hma'][i]) and ok(F['hma'][i - 2]) and (F['hma'][i] - F['hma'][i - 2]) * s > 0,
    'RSI(14) on trade side of 50': lambda i, s: ok(F['rsi'][i]) and (F['rsi'][i] - 50) * s > 0,
    'RSI not overextended (<70 / >30)': lambda i, s: ok(F['rsi'][i]) and ((F['rsi'][i] < 70) if s == 1 else (F['rsi'][i] > 30)),
    'EMA 21>50>200 stack agrees': lambda i, s: ok(F['e200'][i]) and ((F['e21'][i] > F['e50'][i] > F['e200'][i]) if s == 1 else (F['e21'][i] < F['e50'][i] < F['e200'][i])),
    'Price beyond EMA200': lambda i, s: ok(F['e200'][i]) and (C[i] - F['e200'][i]) * s > 0,
    'Bollinger %B not stretched (<0.9/>0.1)': lambda i, s: ok(F['bbpct'][i]) and ((F['bbpct'][i] < 0.9) if s == 1 else (F['bbpct'][i] > 0.1)),
    'Donchian(20) breakout bar': lambda i, s: ok(F['dch'][i - 1]) and ((C[i] > F['dch'][i - 1]) if s == 1 else (C[i] < F['dcl'][i - 1])),
}
def line(lab, r):
    tr = r['trades']; c = r['cfg']
    m = metrics(tr, c, 719); mi = metrics([t for t in tr if t['readyTime'] < SPLIT], c); mo = metrics([t for t in tr if t['readyTime'] >= SPLIT], c)
    print('%-42s n=%4d %.2f/d WR %4.1f%% PF %.2f net %+6.1fR DD %4.1f | IS WR %4.1f%% PF %.2f | OOS WR %4.1f%% PF %.2f' % (
        lab, m['n'], m['perday'], 100 * m['wr'], m['pf'], m['net'], m['dd'], 100 * mi['wr'], mi['pf'], 100 * mo['wr'], mo['pf']))
line('V7.3 (no extra filter)', run(V73, show=False))
for lab, f in filters.items():
    line(lab, run(dict(V73, filter=f), show=False))
