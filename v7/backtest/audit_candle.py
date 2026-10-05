"""Audit: does the shape of the 5m break candle separate V7.4 winners from losers?
(LuxAlgo's optional 'internal confluence filter' compares the candle's wicks.)"""
from simple_engine import run, H, L, C, O, A
from famous_test import line
from v72_final import v74
base = v74(); st = base['filter']
up = lambda i: H[i] - max(C[i], O[i]); dn = lambda i: min(C[i], O[i]) - L[i]
tests = {
    'LuxAlgo confluence (long: upper wick > lower)': lambda i, s: (up(i) > dn(i)) if s == 1 else (up(i) < dn(i)),
    'Strong close (wick against trade < wick with)': lambda i, s: (up(i) < dn(i)) if s == 1 else (up(i) > dn(i)),
    'Body >= 0.5 ATR in trade direction': lambda i, s: (C[i] - O[i]) * s >= 0.5 * A[i],
    'Body <= 1.0 ATR (not a spike)': lambda i, s: abs(C[i] - O[i]) <= 1.0 * A[i],
    'Close in outer third of range': lambda i, s: H[i] > L[i] and ((C[i] - L[i]) / (H[i] - L[i]) >= 2 / 3 if s == 1 else (H[i] - C[i]) / (H[i] - L[i]) >= 2 / 3),
}
for lab, f in tests.items():
    line('V7.4 + ' + lab, run(dict(base, filter=lambda i, s, f=f: st(i, s) and f(i, s)), show=False))
