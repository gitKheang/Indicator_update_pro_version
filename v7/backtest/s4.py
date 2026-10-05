from simple_engine import run, metrics
Z = ('SUPPLY', 'BEAR_OB', 'PIVOT_RESISTANCE', 'DEMAND', 'BULL_OB', 'PIVOT_SUPPORT')
B = dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z, tp2_cap=0)
r = run(B, 'B'); print('   rejections', r['rej'])
d = sorted(t['exitBar'] - t['fillBar'] for t in r['trades']); print('   bars in trade median %d p75 %d p90 %d' % (d[len(d)//2], d[3*len(d)//4], d[9*len(d)//10]))
r = run(dict(B, tp2_before_zone=True, tp_front=0.1), 'B2: TP2 = 2.5R or just before the next opposing zone')
for mh in (288, 144):
    r = run(dict(B, max_hold=mh), 'B max hold %d bars' % mh)
r = run(dict(B, min_sl=1.0), 'B min SL $1')
