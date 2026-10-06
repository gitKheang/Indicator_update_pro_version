"""Out-of-window check of the break-even modes: the V7.6 signals on 2024-01-02 .. 2026-04-02
(the history BEFORE the 6-month tuning window, never used to choose any setting)."""
import datetime, pickle
from v76_lab import setups, T, I0
from v77_lab import simulate_be, sequential, summary, fmt
UTC = datetime.timezone.utc
F = pickle.load(open('data/famous.pkl', 'rb'))
ok = lambda v: v is not None
TK = lambda i, s: ok(F['kijun'][i]) and (F['tenkan'][i] - F['kijun'][i]) * s > 0
RS = lambda i, s: ok(F['rsi'][i]) and ((F['rsi'][i] < 70) if s == 1 else (F['rsi'][i] > 30))
t0 = int(datetime.datetime(2024, 1, 2, tzinfo=UTC).timestamp() * 1000)
i0 = next(i for i in range(len(T)) if T[i] >= t0)
base, _ = setups(dict(chop_max=0, pe_after_pivot=True, extra=lambda i, s: TK(i, s) and RS(i, s)), i0=i0, i1=I0)
print('older history %s .. %s' % (datetime.datetime.fromtimestamp(T[i0] / 1000, UTC).date(), datetime.datetime.fromtimestamp(T[I0 - 1] / 1000, UTC).date()))
for lab, mode, x in (('no BE', 'none', 0), ('BE after TP1', 'after_tp1', 0), ('BE at +0.5R', 'R', 0.5), ('BE at +0.75R', 'R', 0.75), ('BE at +1.0R', 'R', 1.0)):
    print('  %-13s %s' % (lab, fmt(summary(sequential([simulate_be(r, mode, x) for r in base])))))
