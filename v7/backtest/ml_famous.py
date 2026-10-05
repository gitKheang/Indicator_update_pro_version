"""Ceiling test on V7.3's own candidate signals with famous-indicator features added."""
import pickle, math, datetime
from simple_engine import run, ctx, C, O, H, L, A, T, N, MB, B1
from v72_final import V73
from famous_test import F
from ml_dataset import features as base_features
# candidate signals: V7.3 construction, every valid signal (not one-at-a-time)
import simple_engine as se
cands = []
orig_trade = None
cfg = dict(V73)
# run once with a filter that records every signal that reaches construction, then simulate each independently
from lab import construct, simulate, DEF
from phase5 import range_location
rows = []
r = run(dict(V73), show=False)
E = []
for i in range(600, N - 1):
    for s, kb in ((1, 'bull_ibreak'), (-1, 'bear_ibreak')):
        if ctx['ev'][kb][i] and MB[i] == s and B1[i] == s:
            E.append((i, s))
def famous_feats(i, s):
    a = A[i]; f = {}
    def g(k): return F[k][i]
    f['st'] = 1 if g('st') == s else -1
    f['adx'] = g('adx'); f['di'] = None if g('pdi') is None else (g('pdi') - g('mdi')) * s
    f['vwap'] = (C[i] - g('vwap')) * s / a
    f['sqz'] = 1 if g('sqz') else 0; f['sqzmom'] = None if g('sqzmom') is None else g('sqzmom') * s / a
    f['wt1'] = None if g('wt1') is None else g('wt1') * s; f['wtx'] = None if g('wt2') is None else (g('wt1') - g('wt2')) * s
    f['rf'] = 1 if g('rf') == s else -1; f['ut'] = 1 if g('ut') == s else -1
    f['cloud'] = None if g('ktop') is None else ((C[i] - g('ktop')) / a if s == 1 else (g('kbot') - C[i]) / a)
    f['tk'] = None if g('kijun') is None else (g('tenkan') - g('kijun')) * s / a
    f['hma'] = None if g('hma') is None or F['hma'][i - 2] is None else (g('hma') - F['hma'][i - 2]) * s / a
    f['rsi'] = None if g('rsi') is None else (g('rsi') - 50) * s
    f['e21_50'] = None if g('e50') is None else (g('e21') - g('e50')) * s / a
    f['e200'] = None if g('e200') is None else (C[i] - g('e200')) * s / a
    f['bbpct'] = None if g('bbpct') is None else (g('bbpct') - 0.5) * s
    return f
import simple_engine
eng_cfg = dict(simple_engine.DEF); eng_cfg.update(V73)
for i, s in E:
    # V7.3 construction exactly (protected extreme, buffer, $15 cap, clean room, TP2 cap)
    pbar = simple_engine.PTOP[i] if s == 1 else simple_engine.PBTM[i]
    ext = (min(L[pbar:i + 1]) if s == 1 else max(H[pbar:i + 1])) if pbar is not None and i - pbar <= 200 else (min(L[i - 12:i + 1]) if s == 1 else max(H[i - 12:i + 1]))
    a = A[i]
    if a is None: continue
    stop = ext - 0.3 * a if s == 1 else ext + 0.3 * a; e = C[i]; risk = (e - stop) * s
    if risk <= 0 or risk > 15 or risk < 2: continue
    tp1 = e + s * 1.51 * risk
    pool = simple_engine._pool_eng.target_pool(i, s)
    kinds = V73['clean_room']
    if any(k in kinds and ((e < p < tp1) if s == 1 else (tp1 < p < e)) for p, k in pool): continue
    zs = sorted([p for p, k in pool if k in kinds and (p - tp1) * s > 0], key=lambda p: abs(p - e))
    cap2 = e + s * 2.5 * risk
    tp2 = cap2 if not zs or (zs[0] - cap2) * s >= 0 else zs[0] - s * 0.1 * a
    if (tp2 - tp1) * s <= 0.25 * risk: continue
    tr = dict(side=s, entry=e, stop=stop, tp1=tp1, tp2=tp2, risk=risk, tp1R=1.51, tp2R=(tp2 - e) * s / risk)
    res = simulate(dict(tr), i, dict(DEF))
    if res is None or res['outcome'] == 'OPEN': continue
    f = base_features(i, s, tr, 'trend'); f.update(famous_feats(i, s))
    rows.append(dict(i=i, t=T[i], y=1 if res['tp1Hit'] else 0, f=f))
pickle.dump(rows, open('data/ml_v73_famous.pkl', 'wb'))
print('V7.3 candidate signals:', len(rows), 'base TP1 hit rate %.3f' % (sum(r['y'] for r in rows) / len(rows)))
