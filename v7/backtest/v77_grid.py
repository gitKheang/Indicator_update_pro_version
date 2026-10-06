import pickle
from v77_lab import evaluate, fmt
F = pickle.load(open('data/famous.pkl', 'rb'))
ok = lambda v: v is not None
TK = lambda i, s: ok(F['kijun'][i]) and (F['tenkan'][i] - F['kijun'][i]) * s > 0
RS = lambda i, s: ok(F['rsi'][i]) and ((F['rsi'][i] < 70) if s == 1 else (F['rsi'][i] > 30))
POOLS = [
    ('V7.6', dict(chop_max=0, pe_after_pivot=True, extra=lambda i, s: TK(i, s) and RS(i, s))),
    ('V7.6 without TK/RSI', dict(chop_max=0, pe_after_pivot=True)),
    ('no fast filter', dict(chop_max=0, pb_max=0, pe_after_pivot=True)),
    ('V7.3-style (no ST/fast/chop)', dict(use_st=False, chop_max=0, pb_max=0, pe_after_pivot=True)),
    ('no clean room', dict(chop_max=0, pb_max=0, clean=False, pe_after_pivot=True)),
    ('1H bias only', dict(htf='1h', chop_max=0, pb_max=0, pe_after_pivot=True)),
    ('no HTF bias (ST only)', dict(htf='none', chop_max=0, pb_max=0, pe_after_pivot=True)),
]
BES = [('no BE', 'none', 0), ('BE after TP1', 'after_tp1', 0), ('BE at +0.3R', 'R', 0.3), ('BE at +0.5R', 'R', 0.5),
       ('BE at +0.75R', 'R', 0.75), ('BE at +1.0R', 'R', 1.0), ('BE: Supertrend past entry', 'st', 0),
       ('BE: Chandelier past entry', 'ce', 0), ('BE: higher low past entry', 'swing', 0)]
for pname, cfg in POOLS:
    print('=====', pname)
    for bname, mode, x in BES:
        full, tr, te = evaluate(cfg, mode, x)
        print('  %-28s 6m %s' % (bname, fmt(full)))
        print('  %-28s    last month (test): %s' % ('', fmt(te)))
