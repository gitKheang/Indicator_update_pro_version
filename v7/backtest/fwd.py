"""Forward-outcome helpers: simulate a bracket from bar i+1 on 5m OHLC."""
def bracket(ctx, i0, side, entry, stop, tp, maxbars=288, need_fill=False, fill_bars=24):
    """Returns ('TP'|'SL'|'OPEN'|'NOFILL', bars). Stop-first on ambiguous bars.
    If need_fill, entry must be touched within fill_bars (limit order), and the
    fill bar only checks the stop."""
    H, L = ctx['H'], ctx['L']
    N = ctx['N']
    i = i0 + 1
    if need_fill:
        filled = None
        while i < N and i - i0 <= fill_bars:
            if L[i] <= entry <= H[i]:
                filled = i
                break
            if (H[i] >= tp) if side == 1 else (L[i] <= tp):
                return 'NOFILL', i - i0
            i += 1
        if filled is None:
            return 'NOFILL', i - i0
        if (L[filled] <= stop) if side == 1 else (H[filled] >= stop):
            return 'SL', 0
        i = filled + 1
    start = i
    while i < N and i - start < maxbars:
        sl = (L[i] <= stop) if side == 1 else (H[i] >= stop)
        tg = (H[i] >= tp) if side == 1 else (L[i] <= tp)
        if sl:
            return 'SL', i - start
        if tg:
            return 'TP', i - start
        i += 1
    return 'OPEN', i - start

def mfe_mae(ctx, i0, side, ref, bars):
    H, L = ctx['H'], ctx['L']
    hi = max(H[i0 + 1:i0 + 1 + bars]); lo = min(L[i0 + 1:i0 + 1 + bars])
    return ((hi - ref), (ref - lo)) if side == 1 else ((ref - lo), (hi - ref))


def sim_trade(ctx, i0, side, entry, stop, tp1, tp2, limit=True, fill_bars=24, maxbars=576, be=True, cost=0.0):
    """Partial model: 50% at TP1, stop -> entry after TP1 (if be), rest to TP2.
    Returns dict(outcome, r, tp1hit, fillbar) or outcome 'NOFILL'."""
    H, L, C = ctx['H'], ctx['L'], ctx['C']
    N = ctx['N']
    risk = abs(entry - stop)
    i = i0 + 1
    if limit:
        filled = None
        while i < N and i - i0 <= fill_bars:
            if L[i] <= entry <= H[i]:
                filled = i; break
            if (H[i] >= tp1) if side == 1 else (L[i] <= tp1):
                return dict(outcome='NOFILL')
            i += 1
        if filled is None:
            return dict(outcome='NOFILL')
        if (L[filled] <= stop) if side == 1 else (H[filled] >= stop):
            return dict(outcome='STOP', r=-1 - cost / risk, tp1hit=False, fill=filled, exit=filled)
        i = filled + 1
    else:
        filled = i0
    st = stop
    t1 = False
    start = i
    while i < N and i - start < maxbars:
        sl = (L[i] <= st) if side == 1 else (H[i] >= st)
        h1 = (H[i] >= tp1) if side == 1 else (L[i] <= tp1)
        h2 = (H[i] >= tp2) if side == 1 else (L[i] <= tp2)
        if sl:
            if t1:
                r = 0.5 * abs(tp1 - entry) / risk + 0.5 * ((abs(st - entry) / risk) * (1 if (st - entry) * side > 0 else -1))
                return dict(outcome='BE' if be else 'STOP_AFTER_TP1', r=r - cost / risk, tp1hit=True, fill=filled, exit=i)
            return dict(outcome='STOP', r=-1 - cost / risk, tp1hit=False, fill=filled, exit=i)
        if h2:
            return dict(outcome='TP2', r=0.5 * abs(tp1 - entry) / risk + 0.5 * abs(tp2 - entry) / risk - cost / risk, tp1hit=True, fill=filled, exit=i)
        if h1 and not t1:
            t1 = True
            if be:
                st = entry
        i += 1
    # time exit at last close
    c = C[min(i, N - 1)]
    pnl = (c - entry) * side / risk
    r = (0.5 * abs(tp1 - entry) / risk + 0.5 * pnl) if t1 else pnl
    return dict(outcome='TIME', r=r - cost / risk, tp1hit=t1, fill=filled, exit=i)
