from simple_engine import run
F = dict(tp_mode='fixed', fixed_tp1=1.51, fixed_tp2=2.5)
run(dict(tp_mode='hybrid', fixed_tp1=1.51, tp2_fallback=True), 'hybrid: TP1 1.51R, TP2 next structure (fallback 2.5R)')
run(dict(tp_mode='hybrid', fixed_tp1=1.51, tp2_fallback=False), 'hybrid: TP1 1.51R, TP2 next structure (no fallback)')
OPP_Z = ('SUPPLY', 'BEAR_OB', 'PIVOT_RESISTANCE', 'DEMAND', 'BULL_OB', 'PIVOT_SUPPORT')
run(dict(tp_mode='hybrid', fixed_tp1=1.51, tp2_fallback=True, clean_room=OPP_Z), 'hybrid + no opposing D/S/OB/pivot zone before TP1')
for b in (0.1, 0.5, 0.8):
    run(dict(F, buf=b), 'fixed 1.51/2.5, buffer %.1f ATR89' % b)
for b in (0.5, 1.0):
    run(dict(F, buf=b, buf_src='atr14'), 'fixed 1.51/2.5, buffer %.1f ATR14' % b)
run(dict(F, max_sl=10.0), 'fixed, max SL $10')
run(dict(F, min_sl=4.0), 'fixed, min SL $4')
run(dict(F, body=0.3), 'fixed, body >= 0.3 ATR')
run(dict(F, fixed_tp2=2.0), 'fixed 1.51/2.0')
run(dict(F, fixed_tp2=3.0), 'fixed 1.51/3.0')
