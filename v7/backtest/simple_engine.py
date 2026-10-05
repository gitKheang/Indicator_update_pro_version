"""V7.2 research engine: trend-aligned 5m structure break, structural stop,
structural targets, no break-even. Uses the same Phase-5 context as the port."""
import datetime
import ta
from engine import Engine, stats
from r2_common import ctx, SPLIT, TWO_Y, DAYS_ALL, DAYS_2Y, report
H, L, C, O, T, A = ctx['H'], ctx['L'], ctx['C'], ctx['O'], ctx['T'], ctx['atr']
N = ctx['N']; EV = ctx['ev']; MB, B1 = ctx['macroBias'], ctx['bias1H']
_itop, _ibtm = ta.swings(H, L, 5)
ATR14 = ta.atr(H, L, C, 14)
# bar index of the internal swing pivot that is current at each bar
PTOP = [None] * N; PBTM = [None] * N
pt = pb = None
for i in range(N):
    if _itop[i]: pt = i - 5
    if _ibtm[i]: pb = i - 5
    PTOP[i] = pt; PBTM[i] = pb
_pool_eng = Engine(ctx)

DEF = dict(trigger=('ibreak',), htf='both', body=0.0, buf=0.3, buf_src='atr89', max_sl=15.0, min_sl=2.0,
           min_tp1_r=1.5, tp_mode='struct', tp_front=0.0, fixed_tp1=1.6, fixed_tp2=2.5, cost=0.3,
           sl_ref='protected', max_hold=576, part=0.5)

class Trade(dict):
    pass

ITOPY = [None] * N; IBTMY = [None] * N
_ty = _by = None
for _i in range(N):
    if _itop[_i]: _ty = _itop[_i]
    if _ibtm[_i]: _by = _ibtm[_i]
    ITOPY[_i] = _ty; IBTMY[_i] = _by

def _retest(i, s, c, rej):
    a = A[i]
    if c['htf'] == 'both' and not (MB[i] == s and B1[i] == s): return None
    if c['htf'] == '4h' and MB[i] != s: return None
    pbar = PTOP[i] if s == 1 else PBTM[i]
    if pbar is not None and i - pbar <= 200:
        ext = min(L[pbar:i + 1]) if s == 1 else max(H[pbar:i + 1])
    else:
        ext = min(L[i - 12:i + 1]) if s == 1 else max(H[i - 12:i + 1])
    lvl = ITOPY[i] if s == 1 else IBTMY[i]
    if lvl is None: return None
    stop = ext - c['buf'] * a if s == 1 else ext + c['buf'] * a
    entry = lvl
    risk = (entry - stop) * s
    if risk <= 0 or (C[i] - entry) * s <= 0: return None
    if risk > c['max_sl']: rej['sl_wide'] = rej.get('sl_wide', 0) + 1; return None
    if risk < c['min_sl']: return None
    tp1 = entry + s * c['fixed_tp1'] * risk
    pool = _pool_eng.target_pool(i, s)
    if c.get('clean_room'):
        obst = [p for p, k in pool if k in c['clean_room'] and ((entry < p < tp1) if s == 1 else (tp1 < p < entry))]
        if obst: rej['blocked'] = rej.get('blocked', 0) + 1; return None
    zs = sorted([p for p, k in pool if k in (c.get('clean_room') or ()) and (p - tp1) * s > 0], key=lambda p: abs(p - entry))
    cap2 = entry + s * c['fixed_tp2'] * risk
    tp2 = cap2 if not zs or (zs[0] - cap2) * s >= 0 else zs[0] - s * c['tp_front'] * a
    if (tp2 - tp1) * s <= 0.25 * risk: return None
    # wait for the limit fill
    for j in range(i + 1, min(N, i + 1 + c.get('fill_bars', 12))):
        if (H[j] >= tp1) if s == 1 else (L[j] <= tp1):
            rej['missed'] = rej.get('missed', 0) + 1; return None
        if L[j] <= entry <= H[j]:
            t = Trade(side=s, entry=entry, stop=stop, tp1=tp1, tp2=tp2, tp1R=(tp1 - entry) * s / risk, tp2R=(tp2 - entry) * s / risk,
                      readyTime=T[i], fillBar=j, tp1Hit=False, risk=risk)
            if (L[j] <= stop) if s == 1 else (H[j] >= stop):
                t['outcome'] = 'STOP'; t['exitBar'] = j; _immediate.append(t); return None
            return t
    rej['expired'] = rej.get('expired', 0) + 1
    return None
_immediate = []

