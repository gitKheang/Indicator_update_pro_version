import datetime, collections
from simple_engine import run, metrics, A, T, N
from v72_final import V72
UTC = datetime.timezone.utc
def monthly(r):
    g = collections.Counter(datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).strftime('%Y-%m') for t in r['trades'])
    return ' '.join('%s:%d' % (k[2:], g[k]) for k in sorted(g) if k >= '2025-07')
s26 = next(i for i in range(N) if T[i] >= int(datetime.datetime(2026, 1, 1, tzinfo=UTC).timestamp() * 1000))
r = run(V72, show=False); print('ON  monthly', monthly(r))
r26 = run(V72, show=False, start=s26); print('ON  2026 rejections', r26['rej'])
r = run(dict(V72, clean_room=()), show=False); print('OFF monthly', monthly(r))
r26 = run(dict(V72, clean_room=()), show=False, start=s26); print('OFF 2026 rejections', r26['rej'])
