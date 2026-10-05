from simple_engine import run
from v72_final import V73
from famous_test import line
import famous
for per, m in ((10, 2.0), (10, 3.0), (10, 4.0), (7, 3.0), (14, 3.0), (20, 3.0)):
    d = famous.supertrend(per, m)
    line('Supertrend(%d,%.0f) agrees' % (per, m), run(dict(V73, filter=lambda i, s, d=d: d[i] == s), show=False))
