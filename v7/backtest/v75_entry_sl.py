"""Entry and stop alternatives on the V7.4 + fast-pullback setups."""
import pickle
from v75_lab import setups, sequential, stats, fmt, features, simulate, T, N, H, L, C, A, X, _pool_eng, CLEAN
rows = setups()
for r in rows: r['f'] = features(r)
fast = [r for r in rows if r['f']['pb_bars'] < 12]
print('base fast (pb<12)  SEQ', fmt(stats(sequential(fast))))

def rebuild(r, entry, stop, fill_bar):
    """Same TP rules from a new entry/stop; returns a new setup dict or None if the rules reject it."""
    s = r['s']; risk = (entry - stop) * s
    if risk <= 0 or risk > 15 or risk < 2: return None
    i = r['i']; tp1 = entry + s * 1.51 * risk
    pool = _pool_eng.target_pool(i, s)
    obst = sorted([p for p, k in pool if k in CLEAN and (p - entry) * s > 0], key=lambda p: abs(p - entry))
    if obst and (obst[0] - tp1) * s < 0: return None
    beyond = [p for p in obst if (p - tp1) * s > 0]; cap2 = entry + s * 2.5 * risk
    tp2 = cap2 if not beyond or (beyond[0] - cap2) * s >= 0 else beyond[0] - s * 0.1 * A[i]
    if (tp2 - tp1) * s <= 0.25 * risk: return None
    n = dict(r); n.update(entry=entry, stop=stop, tp1=tp1, tp2=tp2, risk=risk)
    n['i'] = fill_bar     # simulate from the fill bar (stop-first on the fill bar itself is handled below)
    simulate(n); n['i_sig'] = r['i']
    return n

# --- B: retest limit at the broken level (+ fraction of the way back to the close), valid 12 bars
for frac in (0.0, 0.25, 0.5):
    out = []; missed = 0
    for r in fast:
        s, i = r['s'], r['i']; lim = r['brk'] + frac * (r['entry'] - r['brk'])
        risk = (lim - r['stop']) * s; tp1 = lim + s * 1.51 * risk
        filled = None
        for j in range(i + 1, min(N, i + 13)):
            if (H[j] >= tp1) if s == 1 else (L[j] <= tp1): break       # target reached without us
            if L[j] <= lim <= H[j]: filled = j; break
        if filled is None: missed += 1; continue
        if (L[filled] <= r['stop']) if s == 1 else (H[filled] >= r['stop']):
            n = dict(r); n.update(entry=lim, risk=risk, win=False, R=-1 - 0.3 / max(risk, 0.01), outcome='STOP', exit=filled, i=filled); out.append(n); continue
        n = rebuild(r, lim, r['stop'], filled)
        if n: out.append(n)
    print('B retest limit frac %.2f filled %d missed %d  SEQ %s' % (frac, len(out), missed, fmt(stats(sequential(out)))))

# --- D: stop references
def stop_variant(r, mode):
    s, i = r['s'], r['i']; a = A[i]; pk = X['pk'][i]
    sw = pk['swingLow'] if s == 1 else pk['swingHigh']
    base = r['ext']
    if mode == '15m_swing':
        if sw is None or (r['entry'] - sw) * s <= 0: return None
        ref = sw
    elif mode == 'deeper':
        ref = min(base, sw) if (s == 1 and sw) else max(base, sw) if sw else base
    elif mode.startswith('buf'):
        return base - s * float(mode[3:]) * a
    return ref - s * 0.3 * a
for mode in ('15m_swing', 'deeper', 'buf0.15', 'buf0.5', 'buf0.8'):
    out = []
    for r in fast:
        st = stop_variant(r, mode)
        if st is None: continue
        n = rebuild(r, r['entry'], st, r['i'])
        if n: out.append(n)
    print('D stop %-10s n=%d  SEQ %s' % (mode, len(out), fmt(stats(sequential(out)))))

# --- hybrid: deeper (15m swing) stop when it fits within $15, else the normal protected-extreme stop
for pbmax in (12, 999):
    base = [r for r in rows if r['f']['pb_bars'] < pbmax]
    out = []; changed = 0
    for r in base:
        st = stop_variant(r, 'deeper')
        n = rebuild(r, r['entry'], st, r['i']) if st is not None and abs(st - r['stop']) > 1e-9 else None
        if n: out.append(n); changed += 1
        else: out.append(r)
    print('hybrid deeper stop pb<%d (changed %d)  SEQ %s' % (pbmax, changed, fmt(stats(sequential(out)))))
