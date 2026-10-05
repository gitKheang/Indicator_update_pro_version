"""Feature scan on the latest-6-month setups (V7.5 rules without the chop filter)."""
import itertools
from v76_lab import setups, stats, fmt, SPLIT6
from v75_lab import features, sequential, T, wr, pf
from v75_intermarket import inter_features
rows, _ = setups(dict(chop_max=0))
wide, _ = setups(dict(chop_max=0, pb_max=0, use_st=False))      # broader V7.3-style base for more data
for r in rows + wide:
    r['f'] = features(r); r['f'].update(inter_features(r))
g = lambda r, k, d=None: r['f'].get(k) if r['f'].get(k) is not None else d
TESTS = {
    'tight (impulse < 2 ATR)': lambda r: g(r, 'impulse_atr', 99) < 2.0,
    'SL < 2.5 ATR89': lambda r: r['f']['sl_atr89'] < 2.5,
    'calm1h (chop < 50)': lambda r: g(r, 'chop_1h', 99) < 50,
    '1H Supertrend agrees': lambda r: g(r, 'st_1h', 0) == 1,
    '15m Supertrend agrees': lambda r: g(r, 'st_15m', 0) == 1,
    '4H Supertrend agrees': lambda r: g(r, 'st_4h', 0) == 1,
    'room >= 3R': lambda r: r['f']['room_R'] >= 3,
    'longs only': lambda r: r['s'] == 1,
    'pb <= 8 bars': lambda r: g(r, 'pb_bars', 99) <= 8,
    'silver confirms break': lambda r: g(r, 'silver_break', 0) == 1,
    'dollar same direction': lambda r: g(r, 'dxy_st_opp', 1) == 0,
    'NY session (07-16 NY)': lambda r: 7 <= g(r, 'ny_hour', 0) < 16,
    'day direction agrees': lambda r: g(r, 'day_dir', 0) == 1,
    'not extended (< 1.5 ATR from EMA20)': lambda r: g(r, 'ext_ema20_atr', 9) < 1.5,
}
def line(lab, sel):
    tr = [r for r in sel if T[r['i']] < SPLIT6]; te = [r for r in sel if T[r['i']] >= SPLIT6]
    return '%-38s n=%3d WR %5.1f%% PF %5.2f | train n=%3d %5.1f%% | test n=%2d %5.1f%%' % (lab, len(sel), 100 * wr(sel), pf(sel), len(tr), 100 * wr(tr), len(te), 100 * wr(te))
for base_lab, base in (('V7.5 w/o chop (each setup alone)', rows), ('V7.3-style base (each setup alone)', wide)):
    print('==', line(base_lab, base))
    for lab, f in TESTS.items():
        sel = [r for r in base if f(r)]
        if len(sel) >= 8: print('  ', line(lab, sel))
