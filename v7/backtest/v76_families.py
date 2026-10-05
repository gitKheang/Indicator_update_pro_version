"""Famous free TradingView indicators as complete signal systems, latest 6 months only.

Every system uses the project rules: structural stop <= $15 (else NO TRADE), TP1 = 1.51R,
TP2 = 2.5R, no break-even, stop first when one candle touches both, $0.30 cost.
Entry at the signal candle close. One position at a time ("SEQ") and every signal ("ALL").
Optional trend gate = 4H + 1H major structure agree (the V7 bias).
"""
import math
from v76_lab import I0, T, H, L, C, O, A, N, MB, B1, DAYS6, SPLIT6, stats, fmt
from v75_lab import simulate, sequential, supertrend, ema, ST_LINE, ST_SIDE
import famous, pickle, os
F = pickle.load(open('data/famous.pkl', 'rb'))


def sma(x, n):
    out = [None] * len(x); s = 0.0
    for i, v in enumerate(x):
        s += v
        if i >= n: s -= x[i - n]
        if i >= n - 1: out[i] = s / n
    return out


def rsi_n(x, n):
    return famous.rsi(x, n)


def lowest(a, i, n): return min(a[max(0, i - n + 1):i + 1])
def highest(a, i, n): return max(a[max(0, i - n + 1):i + 1])


def build(signals, trend=False, max_sl=15.0, tp1r=1.51, tp2r=2.5, cost=0.3):
    """signals: list of (i, side, stop). Applies the rules and simulates each one."""
    out = []
    for i, s, stop in signals:
        if i < I0 or i >= N - 1 or stop is None: continue
        if trend and not (MB[i] == s and B1[i] == s): continue
        entry = C[i]; risk = (entry - stop) * s
        if risk <= 0.5 or risk > max_sl: continue
        st = dict(i=i, s=s, entry=entry, stop=stop, tp1=entry + s * tp1r * risk, tp2=entry + s * tp2r * risk, risk=risk)
        simulate(st, cost); out.append(st)
    return out


A14 = famous.ta.atr(H, L, C, 14)
E200 = F['e200']; E50 = F['e50']; E21 = F['e21']; E9 = F['e9']
FAM = {}

# 1. Supertrend(10,3) flip, stop at the new Supertrend line
sig = []
for i in range(max(I0, 2), N):
    if ST_SIDE[i] != ST_SIDE[i - 1] and ST_SIDE[i] != 0:
        sig.append((i, ST_SIDE[i], ST_LINE[i]))
FAM['Supertrend(10,3) flip'] = sig

# 2. UT Bot (1, 10) flip, stop beyond the last 5-bar extreme + 0.3 ATR14
sig = [(i, F['ut'][i], (lowest(L, i, 5) - 0.3 * A14[i]) if F['ut'][i] == 1 else (highest(H, i, 5) + 0.3 * A14[i]))
       for i in range(max(I0, 1), N) if F['ut'][i] != F['ut'][i - 1] and F['ut'][i] != 0 and A14[i]]
FAM['UT Bot(1,10) flip'] = sig

# 3. Range Filter (100,3) direction change, stop beyond the 10-bar extreme
sig = [(i, F['rf'][i], (lowest(L, i, 10) - 0.3 * A14[i]) if F['rf'][i] == 1 else (highest(H, i, 10) + 0.3 * A14[i]))
       for i in range(max(I0, 1), N) if F['rf'][i] != F['rf'][i - 1] and F['rf'][i] != 0 and A14[i]]
FAM['Range Filter(100,3) flip'] = sig

# 4. Donchian(20) breakout (Turtle), stop at the 10-bar opposite extreme
sig = []
for i in range(max(I0, 21), N):
    if F['dch'][i - 1] is not None and C[i] > F['dch'][i - 1] and C[i - 1] <= F['dch'][i - 2]:
        sig.append((i, 1, lowest(L, i, 10) - 0.3 * A14[i]))
    if F['dcl'][i - 1] is not None and C[i] < F['dcl'][i - 1] and C[i - 1] >= F['dcl'][i - 2]:
        sig.append((i, -1, highest(H, i, 10) + 0.3 * A14[i]))
FAM['Donchian(20) breakout'] = sig