def run(cfg=None, label=None, show=True, start=600, end=None):
    c = dict(DEF); c.update(cfg or {})
    trades = []; rej = {}
    ex = None
    end = end or N - 1
    for i in range(start, end):
        a = A[i]
        if a is None: continue
        h, l = H[i], L[i]
        # ---- manage open trade (stop-first, no break-even)
        if ex is not None and i > ex['fillBar']:
            s = ex['side']
            st = (l <= ex['stop']) if s == 1 else (h >= ex['stop'])
            t1 = (h >= ex['tp1']) if s == 1 else (l <= ex['tp1'])
            t2 = (h >= ex['tp2']) if s == 1 else (l <= ex['tp2'])
            if st or t2 or i - ex['fillBar'] >= c['max_hold']:
                if st:
                    ex['outcome'] = 'STOP_AFTER_TP1' if ex['tp1Hit'] else 'STOP'
                elif t2:
                    ex['outcome'] = 'TP2'; ex['tp1Hit'] = True
                else:
                    ex['outcome'] = 'TIME'; ex['timeClose'] = C[i]
                ex['exitBar'] = i; trades.append(ex); ex = None
            elif t1 and not ex['tp1Hit']:
                ex['tp1Hit'] = True
        if ex is not None:
            if (EV['bull_ibreak'][i] and MB[i] == 1 and B1[i] == 1) or (EV['bear_ibreak'][i] and MB[i] == -1 and B1[i] == -1):
                rej['busy'] = rej.get('busy', 0) + 1
            continue
        # ---- signal
        side = 0
        for s, kb, kc in ((1, 'bull_ibreak', 'bull_ichoch'), (-1, 'bear_ibreak', 'bear_ichoch')):
            fired = ('ibreak' in c['trigger'] and EV[kb][i]) or ('ichoch' in c['trigger'] and EV[kc][i])
            if fired: side = s
        if side == 0: continue
        s = side
        if c.get('entry_mode') == 'retest':
            res_ = _retest(i, s, c, rej)
            if res_ is not None:
                ex = res_
            continue
        if c['htf'] == 'both' and not (MB[i] == s and B1[i] == s): continue
        if c['htf'] == '4h' and MB[i] != s: continue
        if c['htf'] == '1h' and B1[i] != s: continue
        if c['body'] and (C[i] - O[i]) * s < c['body'] * a: continue
        if 'filter' in c and not c['filter'](i, s): continue
        # ---- structural stop: beyond the protected swing extreme of the broken leg
        pbar = PTOP[i] if s == 1 else PBTM[i]
        if c['sl_ref'] == 'protected' and pbar is not None and i - pbar <= 200:
            ext = min(L[pbar:i + 1]) if s == 1 else max(H[pbar:i + 1])
        else:
            ext = min(L[i - 12:i + 1]) if s == 1 else max(H[i - 12:i + 1])
        bsrc = a if c['buf_src'] == 'atr89' else ATR14[i]
        stop = ext - c['buf'] * bsrc if s == 1 else ext + c['buf'] * bsrc
        entry = C[i]
        risk = (entry - stop) * s
        if risk <= 0: rej['bad'] = rej.get('bad', 0) + 1; continue
        if risk > c['max_sl']: rej['sl_wide'] = rej.get('sl_wide', 0) + 1; continue
        if risk > c.get('max_sl_atr', 99) * a: rej['sl_wide_atr'] = rej.get('sl_wide_atr', 0) + 1; continue
        if risk < c['min_sl']: rej['sl_tight'] = rej.get('sl_tight', 0) + 1; continue
        # ---- targets
        if c['tp_mode'] == 'struct':
            pool = _pool_eng.target_pool(i, s)
            lv = sorted(set(round(p, 3) for p, k in pool if ((p > entry and p > h) if s == 1 else (p < entry and p < l))), key=lambda p: abs(p - entry))
            lv = [p - s * c['tp_front'] * a for p in lv]
            beyond = [p for p in lv if (p - entry) * s > c['min_tp1_r'] * risk]
            if len(beyond) < 2: rej['no_room'] = rej.get('no_room', 0) + 1; continue
            tp1, tp2 = beyond[0], beyond[1]
            if 'max_tp1_r' in c and (tp1 - entry) * s > c['max_tp1_r'] * risk: rej['tp1_far'] = rej.get('tp1_far', 0) + 1; continue
        elif c['tp_mode'] == 'hybrid':
            # TP1 just beyond the 1.5R floor; TP2 = first real structure/liquidity level beyond TP1
            tp1 = entry + s * c['fixed_tp1'] * risk
            pool = _pool_eng.target_pool(i, s)
            lv = sorted(set(round(p, 3) for p, k in pool if ((p > entry and p > h) if s == 1 else (p < entry and p < l))), key=lambda p: abs(p - entry))
            if c.get('clean_room'):
                kinds = c['clean_room']
                obst = [p for p, k in pool if k in kinds and ((entry < p < tp1) if s == 1 else (tp1 < p < entry))]
                if obst: rej['blocked'] = rej.get('blocked', 0) + 1; continue
            if c.get('tp2_before_zone'):
                zs = sorted([p for p, k in pool if k in c['clean_room'] and (p - tp1) * s > 0], key=lambda p: abs(p - entry))
                cap2 = entry + s * c['fixed_tp2'] * risk
                tp2 = cap2 if not zs or (zs[0] - cap2) * s >= 0 else zs[0] - s * c['tp_front'] * a
                if (tp2 - tp1) * s <= 0.25 * risk:
                    rej['no_tp2'] = rej.get('no_tp2', 0) + 1; continue
                beyond = None
            else:
                beyond = [p - s * c['tp_front'] * a for p in lv if (p - s * c['tp_front'] * a - tp1) * s > 0.25 * risk]
            if c.get('tp2_before_zone'):
                pass
            elif beyond and (beyond[0] - entry) * s <= c.get('tp2_cap', 99) * risk:
                tp2 = beyond[0]
            elif c.get('tp2_fallback'):
                tp2 = entry + s * c['fixed_tp2'] * risk
            else:
                rej['no_tp2'] = rej.get('no_tp2', 0) + 1; continue
        else:
            tp1 = entry + s * c['fixed_tp1'] * risk; tp2 = entry + s * c['fixed_tp2'] * risk
        ex = Trade(side=s, entry=entry, stop=stop, tp1=tp1, tp2=tp2, tp1R=(tp1 - entry) * s / risk, tp2R=(tp2 - entry) * s / risk,
                   readyTime=T[i], fillBar=i, tp1Hit=False, risk=risk)
    trades = sorted(trades + [t for t in _immediate], key=lambda t: t['readyTime']); _immediate.clear()
    res = dict(trades=trades, rej=rej, cfg=c)
    if show:
        summarize(res, label or str(cfg))
    return res

