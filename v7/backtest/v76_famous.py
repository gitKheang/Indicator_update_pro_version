import pickle, os
from v76_lab import run, stats, fmt
import famous
from lab import C
fn = 'data/famous.pkl'
F = pickle.load(open(fn, 'rb')) if os.path.exists(fn) else famous.build_all()
if not os.path.exists(fn): pickle.dump(F, open(fn, 'wb'))
ok = lambda v: v is not None
BASE = dict(chop_max=0, pe_after_pivot=True)
filters = {
    'Ichimoku: beyond cloud': lambda i, s: ok(F['ktop'][i]) and ((C[i] > F['ktop'][i]) if s == 1 else (C[i] < F['kbot'][i])),
    'Ichimoku: tenkan vs kijun': lambda i, s: ok(F['kijun'][i]) and (F['tenkan'][i] - F['kijun'][i]) * s > 0,
    'Range Filter(100,3)': lambda i, s: F['rf'][i] == s,
    'Session VWAP side': lambda i, s: (C[i] - F['vwap'][i]) * s > 0,
    'EMA 21>50>200 stack': lambda i, s: ok(F['e200'][i]) and ((F['e21'][i] > F['e50'][i] > F['e200'][i]) if s == 1 else (F['e21'][i] < F['e50'][i] < F['e200'][i])),
    'RSI(14) side of 50': lambda i, s: ok(F['rsi'][i]) and (F['rsi'][i] - 50) * s > 0,
    'RSI not overextended': lambda i, s: ok(F['rsi'][i]) and ((F['rsi'][i] < 70) if s == 1 else (F['rsi'][i] > 30)),
    'WaveTrend wt1>wt2': lambda i, s: ok(F['wt2'][i]) and (F['wt1'][i] - F['wt2'][i]) * s > 0,
    'Squeeze momentum sign': lambda i, s: ok(F['sqzmom'][i]) and F['sqzmom'][i] * s > 0,
    'ADX>=25 and DI agrees': lambda i, s: ok(F['adx'][i]) and F['adx'][i] >= 25 and ok(F['pdi'][i]) and (F['pdi'][i] - F['mdi'][i]) * s > 0,
    'DI+/DI- agrees': lambda i, s: ok(F['pdi'][i]) and (F['pdi'][i] - F['mdi'][i]) * s > 0,
    'Hull(55) slope': lambda i, s: ok(F['hma'][i]) and ok(F['hma'][i - 2]) and (F['hma'][i] - F['hma'][i - 2]) * s > 0,
    'UT Bot(1,10)': lambda i, s: F['ut'][i] == s,
    'Bollinger %B not stretched': lambda i, s: ok(F['bbpct'][i]) and ((F['bbpct'][i] < 0.9) if s == 1 else (F['bbpct'][i] > 0.1)),
    'Donchian(20) breakout': lambda i, s: ok(F['dch'][i - 1]) and ((C[i] > F['dch'][i - 1]) if s == 1 else (C[i] < F['dcl'][i - 1])),
}
sel, _ = run(BASE); print('%-30s %s' % ('V7.6 base', fmt(stats(sel))))
for lab, f in filters.items():
    sel, _ = run(dict(BASE, extra=f))
    print('%-30s %s' % (lab, fmt(stats(sel))))

print('-- stacking filters (how 85% would only appear on tiny samples)')
TK = filters['Ichimoku: tenkan vs kijun']; RS = filters['RSI not overextended']; DC = filters['Donchian(20) breakout']
SQ = filters['Squeeze momentum sign']; HU = filters['Hull(55) slope']; WT = filters['WaveTrend wt1>wt2']
for lab, f in (('TK', TK), ('TK + RSI ok', lambda i, s: TK(i, s) and RS(i, s)), ('TK + RSI ok + Squeeze', lambda i, s: TK(i, s) and RS(i, s) and SQ(i, s)),
               ('TK + RSI ok + Donchian', lambda i, s: TK(i, s) and RS(i, s) and DC(i, s)), ('TK + RSI ok + Hull + WT', lambda i, s: TK(i, s) and RS(i, s) and HU(i, s) and WT(i, s)),
               ('TK + RSI ok + Squeeze + Donchian + Hull', lambda i, s: TK(i, s) and RS(i, s) and SQ(i, s) and DC(i, s) and HU(i, s))):
    sel, _ = run(dict(BASE, extra=f)); print('%-40s %s' % (lab, fmt(stats(sel))))
