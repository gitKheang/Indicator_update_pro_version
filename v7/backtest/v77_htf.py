"""V7.7 diagnosis: the 4H major structure (LuxAlgo 50-bar swings on 4H) is the engine that
stops all trading in the last month. It stayed bullish from the August rally while price
fell $280 (Sep 2 - Oct 4): a 50-bar 4H pivot needs ~8 trading days on each side, so the
bias flips only after price closes beyond an old, distant swing.

Test: replace it with faster, famous higher-timeframe trend filters (completed bars only):
  4H Supertrend(10,3) side, 4H close vs EMA50, 1H Supertrend(10,3) side.
Everything else = V7.6 (5m internal BOS, 5m Supertrend, fast pullback <= 11 bars,
Ichimoku TK, RSI cap, clean room, structural stop <= $15, TP1 1.51R, TP2 > TP1).
Train = 2026-04-05 .. 2026-09-04, test = 2026-09-05 .. 2026-10-04, one position at a time.
"""
import pickle
from v76_lab import setups, T, MB, B1
from v75_lab import HTF
from v77_lab import simulate_be, sequential, summary, fmt, TEST0
F = pickle.load(open('data/famous.pkl', 'rb'))
ok = lambda v: v is not None
TK = lambda i, s: ok(F['kijun'][i]) and (F['tenkan'][i] - F['kijun'][i]) * s > 0
RS = lambda i, s: ok(F['rsi'][i]) and ((F['rsi'][i] < 70) if s == 1 else (F['rsi'][i] > 30))
MOM = lambda i, s: TK(i, s) and RS(i, s)


def htf_side(name, kind):
    d = HTF[name]
    def f(i):
        k = d['done'][i]
        if k is None: return 0
        if kind == 'st': return d['st'][k]
        e = d['ema50'][k]
        return 0 if e is None else (1 if d['c'][k] > e else -1)
    return f


ST4, EM4, ST1 = htf_side('4h', 'st'), htf_side('4h', 'ema'), htf_side('1h', 'st')
BIAS = {
    '4H+1H structure (V7.6)':        None,
    '1H structure + 4H Supertrend':  lambda i, s: B1[i] == s and ST4(i) == s,
    '1H structure + 4H EMA50':       lambda i, s: B1[i] == s and EM4(i) == s,
    '1H structure + 1H Supertrend':  lambda i, s: B1[i] == s and ST1(i) == s,
    '4H Supertrend + 1H Supertrend': lambda i, s: ST4(i) == s and ST1(i) == s,
    '1H structure only':             lambda i, s: B1[i] == s,
}
BES = [('no BE', 'none', 0), ('BE +0.75R', 'R', 0.75), ('BE after TP1', 'after_tp1', 0)]


def pool(bias, fast=True, mom=True):
    cfg = dict(chop_max=0, pe_after_pivot=True)
    if not fast: cfg['pb_max'] = 0
    if bias is None:
        if mom: cfg['extra'] = MOM
    else:
        cfg['htf'] = 'none'
        cfg['extra'] = (lambda i, s: bias(i, s) and MOM(i, s)) if mom else bias
    return setups(cfg)[0]


if __name__ == '__main__':
    for fast, mom, tag in ((True, True, 'V7.6 entry filters'), (False, True, 'no fast-pullback filter'), (False, False, 'no fast / no TK-RSI')):
        print('######', tag)
        for name, bias in BIAS.items():
            base = pool(bias, fast, mom)
            print('=====', name)
            for bname, mode, x in BES:
                rows = sequential([simulate_be(r, mode, x) for r in base])
                tr = [r for r in rows if T[r['i']] < TEST0]; te = [r for r in rows if T[r['i']] >= TEST0]
                print('  %-13s 6m    %s' % (bname, fmt(summary(rows))))
                print('  %-13s train %s' % ('', fmt(summary(tr))))
                print('  %-13s test  %s' % ('', fmt(summary(te))))
