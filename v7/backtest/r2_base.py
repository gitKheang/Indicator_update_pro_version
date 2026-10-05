from r2_common import *
from v71_rules import v71_hooks, V71_CONFIG
# V7.1 as deployed (with BE) for reference
e = Engine(ctx, V71_CONFIG, hooks=v71_hooks()).run(); report(e, V71_CONFIG, 'V7.1 deployed (BE, 1R/2.5R)')
# V7.1 signals, fixed 1.5R/2.5R TP, no BE, stop cap $15
for lab, kw in (('struct SL aoi_or_A +0.5ATR, TP1 first struct>1.5R', {}),
                ('  same, clean room', dict(clean_room=True)),
                ('  SL beyond A only', dict(sl_mode='A')),
                ('  SL beyond AOI only', dict(sl_mode='aoi'))):
    run(structural_hook(**kw), confirm=body_confirm(0.3), label=lab)
