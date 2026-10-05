import datetime, collections
from simple_engine import run, metrics, fmt, ctx, H, L, C, A, T
UTC = datetime.timezone.utc
Z_OPP = ('SUPPLY', 'BEAR_OB', 'PIVOT_RESISTANCE', 'DEMAND', 'BULL_OB', 'PIVOT_SUPPORT')
Z_FVG = Z_OPP + ('BEAR_FVG', 'BULL_FVG')
Z_ALL = Z_FVG + ('EQH', 'EQL', 'PDH', 'PDL', 'PWH', 'PWL', 'PMH', 'PML', '15M_SWING_HIGH', '15M_SWING_LOW', '4H_SWING_HIGH', '4H_SWING_LOW')
def yearly(res):
    g = collections.defaultdict(list)
    for t in res['trades']: g[datetime.datetime.fromtimestamp(t['readyTime'] / 1000, UTC).year].append(t)
    for y in sorted(g): print('     %d' % y, fmt(metrics(g[y], res['cfg'])))
r = run(dict(tp_mode='fixed', fixed_tp1=1.51, fixed_tp2=2.5), 'A: no room check, TP 1.51/2.5'); yearly(r)
r = run(dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z_OPP, tp2_cap=0), 'B: clean room (opposing D/S/OB/pivot), TP 1.51/2.5'); yearly(r)
r = run(dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z_FVG, tp2_cap=0), 'C: clean room incl. FVG, TP 1.51/2.5'); yearly(r)
r = run(dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z_ALL, tp2_cap=0), 'D: clean room incl. all liquidity, TP 1.51/2.5'); yearly(r)
r = run(dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z_OPP), 'E: clean room, TP2 structural (fallback 2.5R)'); yearly(r)
# AOI context: the protected swing extreme touched a fresh same-side 15m zone
def aoi_ctx(i, s):
    pk = ctx['pk'][i]
    fams = ('demand', 'bullOb', 'pSup', 'bullFvg') if s == 1 else ('supply', 'bearOb', 'pRes', 'bearFvg')
    lo, hi = min(L[i - 24:i + 1]), max(H[i - 24:i + 1])
    for f in fams:
        for z in pk[f]:
            if z and z[4] and lo <= z[0] and hi >= z[1] and ((z[0] <= C[i]) if s == 1 else (z[1] >= C[i])):
                return True
    return False
r = run(dict(tp_mode='fixed', fixed_tp1=1.51, fixed_tp2=2.5, filter=aoi_ctx), 'F: A + pullback touched fresh 15m zone')
r = run(dict(tp_mode='hybrid', fixed_tp1=1.51, fixed_tp2=2.5, tp2_fallback=True, clean_room=Z_OPP, tp2_cap=0, filter=aoi_ctx), 'G: B + pullback touched fresh 15m zone')
