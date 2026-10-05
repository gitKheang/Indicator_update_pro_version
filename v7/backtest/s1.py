from simple_engine import run
run({}, 'trend break (4H+1H), protected-swing SL +0.3ATR, TP1 first struct >1.5R, TP2 next')
run(dict(tp_mode='fixed', fixed_tp1=1.51, fixed_tp2=2.5), '  same signals, fixed TP1 1.51R / TP2 2.5R')
run(dict(sl_ref='last12'), '  SL ref = lowest of last 12 bars')
run(dict(trigger=('ichoch',)), '  trigger internal CHoCH only')
run(dict(htf='4h'), '  4H bias only')
run(dict(htf='1h'), '  1H bias only')
