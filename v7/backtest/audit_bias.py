"""Audit: does the system's 4H/1H 'bias' match the trend a trader sees on the chart?
Bias = direction of the last close beyond a swings(50) pivot (LuxAlgo structure).
A swings(50) pivot on 4H is only confirmed 50 bars (~8 trading days) later."""
import datetime, collections
import data_load
from data_load import key_fixed, key_4h
from simple_engine import ctx, T, C, H, L, N, MB, B1, A
UTC = datetime.timezone.utc
bars = data_load.build()
# realised direction a chart-reader would call: next 24h and next 5 trading days move
def fwd(i, k):
    j = min(N - 1, i + k)
    return C[j] - C[i]
# 1) how often is the bias pointing the opposite way of a large realised move?
rows = []
for i in range(2000, N - 1500, 12):
    a = A[i]
    if a is None or MB[i] is None: continue
    rows.append((i, MB[i], B1[i], fwd(i, 288), fwd(i, 1440), a))
def agree(col, k):
    n = sum(1 for r in rows if abs(r[k]) > 0)
    return sum(1 for r in rows if r[col] != 0 and r[col] * r[k] > 0) / n
print('Bias vs realised direction (sampled hourly, %d samples):' % len(rows))
print('  4H bias agrees with next 24h move: %.1f%% | next 5 days: %.1f%%' % (100 * agree(1, 3), 100 * agree(1, 4)))
print('  1H bias agrees with next 24h move: %.1f%% | next 5 days: %.1f%%' % (100 * agree(2, 3), 100 * agree(2, 4)))
# 2) the September 2026 example: bias vs price
print('\nSept 2026 daily snapshot (00:00 UTC): close | 4H bias | 1H bias | 4H swing high / low used')
for d in range(1, 31, 3):
    t0 = int(datetime.datetime(2026, 9, d, tzinfo=UTC).timestamp() * 1000)
    i = next((k for k in range(N) if T[k] >= t0), None)
    if i is None: continue
    print('  2026-09-%02d  %.1f | %s | %s | %.1f / %.1f' % (d, C[i], {1: 'BULL', -1: 'BEAR', 0: '-'}[MB[i]], {1: 'BULL', -1: 'BEAR', 0: '-'}[B1[i]], ctx['macroHigh'][i], ctx['macroLow'][i]))
# 3) lag: after a 4H trend change visible as a 3% move against the bias, how long until the bias flips?
lags = []; i = 2000
while i < N - 1:
    b = MB[i]
    if b in (1, -1):
        # find move of >=3% against bias from the most recent extreme
        start = i; ext = C[i]
        j = i
        while j < N - 1 and MB[j] == b:
            ext = max(ext, C[j]) if b == 1 else min(ext, C[j])
            if (ext - C[j]) * b / ext >= 0.03:
                k = j
                while k < N - 1 and MB[k] == b: k += 1
                lags.append(((T[k] - T[j]) / 3600000, (C[j] - C[k]) * b))
                j = k; break
            j += 1
        i = j + 1
    else:
        i += 1
if lags:
    hrs = sorted(x[0] for x in lags); extra = sorted(x[1] for x in lags)
    print('\nAfter price had already moved 3%% against the 4H bias (%d cases):' % len(lags))
    print('  hours until the bias flipped: median %.0f h, p75 %.0f h' % (hrs[len(hrs) // 2], hrs[3 * len(hrs) // 4]))
    print('  further adverse move before the flip: median $%.0f' % extra[len(extra) // 2])
