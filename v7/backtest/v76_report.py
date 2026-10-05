"""V7.6 report: latest 6 months (train Apr-Jul, test Aug-Oct) + older-data robustness."""
import pickle, datetime, collections
from v76_lab import setups, stats, fmt, I0, T, DAYS6
from v75_lab import sequential, wr, pf
F = pickle.load(open('data/famous.pkl', 'rb'))
ok = lambda v: v is not None
TK = lambda i, s: ok(F['kijun'][i]) and (F['tenkan'][i] - F['kijun'][i]) * s > 0
RS = lambda i, s: ok(F['rsi'][i]) and ((F['rsi'][i] < 70) if s == 1 else (F['rsi'][i] > 30))
V76 = dict(chop_max=0, pe_after_pivot=True, extra=lambda i, s: TK(i, s) and RS(i, s))
UTC = datetime.timezone.utc
def show(lab, cfg):
    rows, rej = setups(cfg); seq = sequential(rows)
    print('==', lab); print('   latest 6 months', fmt(stats(seq)))
    oc = collections.Counter('TP2' if r['outcome'] == 'TP2' else 'TP1 then stop' if r['outcome'] == 'STOP_AFTER_TP1' else 'SL' for r in seq)
    print('   outcomes', dict(oc), '| median SL $%.1f max SL $%.1f | min TP1 %.2fR' % (sorted(r['risk'] for r in seq)[len(seq) // 2], max(r['risk'] for r in seq), min((r['tp1'] - r['entry']) * r['s'] / r['risk'] for r in seq)))
    old = sequential(setups(cfg, i0=600, i1=I0)[0])
    print('   older data 2024-01..2026-04: n=%d WR %.1f%% PF %.2f net %+.1fR' % (len(old), 100 * wr(old), pf(old), sum(r['R'] for r in old)))
    return seq
show('V7.5 (as deployed before)', {})
seq = show('V7.6 (latest-6-month tuning)', V76)
print('   trades:')
for r in seq:
    print('     %s %s entry %.2f SL $%.1f TP1 %.2fR -> %s' % (datetime.datetime.fromtimestamp(T[r['i']] / 1000, UTC).strftime('%Y-%m-%d %H:%M'), 'L' if r['s'] == 1 else 'S', r['entry'], r['risk'], (r['tp1'] - r['entry']) * r['s'] / r['risk'], r['outcome']))
