"""ML ceiling on the latest 6 months: can ANY combination of ~40 features pick
~1.5 trades/day at 85%? Train Apr-Jul, test Aug-Oct (unseen)."""
import pickle, numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from v76_lab import setups, T, SPLIT6, DAYS6, I0, N
from v75_lab import features
from v75_intermarket import inter_features
F = pickle.load(open('data/famous.pkl', 'rb'))
rows, _ = setups(dict(htf='none', use_st=False, pb_max=0, chop_max=0, pe_after_pivot=True))   # broad pool, clean room on
for r in rows:
    f = features(r); f.update(inter_features(r)); i = r['i']; s = r['s']
    for k in ('rsi', 'adx', 'wt1', 'sqzmom', 'bbpct'):
        v = F[k][i]; f['ind_' + k] = (v * s if k in ('wt1', 'sqzmom') else v) if v is not None else None
    f['ind_tk'] = 1 if F['kijun'][i] is not None and (F['tenkan'][i] - F['kijun'][i]) * s > 0 else 0
    f['ind_rf'] = 1 if F['rf'][i] == s else 0; f['ind_ut'] = 1 if F['ut'][i] == s else 0
    f['htf4'] = 1 if r['f' if False else 's'] and __import__('v76_lab').MB[i] == s else 0
    f['htf1'] = 1 if __import__('v76_lab').B1[i] == s else 0
    r['f'] = f
keys = sorted({k for r in rows for k in r['f']})
X = np.array([[np.nan if r['f'].get(k) is None else float(r['f'][k]) for k in keys] for r in rows]); y = np.array([1 if r['win'] else 0 for r in rows])
tr = np.array([T[r['i']] < SPLIT6 for r in rows]); te = ~tr
test_days = DAYS6 * te.sum() / max(1, len(rows)) if False else 45
print('pool %d setups (%.1f/day) | features %d | train %d (WR %.1f%%) | test %d (WR %.1f%%)' % (len(rows), len(rows) / DAYS6, len(keys), tr.sum(), 100 * y[tr].mean(), te.sum(), 100 * y[te].mean()))
gb = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=15, random_state=1).fit(X[tr], y[tr])
Xi = np.where(np.isnan(X), np.nanmedian(X[tr], axis=0), X); sc = StandardScaler().fit(Xi[tr])
lr = LogisticRegression(C=0.1, max_iter=3000).fit(sc.transform(Xi[tr]), y[tr])
for name, p in (('boosting', gb.predict_proba(X[te])[:, 1]), ('logistic', lr.predict_proba(sc.transform(Xi[te]))[:, 1])):
    order = np.argsort(-p); yt = y[te][order]
    parts = []
    for perday in (0.25, 0.5, 1.0, 1.54, 2.0):
        k = max(1, int(perday * test_days)); parts.append('top %.2f/d (%d): %.1f%%' % (perday, k, 100 * yt[:k].mean()))
    print('%-9s test AUC %.3f | %s' % (name, roc_auc_score(y[te], p), ' | '.join(parts)))
