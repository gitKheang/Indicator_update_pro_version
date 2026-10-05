"""Build a labelled dataset of every candidate setup for the ML ceiling test."""
import pickle, math, datetime
from lab_events import *
from phase5 import range_location

def features(i, s, tr, fam):
    a = A[i]; pk = ctx['pk'][i]
    def adj(x): return None if x is None else x * s
    past = [x for x in A[max(0, i - 2880):i:96] if x]
    f = {}
    f['side'] = s
    f['fam_' + fam] = 1
    f['mb'] = 1 if MB[i] == s else (-1 if MB[i] == -s else 0)
    f['b1'] = 1 if B1[i] == s else (-1 if B1[i] == -s else 0)
    f['swingTrend'] = 1 if ctx['trend'][i] == s else -1
    f['itrend'] = 1 if ctx['itrend'][i] == s else -1
    f['loc15'] = range_location(C[i], pk['swingHigh'], pk['swingLow']) * s
    f['loc4h'] = range_location(C[i], ctx['macroHigh'][i], ctx['macroLow'][i]) * s
    hm = ET_H[i] + ET_M[i] / 60
    f['hsin'] = math.sin(2 * math.pi * hm / 24); f['hcos'] = math.cos(2 * math.pi * hm / 24)
    f['hour'] = ET_H[i]
    f['dow'] = datetime.datetime.fromtimestamp(T[i] / 1000, NY).weekday()
    f['volreg'] = a / (sum(past) / len(past)) if past else 1.0
    f['atr_ratio'] = (A14[i] / a) if A14[i] else 1.0
    f['riskATR'] = tr['risk'] / a; f['risk$'] = tr['risk']
    f['tp1R'] = tr['tp1R']; f['tp2R'] = tr['tp2R']
    f['body'] = (C[i] - O[i]) * s / a; f['range'] = (H[i] - L[i]) / a
    for k in (12, 48, 288):
        f['mom%d' % k] = (C[i] - C[i - k]) * s / a if i >= k else 0.0
    f['dOpen'] = (C[i] - DAY_OPEN[i]) * s / a if DAY_OPEN[i] else 0.0
    f['dMid'] = (C[i] - MID_OPEN[i]) * s / a if MID_OPEN[i] else 0.0
    if ASIA_H[i] is not None:
        f['asiaRange'] = (ASIA_H[i] - ASIA_L[i]) / a
        f['asiaPos'] = ((C[i] - ASIA_L[i]) / max(ASIA_H[i] - ASIA_L[i], 1e-6) - 0.5) * s
    f['dPDH'] = ((ctx['pdh'][i] - C[i]) / a) if ctx['pdh'][i] else None
    f['dPDL'] = ((C[i] - ctx['pdl'][i]) / a) if ctx['pdl'][i] else None
    if s == -1: f['dPDH'], f['dPDL'] = f['dPDL'], f['dPDH']
    e = tr['entry']; risk = tr['risk']
    opp = [p for p, k in levels(i, s, 'zones') if 0 < (p - e) * s]
    liq = [p for p, k in levels(i, s, 'liq') if 0 < (p - e) * s]
    f['nZones2R'] = sum(1 for p in opp if (p - e) * s <= 2 * risk)
    f['nearZoneR'] = min(((p - e) * s / risk for p in opp), default=10)
    f['nLiq15R'] = sum(1 for p in liq if (p - e) * s <= 1.5 * risk)
    f['nearLiqR'] = min(((p - e) * s / risk for p in liq), default=10)
    lo12, hi12 = min(L[i - 12:i + 1]), max(H[i - 12:i + 1])
    f['pullback12'] = ((hi12 - C[i]) if s == 1 else (C[i] - lo12)) / a
    f['sinceExt'] = (C[i] - (lo12 if s == 1 else hi12)) * s / a
    f['kz'] = 1 if (in_et(i, 2, 0, 5, 0) or in_et(i, 7, 0, 11, 0)) else 0
    return f

def build(tp_mode='struct'):
    fams = {'trend': ev_trend(), 'trend4h': ev_trend(htf='4h'), 'sweep': ev_sweep(), 'asia': ev_asia_fb(),
            'fvg': ev_fvg(), 'orb': ev_orb(), 'aoi': ev_aoi()}
    rows = []
    for fam, E in fams.items():
        cfg = dict(DEF); cfg['entry'] = 'limit' if fam == 'fvg' else 'close'
        if tp_mode == 'fixed151':
            cfg['tp_kinds'] = 'none'
        for evt in E:
            i, s, inval = evt[0], evt[1], evt[2]
            ent = evt[3] if fam == 'fvg' else None
            if tp_mode == 'struct':
                tr, why = construct(i, s, inval, cfg, ent)
            else:
                a = A[i]; e = C[i] if ent is None else ent
                stop = inval - s * cfg['buf_k'] * a; risk = (e - stop) * s
                if risk <= 0 or risk > 15 or risk < 2: continue
                tr = dict(side=s, entry=e, stop=stop, tp1=e + s * 1.51 * risk, tp2=e + s * 2.5 * risk, risk=risk, tp1R=1.51, tp2R=2.5); why = None
            if tr is None: continue
            res = simulate(dict(tr), i, cfg)
            if res is None or res['outcome'] == 'OPEN': continue
            f = features(i, s, tr, fam)
            rows.append(dict(i=i, t=T[i], fam=fam, y=1 if res['tp1Hit'] else 0, exit=res['exit'], outcome=res['outcome'],
                             tp1R=tr['tp1R'], tp2R=tr['tp2R'], risk=tr['risk'], f=f))
    return rows

if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'struct'
    rows = build(mode)
    pickle.dump(rows, open('data/ml_%s.pkl' % mode, 'wb'))
    print(mode, 'rows', len(rows), 'base WR %.3f' % (sum(r['y'] for r in rows) / len(rows)))
