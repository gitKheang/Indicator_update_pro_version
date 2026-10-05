"""ML ceiling inside the V7.4 trend stack: train on 2024-01..2025-06 setups, test after."""
import pickle, math
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
from v75_lab import T, SPLIT
rows = pickle.load(open('data/v75_inter_rows.pkl', 'rb'))
keys = sorted({k for r in rows for k in r['f']} | {k for r in rows for k in r['g']})
def vec(r):
    return [float('nan') if (r['f'].get(k, r['g'].get(k)) is None) else float(r['f'].get(k, r['g'].get(k))) for k in keys]
X = np.array([vec(r) for r in rows]); y = np.array([1 if r['win'] else 0 for r in rows])
tr = np.array([T[r['i']] < SPLIT for r in rows]); te = ~tr
print('features', len(keys), 'train', tr.sum(), 'test', te.sum(), 'base WR test %.1f%%' % (100 * y[te].mean()))
gb = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=20, random_state=1).fit(X[tr], y[tr])
p_gb = gb.predict_proba(X[te])[:, 1]
Xi = np.where(np.isnan(X), np.nanmedian(X[tr], axis=0), X); sc = StandardScaler().fit(Xi[tr])
lr = LogisticRegression(C=0.1, max_iter=2000).fit(sc.transform(Xi[tr]), y[tr])
p_lr = lr.predict_proba(sc.transform(Xi[te]))[:, 1]
for name, p in (('boosting', p_gb), ('logistic', p_lr)):
    auc = roc_auc_score(y[te], p)
    order = np.argsort(-p); yt = y[te][order]
    q = [yt[:max(1, int(len(yt) * f))].mean() for f in (0.1, 0.2, 0.3, 0.5)]
    print('%-9s test AUC %.3f | top10%% WR %.1f%% top20%% %.1f%% top30%% %.1f%% top50%% %.1f%%' % (name, auc, *(100 * v for v in q)))
print('train AUC boosting %.3f (memorisation check)' % roc_auc_score(y[tr], gb.predict_proba(X[tr])[:, 1]))
coef = sorted(zip(keys, lr.coef_[0]), key=lambda x: -abs(x[1]))[:10]
print('logistic top weights:', ', '.join('%s %+.2f' % (k, v) for k, v in coef))
