"""V7.4 extras for the notes: clean room OFF frequency, and the recent trade list
(to compare with the TradingView chart scoreboard)."""
import datetime
from simple_engine import run, metrics, fmt
from r2_common import SPLIT, DAYS_ALL
from v72_final import v74
UTC = datetime.timezone.utc
base = v74()
r = run(dict(base, clean_room=None, tp2_before_zone=False, tp2_fallback=True, tp_mode='hybrid'), show=False)
tr = r['trades']; c = r['cfg']
print('V7.4 clean room OFF', fmt(metrics(tr, c, DAYS_ALL)))
print('   IS ', fmt(metrics([t for t in tr if t['readyTime'] < SPLIT], c)))
print('   OOS', fmt(metrics([t for t in tr if t['readyTime'] >= SPLIT], c)))
r = run(base, show=False)
w0 = int(datetime.datetime(2026, 7, 20, tzinfo=UTC).timestamp() * 1000)
for t in r['trades']:
    if t['readyTime'] >= w0:
        # UTC+7 to match the chart's clock
        print('  ', datetime.datetime.fromtimestamp(t['readyTime'] / 1000 + 7 * 3600, UTC).strftime('%m-%d %H:%M'), 'L' if t['side'] == 1 else 'S', round(t['entry'], 2), 'risk $%.1f' % t['risk'], t['outcome'])