# 5. EMA 9/21 cross in the EMA200 direction, stop beyond the 10-bar extreme
sig = []
for i in range(max(I0, 2), N):
    if E200[i] is None: continue
    if E9[i] > E21[i] and E9[i - 1] <= E21[i - 1] and C[i] > E200[i]:
        sig.append((i, 1, lowest(L, i, 10) - 0.3 * A14[i]))
    if E9[i] < E21[i] and E9[i - 1] >= E21[i - 1] and C[i] < E200[i]:
        sig.append((i, -1, highest(H, i, 10) + 0.3 * A14[i]))
FAM['EMA 9/21 cross with EMA200'] = sig

# 6. Squeeze Momentum (LazyBear) release with momentum sign
sig = []
for i in range(max(I0, 2), N):
    if F['sqz'][i - 1] and not F['sqz'][i] and F['sqzmom'][i] is not None and F['sqzmom'][i] != 0:
        s = 1 if F['sqzmom'][i] > 0 else -1
        sig.append((i, s, (lowest(L, i, 10) - 0.3 * A14[i]) if s == 1 else (highest(H, i, 10) + 0.3 * A14[i])))
FAM['Squeeze Momentum release'] = sig

# 7. Connors RSI(2) pullback in the SMA200 trend (famous high-win-rate system)
R2 = rsi_n(C, 2); S200 = sma(C, 200)
sig = []
for i in range(max(I0, 1), N):
    if R2[i] is None or S200[i] is None: continue
    if C[i] > S200[i] and R2[i] < 10: sig.append((i, 1, lowest(L, i, 5) - 0.3 * A14[i]))
    if C[i] < S200[i] and R2[i] > 90: sig.append((i, -1, highest(H, i, 5) + 0.3 * A14[i]))
FAM['Connors RSI(2) in SMA200 trend'] = sig

# 8. Bollinger(20,2) re-entry in the EMA50 trend (touch outside, close back inside)
B20 = sma(C, 20); SD = famous.stdev(C, 20)
sig = []
for i in range(max(I0, 1), N):
    if B20[i] is None or SD[i] is None or E50[i] is None: continue
    lo, hi = B20[i] - 2 * SD[i], B20[i] + 2 * SD[i]
    if C[i] > E50[i] and L[i] < lo and C[i] > lo: sig.append((i, 1, L[i] - 0.3 * A14[i]))
    if C[i] < E50[i] and H[i] > hi and C[i] < hi: sig.append((i, -1, H[i] + 0.3 * A14[i]))
FAM['Bollinger re-entry in EMA50 trend'] = sig

# 9. EMA20 pullback in a stacked trend (9>21>50), bullish/bearish close after touching EMA20
E20 = ema(C, 20)
sig = []
for i in range(max(I0, 1), N):
    if E50[i] is None: continue
    if E9[i] > E21[i] > E50[i] and L[i] <= E20[i] and C[i] > O[i] and C[i] > E20[i]:
        sig.append((i, 1, lowest(L, i, 3) - 0.3 * A14[i]))
    if E9[i] < E21[i] < E50[i] and H[i] >= E20[i] and C[i] < O[i] and C[i] < E20[i]:
        sig.append((i, -1, highest(H, i, 3) + 0.3 * A14[i]))
FAM['EMA20 pullback in stacked trend'] = sig

# 10. Hull(55) slope turn
HM = F['hma']
sig = []
for i in range(max(I0, 3), N):
    if None in (HM[i], HM[i - 1], HM[i - 2]): continue
    up = HM[i] > HM[i - 1] and HM[i - 1] <= HM[i - 2]; dn = HM[i] < HM[i - 1] and HM[i - 1] >= HM[i - 2]
    if up: sig.append((i, 1, lowest(L, i, 10) - 0.3 * A14[i]))
    if dn: sig.append((i, -1, highest(H, i, 10) + 0.3 * A14[i]))
FAM['Hull(55) turn'] = sig

if __name__ == '__main__':
    print('6 months: %d trading days. Need >= 200 trades (1.54/day) at ~85%%.' % DAYS6)
    for name, sig in FAM.items():
        for trend in (False, True):
            rows = build(sig, trend=trend)
            seq = sequential(rows)
            print('%-36s %-9s SEQ %s' % (name, 'trend' if trend else 'no gate', fmt(stats(seq))))
            print('%-46s ALL %s' % ('', fmt(stats(rows))))
