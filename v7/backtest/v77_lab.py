"""V7.7 lab: break-even (BE) before TP1, latest 6 months.

Rules kept: structural SL <= $15, TP1 = 1.51R (> 1.5R), TP2 2.5R or before obstacle
(> TP1), entry at the trigger close, $0.30 cost, one position at a time (or ALL).
New: the stop moves to the BE level (entry + offset) once a BE trigger fires; it acts
from the NEXT bar (the Trade Manager works on confirmed 5m bars). Stop first when one
candle touches the stop and a target.

Outcomes:  WIN  = TP1 reached (runner then exits at TP2 or at the current stop)
           LOSS = original stop hit before BE was armed
           BE   = BE stop hit after it was armed, before TP1
Train = 2026-04-05 .. 2026-09-04 (5 months), test = 2026-09-05 .. 2026-10-04 (last month).
"""
import datetime
import ta
from v76_lab import setups, I0, T, H, L, C, N, A, DAYS6
from v75_lab import ST_LINE, ST_SIDE
from simple_engine import _itop, _ibtm
UTC = datetime.timezone.utc
TEST0 = int(datetime.datetime(2026, 9, 5, tzinfo=UTC).timestamp() * 1000)
# Chandelier Exit (Chuck LeBeau): long stop = highest high(22) - 3 x ATR(22); short = lowest low(22) + 3 x ATR(22)
_A22 = ta.atr(H, L, C, 22); _HH = ta.sliding_max(H, 22); _LL = ta.sliding_min(L, 22)
CE_LONG = [None if _A22[i] is None or _HH[i] is None else _HH[i] - 3 * _A22[i] for i in range(N)]
CE_SHORT = [None if _A22[i] is None or _LL[i] is None else _LL[i] + 3 * _A22[i] for i in range(N)]


def simulate_be(st, be='none', x=0.5, offset=0.0, cost=0.3):
    """Re-simulate one setup with a BE rule. offset is in R (e.g. 0.1 = BE+0.1R)."""
    i, s, e, R = st['i'], st['s'], st['entry'], st['risk']
    stop0, tp1, tp2 = st['stop'], st['tp1'], st['tp2']
    be_level = e + s * offset * R
    armed = False; hit1 = False; res = None; j = i + 1
    while j < N:
        cur_stop = be_level if armed else stop0
        stop_hit = (L[j] <= cur_stop) if s == 1 else (H[j] >= cur_stop)
        if not hit1:
            if stop_hit: res = 'BE' if armed else 'LOSS'; break
            if (H[j] >= tp1) if s == 1 else (L[j] <= tp1):
                hit1 = True
                if (H[j] >= tp2) if s == 1 else (L[j] <= tp2): res = 'TP2'; break
        else:
            if stop_hit: res = 'TP1_STOP'; break
            if (H[j] >= tp2) if s == 1 else (L[j] <= tp2): res = 'TP2'; break
        # arm BE at this bar's close (effective from the next bar)
        if be != 'none' and not armed:
            if be == 'R':
                fav = (H[j] - e) * s if s == 1 else (e - L[j])
                armed = fav >= x * R
            elif be == 'st':
                armed = ST_SIDE[j] == s and ST_LINE[j] is not None and (ST_LINE[j] - e) * s > 0
            elif be == 'ce':
                ce = CE_LONG[j] if s == 1 else CE_SHORT[j]
                armed = ce is not None and (ce - e) * s > 0
            elif be == 'swing':
                piv = _ibtm[j] if s == 1 else _itop[j]        # internal swing confirmed on this bar
                armed = bool(piv) and (j - 5) > i and (piv - e) * s > 0   # higher low / lower high formed after entry
            elif be == 'after_tp1':
                armed = hit1
        if be == 'after_tp1' and hit1: armed = True
        j += 1
    r1 = (tp1 - e) * s / R; r2 = (tp2 - e) * s / R; c = cost / R
    runner_stop_R = offset if armed else -1.0
    out = dict(st)
    out['res'] = res or 'OPEN'; out['exit'] = j; out['win'] = hit1
    out['R'] = (-1 - c) if res == 'LOSS' else (offset - c) if res == 'BE' else \
               (0.5 * r1 + 0.5 * runner_stop_R - c) if res == 'TP1_STOP' else (0.5 * r1 + 0.5 * r2 - c) if res == 'TP2' else 0.0
    return out


def sequential(rows):
    out = []; free = -1
    for r in sorted(rows, key=lambda r: (r['i'], -r['s'])):
        if r['i'] >= free: out.append(r); free = r['exit']
    return out


def summary(rows):
    if not rows: return dict(n=0)
    W = sum(1 for r in rows if r['win']); Lo = sum(1 for r in rows if r['res'] == 'LOSS'); B = sum(1 for r in rows if r['res'] == 'BE')
    rs = [r['R'] for r in rows]; gp = sum(x for x in rs if x > 0); gl = -sum(x for x in rs if x < 0)
    eq = pk = dd = 0.0
    for x in rs: eq += x; pk = max(pk, eq); dd = max(dd, pk - eq)
    return dict(n=len(rows), W=W, L=Lo, B=B, wr_dec=W / (W + Lo) if W + Lo else float('nan'), wr_all=W / len(rows),
                nonloss=(W + B) / len(rows), net=sum(rs), pf=gp / gl if gl else float('inf'), dd=dd)


def fmt(s):
    if not s.get('n'): return 'n=0'
    return 'n=%3d W/L/BE %3d/%3d/%3d | WR(W/(W+L)) %5.1f%% | WR(all) %5.1f%% | no-loss %5.1f%% | net %+6.1fR PF %5.2f DD %4.1f' % (
        s['n'], s['W'], s['L'], s['B'], 100 * s['wr_dec'], 100 * s['wr_all'], 100 * s['nonloss'], s['net'], s['pf'], s['dd'])


def evaluate(cfg, be='none', x=0.5, offset=0.0, seq=True):
    base, _ = setups(cfg)
    rows = [simulate_be(r, be, x, offset) for r in base]
    sel = sequential(rows) if seq else rows
    tr = [r for r in sel if T[r['i']] < TEST0]; te = [r for r in sel if T[r['i']] >= TEST0]
    return summary(sel), summary(tr), summary(te)