def r_of(t, c):
    risk = t['risk']; cost = c['cost'] / risk; p = c['part']
    if t['outcome'] == 'STOP': return -1 - cost
    if t['outcome'] == 'STOP_AFTER_TP1': return p * t['tp1R'] - (1 - p) - cost
    if t['outcome'] == 'TP2': return p * t['tp1R'] + (1 - p) * t['tp2R'] - cost
    pnl = (t['timeClose'] - t['entry']) * t['side'] / risk
    return (p * t['tp1R'] + (1 - p) * pnl if t['tp1Hit'] else pnl) - cost

def metrics(tr, c, days=None):
    if not tr: return None
    rs = [r_of(t, c) for t in tr]
    wins = sum(1 for t in tr if t['tp1Hit'])
    gp = sum(r for r in rs if r > 0); gl = -sum(r for r in rs if r < 0)
    eq = pk = dd = 0; mcl = cur = 0
    for t, r in zip(tr, rs):
        eq += r; pk = max(pk, eq); dd = max(dd, pk - eq)
        cur = cur + 1 if not t['tp1Hit'] else 0; mcl = max(mcl, cur)
    return dict(n=len(tr), perday=len(tr) / days if days else None, wins=wins, losses=len(tr) - wins, wr=wins / len(tr),
                pf=gp / gl if gl else float('inf'), exp=sum(rs) / len(rs), net=sum(rs), dd=dd, mcl=mcl,
                tp1R=sum(t['tp1R'] for t in tr) / len(tr), tp2R=sum(t['tp2R'] for t in tr) / len(tr),
                risk=sorted(t['risk'] for t in tr)[len(tr) // 2])

def fmt(m):
    if not m: return 'n=0'
    return 'n=%4d%s W/L %d/%d WR %4.1f%% PF %.2f exp %+.3f net %+6.1fR DD %4.1f MCL %2d | TP1 %.2fR TP2 %.2fR SL$ %.1f' % (
        m['n'], (' %.2f/d' % m['perday']) if m['perday'] else '', m['wins'], m['losses'], 100 * m['wr'], m['pf'], m['exp'], m['net'], m['dd'], m['mcl'], m['tp1R'], m['tp2R'], m['risk'])

def summarize(res, label):
    tr, c = res['trades'], res['cfg']
    print('== %s' % label)
    print('   ALL ', fmt(metrics(tr, c, DAYS_ALL)))
    print('   2Y  ', fmt(metrics([t for t in tr if t['readyTime'] >= TWO_Y], c, DAYS_2Y)))
    print('   IS  ', fmt(metrics([t for t in tr if t['readyTime'] < SPLIT], c)))
    print('   OOS ', fmt(metrics([t for t in tr if t['readyTime'] >= SPLIT], c)))
