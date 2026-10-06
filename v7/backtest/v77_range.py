"""Regime switching: when 4H and 1H disagree (range / transition), try famous
mean-reversion logic instead of trend continuation. Same rules: structural SL <= $15,
TP1 1.51R, TP2 2.5R, optional BE, latest 6 months, last month = test.

Mean-reversion systems (all on the 5m chart, signals only while 4H != 1H bias):
  BB re-entry : close back inside Bollinger(20, 2) after a candle closed outside it
                (John Bollinger: a re-entry after a band walk ends signals reversion)
  RSI 30/70   : RSI(14) crosses back above 30 (long) / below 70 (short) (J. Welles Wilder)
  StochRSI    : Stochastic RSI(14,14,3,3) %K crosses %D below 20 (long) / above 80 (short)
  Pivot bounce: candle trades into the nearest 15m Pivot support (resistance) zone and
                closes back above its top (below its bottom) - the Brain's own zones
Stops: beyond the excursion extreme of the last 3 bars + 0.3 x ATR(14).
"""
import pickle
import famous, ta
from v76_lab import I0, T, H, L, C, O, N, MB, B1, X
from v77_lab import simulate_be, sequential, summary, fmt, TEST0
F = pickle.load(open('data/famous.pkl', 'rb'))
A14 = ta.atr(H, L, C, 14)
SMA20 = famous.sma(C, 20); SD20 = famous.stdev(C, 20)
RSI14 = F['rsi']
# Stochastic RSI (TradingView defaults 14,14,3,3)
_r = RSI14
_k_raw = [None] * N
for i in range(N):
    w = [v for v in _r[max(0, i - 13):i + 1] if v is not None]
    if len(w) == 14:
        lo, hi = min(w), max(w)
        _k_raw[i] = 100 * (_r[i] - lo) / (hi - lo) if hi > lo else 50.0
K = famous.sma([v if v is not None else 50.0 for v in _k_raw], 3); D = famous.sma([v if v is not None else 50.0 for v in K], 3)


def mixed(i):
    return not (MB[i] == B1[i] and MB[i] in (1, -1))


def lo3(i): return min(L[i - 2:i + 1])
def hi3(i): return max(H[i - 2:i + 1])


def candidates(name):
    sig = []
    for i in range(max(I0, 30), N - 1):
        if not mixed(i) or A14[i] is None: continue
        a = 0.3 * A14[i]
        if name == 'BB re-entry':
            if SMA20[i] is None or SD20[i] is None or SMA20[i - 1] is None or SD20[i - 1] is None: continue
            lo_b, hi_b = SMA20[i] - 2 * SD20[i], SMA20[i] + 2 * SD20[i]
            plo, phi = SMA20[i - 1] - 2 * SD20[i - 1], SMA20[i - 1] + 2 * SD20[i - 1]
            if C[i - 1] < plo and C[i] > lo_b: sig.append((i, 1, lo3(i) - a))
            if C[i - 1] > phi and C[i] < hi_b: sig.append((i, -1, hi3(i) + a))
        elif name == 'RSI 30/70':
            if RSI14[i] is None or RSI14[i - 1] is None: continue
            if RSI14[i - 1] < 30 <= RSI14[i]: sig.append((i, 1, lo3(i) - a))
            if RSI14[i - 1] > 70 >= RSI14[i]: sig.append((i, -1, hi3(i) + a))
        elif name == 'StochRSI cross':
            if None in (K[i], D[i], K[i - 1], D[i - 1]): continue
            if K[i - 1] <= D[i - 1] and K[i] > D[i] and K[i] < 20: sig.append((i, 1, lo3(i) - a))
            if K[i - 1] >= D[i - 1] and K[i] < D[i] and K[i] > 80: sig.append((i, -1, hi3(i) + a))
        elif name == 'Pivot bounce':
            pk = X['pk'][i]
            for z in pk['pSup']:
                if z and L[i] <= z[0] and C[i] > z[0] and C[i - 1] > z[1]:
                    sig.append((i, 1, min(z[1], lo3(i)) - a)); break
            for z in pk['pRes']:
                if z and H[i] >= z[1] and C[i] < z[1] and C[i - 1] < z[0]:
                    sig.append((i, -1, max(z[0], hi3(i)) + a)); break
    rows = []
    for i, s, stop in sig:
        e = C[i]; R = (e - stop) * s
        if R <= 0.5 or R > 15.0: continue
        rows.append(dict(i=i, s=s, entry=e, stop=stop, risk=R, tp1=e + s * 1.51 * R, tp2=e + s * 2.5 * R))
    return rows


if __name__ == '__main__':
    for name in ('BB re-entry', 'RSI 30/70', 'StochRSI cross', 'Pivot bounce'):
        base = candidates(name)
        print('=====', name, '(mixed 4H/1H regime only)')
        for bname, mode, x in (('no BE', 'none', 0), ('BE at +0.3R', 'R', 0.3), ('BE at +0.5R', 'R', 0.5), ('BE at +0.75R', 'R', 0.75)):
            rows = sequential([simulate_be(r, mode, x) for r in base])
            te = [r for r in rows if T[r['i']] >= TEST0]
            print('  %-14s 6m %s' % (bname, fmt(summary(rows))))
            print('  %-14s    last month %s' % ('', fmt(summary(te))))
