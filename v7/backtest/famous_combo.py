import pickle, datetime, collections
from simple_engine import run, metrics, C
from r2_common import SPLIT
from v72_final import V73
from famous_test import F, filters, line
ST = filters['Supertrend(10,3) agrees']; IC = filters['Ichimoku: price beyond cloud']; TK = filters['Ichimoku: tenkan vs kijun agrees']
VW = filters['Session VWAP side (TWAP proxy)']; RF = filters['Range Filter(100,3) agrees']
combos = {
    'ST + Ichimoku cloud': lambda i, s: ST(i, s) and IC(i, s),
    'ST + VWAP': lambda i, s: ST(i, s) and VW(i, s),
    'Ichimoku cloud + VWAP': lambda i, s: IC(i, s) and VW(i, s),
    'ST + cloud + VWAP': lambda i, s: ST(i, s) and IC(i, s) and VW(i, s),
    'ST + cloud + VWAP + RF': lambda i, s: ST(i, s) and IC(i, s) and VW(i, s) and RF(i, s),
    'ST + cloud + TK + VWAP + RF (all 5)': lambda i, s: ST(i, s) and IC(i, s) and TK(i, s) and VW(i, s) and RF(i, s),
    '2 of {ST, cloud, VWAP}': lambda i, s: (ST(i, s) + IC(i, s) + VW(i, s)) >= 2,
}
for lab, f in combos.items():
    line(lab, run(dict(V73, filter=f), show=False))
