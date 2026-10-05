from v76_lab import run, stats, fmt, setups
from v75_lab import sequential
grid = [
    ('V7.5 (deployed)', {}),
    ('no chop filter', dict(chop_max=0)),
    ('no fast-pullback filter', dict(pb_max=0)),
    ('no chop, no fast', dict(chop_max=0, pb_max=0)),
    ('no Supertrend', dict(use_st=False)),
    ('V7.3 (no ST, chop, fast)', dict(use_st=False, chop_max=0, pb_max=0)),
    ('clean room OFF', dict(clean=False)),
    ('clean room OFF, no chop, no fast', dict(clean=False, chop_max=0, pb_max=0)),
    ('1H bias only', dict(htf='1h')),
    ('1H only, no chop, no fast', dict(htf='1h', chop_max=0, pb_max=0)),
    ('no HTF, no chop, no fast', dict(htf='none', chop_max=0, pb_max=0)),
    ('no HTF, no ST, no chop, no fast, no clean', dict(htf='none', use_st=False, chop_max=0, pb_max=0, clean=False)),
]
for lab, cfg in grid:
    rows, rej = setups(cfg)
    print('%-42s SEQ %s' % (lab, fmt(stats(sequential(rows)))))
    print('%-42s ALL %s | sl_wide %d' % ('', fmt(stats(rows)), rej.get('sl_wide', 0)))
