import datetime, collections
from simple_engine import run, metrics, fmt
from v72_final import V72
UTC = datetime.timezone.utc
def monthly(r):
    g = collections.Counter(datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).strftime('%Y-%m') for t in r['trades'])
    return ' '.join('%s:%d' % (k[2:], g[k]) for k in sorted(g) if k >= '2026-01')
for lab, kw in (('close entry, 4H+1H, clean ON (V72)', {}),
                ('close entry, 4H only, clean ON', dict(htf='4h')),
                ('retest limit, 4H+1H, clean ON', dict(entry_mode='retest')),
                ('retest limit, 4H only, clean ON', dict(entry_mode='retest', htf='4h')),
                ('retest limit, 4H+1H, clean OFF', dict(entry_mode='retest', clean_room=())),
                ('close entry, 4H only, clean OFF', dict(htf='4h', clean_room=()))):
    r = run(dict(V72, **kw), lab)
    print('    2026 monthly:', monthly(r), '| rej', {k: v for k, v in r['rej'].items() if k in ('missed', 'expired', 'sl_wide', 'blocked')})
