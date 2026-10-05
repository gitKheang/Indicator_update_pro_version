"""ML ceiling test: can ANY combination of the context features pick setups whose
TP1 (>1.5R) hit rate approaches 80% out-of-sample?"""
import pickle, sys, math, datetime
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
SPLIT = int(datetime.datetime(2025, 7, 1, tzinfo=datetime.timezone.utc).timestamp() * 1000)
import sys
for mode in (sys.argv[1:] or ['struct', 'fixed151']):
    rows = pickle.load(open('data/ml_%s.pkl' % mode, 'rb'))
    keys = sorted({k for r in rows for k in r['f']})
    X = np.array([[np.nan if r['f'].get(k) is None else r['f'].get(k, 0.0 if k.startswith('fam_') else np.nan) for k in keys] for r in rows], dtype=float)
    y = np.array([r['y'] for r in rows]); t = np.array([r['t'] for r in rows])
    tr = t < SPLIT; te = ~tr
    print('==== TP1 mode:', mode, '| rows IS %d OOS %d | base WR IS %.3f OOS %.3f' % (tr.sum(), te.sum(), y[tr].mean(), y[te].mean()))
    models = {
        'gboost': HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, min_samples_leaf=60, l2_regularization=1.0, random_state=0),
        'logit': LogisticRegression(max_iter=2000, C=0.3),
    }
    for name, m in models.items():
        Xtr = X[tr]; Xte = X[te]
        if name == 'logit':
            med = np.nanmedian(Xtr, axis=0); Xtr = np.where(np.isnan(Xtr), med, Xtr); Xte = np.where(np.isnan(Xte), med, Xte)
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; Xtr = (Xtr - mu) / sd; Xte = (Xte - mu) / sd
        m.fit(Xtr, y[tr])
        p_tr = m.predict_proba(Xtr)[:, 1]; p = m.predict_proba(Xte)[:, 1]
        auc_tr = roc_auc_score(y[tr], p_tr); auc = roc_auc_score(y[te], p)
        line = '  %-7s AUC IS %.3f OOS %.3f |' % (name, auc_tr, auc)
        order = np.argsort(-p)
        for frac in (0.5, 0.2, 0.1, 0.05, 0.02):
            k = max(1, int(len(p) * frac)); sel = order[:k]
            line += ' top%2d%%: n=%d WR %.1f%%' % (int(frac * 100), k, 100 * y[te][sel].mean())
        print(line)
        # best threshold chosen on IS, applied OOS
        thr = np.quantile(p_tr, 0.9)
        sel = p >= thr
        print('          IS-chosen top-10%% threshold applied OOS: n=%d WR %.1f%%' % (sel.sum(), 100 * (y[te][sel].mean() if sel.sum() else 0)))
