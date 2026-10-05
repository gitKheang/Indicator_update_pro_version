"""V7.5 research lab.

Every V7.4 setup (or a looser variant) is simulated on its own, with no
one-position limit, so feature studies get the largest honest sample. Each setup
carries market-context features measured with data up to the trigger close only.
Final candidates are always re-checked with simple_engine.run (one position).
"""
import datetime, bisect, math, pickle, os
from zoneinfo import ZoneInfo
import ta
from simple_engine import H, L, C, O, T, A, N, EV, MB, B1, PTOP, PBTM, ITOPY, IBTMY, _pool_eng, _itop, _ibtm
from r2_common import SPLIT

NY = ZoneInfo('America/New_York')
UTC = datetime.timezone.utc
A14 = ta.atr(H, L, C, 14)
X = _pool_eng.x
CLEAN = ('PIVOT_RESISTANCE', 'PIVOT_SUPPORT', 'EQH', 'EQL', '4H_SWING_HIGH', '4H_SWING_LOW')


# ----------------------------------------------------------------- generic helpers
def ema(x, n):
    out = [None] * len(x); e = None; a = 2 / (n + 1)
    for i, v in enumerate(x):
        e = v if e is None else e + a * (v - e); out[i] = e
    return out


def supertrend(h, l, c, period=10, mult=3.0):
    """Exact port of Pine ta.supertrend. Returns (line, side) with side +1 up / -1 down."""
    n = len(c); atr = ta.atr(h, l, c, period)
    line = [None] * n; side = [0] * n
    lb_p = ub_p = st_p = None
    for i in range(n):
        if atr[i] is None:
            continue
        src = (h[i] + l[i]) / 2
        lb = src - mult * atr[i]; ub = src + mult * atr[i]
        plb = lb_p if lb_p is not None else 0.0; pub = ub_p if ub_p is not None else 0.0
        lb = lb if (lb > plb or c[i - 1] < plb) else plb
        ub = ub if (ub < pub or c[i - 1] > pub) else pub
        if atr[i - 1] is None or st_p is None:
            d = 1
        elif st_p == pub:
            d = -1 if c[i] > ub else 1
        else:
            d = 1 if c[i] < lb else -1
        st = lb if d == -1 else ub
        lb_p, ub_p, st_p = lb, ub, st
        line[i] = st; side[i] = 1 if d == -1 else -1
    return line, side


def chop(h, l, c, n=14):
    tr1 = ta.tr(h, l, c); out = [None] * len(c)
    hh = ta.sliding_max(h, n); ll = ta.sliding_min(l, n)
    s = 0.0
    for i in range(len(c)):
        s += tr1[i]
        if i >= n: s -= tr1[i - n]
        if i >= n - 1 and hh[i] is not None and hh[i] > ll[i]:
            out[i] = 100 * math.log10(s / (hh[i] - ll[i])) / math.log10(n)
    return out


def eff_ratio(c, n):
    out = [None] * len(c)
    for i in range(n, len(c)):
        path = sum(abs(c[k] - c[k - 1]) for k in range(i - n + 1, i + 1))
        out[i] = abs(c[i] - c[i - n]) / path if path else None
    return out


# ----------------------------------------------------------------- time keys
NYH = [0] * N; NYD = [0] * N; DOW = [0] * N
for i in range(N):
    d = datetime.datetime.fromtimestamp(T[i] / 1000, NY)
    NYH[i] = d.hour + d.minute / 60
    td = d + datetime.timedelta(hours=7)          # trading day starts 17:00 New York
    NYD[i] = td.date().toordinal(); DOW[i] = td.weekday()


def htf(key):
    """Aggregate 5m bars by key. Returns (h, l, c, o, done) where done[i] is the index
    of the last HTF bar completed at bar i's close (None before the first)."""
    h, l, c, o = [], [], [], []; done = [None] * N; cur = None
    for i in range(N):
        if key[i] != cur:
            cur = key[i]; h.append(H[i]); l.append(L[i]); o.append(O[i]); c.append(C[i])
        else:
            h[-1] = max(h[-1], H[i]); l[-1] = min(l[-1], L[i]); c[-1] = C[i]
        last = i == N - 1 or key[i + 1] != key[i]
        j = len(c) - 1
        done[i] = j if last else (j - 1 if j > 0 else None)
    return h, l, c, o, done


K15 = [t // 900000 for t in T]
K1H = [t // 3600000 for t in T]
K4H = [NYD[i] * 6 + int(((NYH[i] - 17) % 24) // 4) for i in range(N)]
HTF = {}
for name, key in (('15m', K15), ('1h', K1H), ('4h', K4H)):
    h, l, c, o, done = htf(key)
    line, side = supertrend(h, l, c, 10, 3.0)
    HTF[name] = dict(h=h, l=l, c=c, o=o, done=done, st=side, chop=chop(h, l, c, 14), ema50=ema(c, 50))

# 5m indicator arrays
ST_LINE, ST_SIDE = supertrend(H, L, C, 10, 3.0)
E20 = ema(C, 20); E50 = ema(C, 50)
CHOP5 = chop(H, L, C, 14); CHOP48 = chop(H, L, C, 48)
ER48 = eff_ratio(C, 48)

# day statistics (running high/low, open, ADR of the last 10 completed days)
DHI = [0.0] * N; DLO = [0.0] * N; DOPEN = [0.0] * N; ADR10 = [None] * N
_ranges = []; _cur = None; _hi = _lo = None; _open = None
for i in range(N):
    if NYD[i] != _cur:
        if _cur is not None: _ranges.append(_hi - _lo)
        _cur = NYD[i]; _hi = H[i]; _lo = L[i]; _open = O[i]
    _hi = max(_hi, H[i]); _lo = min(_lo, L[i])
    DHI[i] = _hi; DLO[i] = _lo; DOPEN[i] = _open
    ADR10[i] = sum(_ranges[-10:]) / 10 if len(_ranges) >= 10 else None

# internal pivots (pivot bar = confirmation bar - 5)
TOPS = [(i - 5, _itop[i]) for i in range(N) if _itop[i]]
BTMS = [(i - 5, _ibtm[i]) for i in range(N) if _ibtm[i]]
TOP_BARS = [b for b, _ in TOPS]; BTM_BARS = [b for b, _ in BTMS]


def prior_pivot(lst, bars, before):
    k = bisect.bisect_left(bars, before) - 1
    return lst[k] if k >= 0 else None


# ----------------------------------------------------------------- alternative internal structure
def micro_context(n):
    """LuxAlgo internal structure with internal swing length n (the Brain uses 5)."""
    top, btm = ta.swings(H, L, 50); itop, ibtm = ta.swings(H, L, n)
    top_y = btm_y = itop_y = ibtm_y = 0.0; itc = ibc = True; itrend = 0
    ev = {k: [False] * N for k in ('bull_ichoch', 'bear_ichoch', 'bull_ibreak', 'bear_ibreak')}
    ptop = [None] * N; pbtm = [None] * N; ity = [None] * N; iby = [None] * N; pt = pb = None
    for i in range(N):
        p_itop_y, p_ibtm_y = itop_y, ibtm_y
        if top[i]: top_y = top[i]
        if btm[i]: btm_y = btm[i]
        if itop[i]: itc = True; itop_y = itop[i]; pt = i - n
        if ibtm[i]: ibc = True; ibtm_y = ibtm[i]; pb = i - n
        c1 = C[i - 1] if i > 0 else None
        if c1 is not None and C[i] > itop_y and c1 <= p_itop_y and itc and top_y != itop_y:
            if itrend < 0: ev['bull_ichoch'][i] = True
            ev['bull_ibreak'][i] = True; itc = False; itrend = 1
        if c1 is not None and C[i] < ibtm_y and c1 >= p_ibtm_y and ibc and btm_y != ibtm_y:
            if itrend > 0: ev['bear_ichoch'][i] = True
            ev['bear_ibreak'][i] = True; ibc = False; itrend = -1
        ptop[i] = pt; pbtm[i] = pb; ity[i] = itop_y or None; iby[i] = ibtm_y or None
    return ev, ptop, pbtm, ity, iby


# ----------------------------------------------------------------- setups
def setups(trigger_filter=None, htf_mode='both', use_st=True, clean=CLEAN, buf=0.3, max_sl=15.0, min_sl=2.0,
           tp1r=1.51, tp2r=2.5, front=0.1, cost=0.3, start=600, end=None, sctx=None):
    """All V7.4-style setups, each simulated alone. trigger_filter(i, s) -> bool adds a rule.
    sctx = (EV, PTOP, PBTM, ITOPY, IBTMY) from micro_context(n) to use another internal swing length."""
    ev, ptop, pbtm, itopy, ibtmy = sctx if sctx else (EV, PTOP, PBTM, ITOPY, IBTMY)
    out = []
    end = end or N - 1
    for i in range(start, end):
        a = A[i]
        if a is None: continue
        for s, kb in ((1, 'bull_ibreak'), (-1, 'bear_ibreak')):
            if not ev[kb][i]: continue
            if htf_mode == 'both' and not (MB[i] == s and B1[i] == s): continue
            if htf_mode == '1h' and B1[i] != s: continue
            if htf_mode == '4h' and MB[i] != s: continue
            if use_st and ST_SIDE[i] != s: continue
            if trigger_filter and not trigger_filter(i, s): continue
            pbar = ptop[i] if s == 1 else pbtm[i]
            if pbar is not None and i - pbar <= 200:
                ext = min(L[pbar:i + 1]) if s == 1 else max(H[pbar:i + 1])
            else:
                ext = min(L[i - 12:i + 1]) if s == 1 else max(H[i - 12:i + 1])
            stop = ext - s * buf * a
            entry = C[i]; risk = (entry - stop) * s
            if risk <= 0 or risk > max_sl or risk < min_sl: continue
            tp1 = entry + s * tp1r * risk
            pool = _pool_eng.target_pool(i, s)
            obst = sorted([p for p, k in pool if k in clean and (p - entry) * s > 0], key=lambda p: abs(p - entry))
            if obst and (obst[0] - tp1) * s < 0: continue
            beyond = [p for p in obst if (p - tp1) * s > 0]
            cap2 = entry + s * tp2r * risk
            tp2 = cap2 if not beyond or (beyond[0] - cap2) * s >= 0 else beyond[0] - s * front * a
            if (tp2 - tp1) * s <= 0.25 * risk: continue
            out.append(dict(i=i, s=s, entry=entry, stop=stop, tp1=tp1, tp2=tp2, risk=risk, pbar=pbar, ext=ext, brk=(itopy[i] if s == 1 else ibtmy[i]),
                            room=(abs(obst[0] - entry) / risk if obst else 99.0)))
    for st in out:
        simulate(st, cost)
    return out


def simulate(st, cost=0.3):
    i, s = st['i'], st['s']; stop, tp1, tp2 = st['stop'], st['tp1'], st['tp2']
    hit1 = False; res = None; j = i + 1; mae = 0.0
    while j < N:
        lo_hit = (L[j] <= stop) if s == 1 else (H[j] >= stop)
        if not hit1:
            if lo_hit: res = 'STOP'; break
            if (H[j] >= tp1) if s == 1 else (L[j] <= tp1):
                hit1 = True; st['bars1'] = j - i
                if (H[j] >= tp2) if s == 1 else (L[j] <= tp2): res = 'TP2'; break
            else:
                adv = ((st['entry'] - L[j]) if s == 1 else (H[j] - st['entry'])) / st['risk']
                mae = max(mae, adv)
        else:
            if lo_hit: res = 'STOP_AFTER_TP1'; break
            if (H[j] >= tp2) if s == 1 else (L[j] <= tp2): res = 'TP2'; break
        j += 1
    st['outcome'] = res or 'OPEN'; st['win'] = hit1; st['exit'] = j; st['mae'] = mae
    r1 = (tp1 - st['entry']) * s / st['risk']; r2 = (tp2 - st['entry']) * s / st['risk']
    c = cost / st['risk']
    st['R'] = (-1 - c) if res == 'STOP' else (0.5 * r1 - 0.5 - c) if res == 'STOP_AFTER_TP1' else (0.5 * r1 + 0.5 * r2 - c) if res == 'TP2' else 0.0
    return st


# ----------------------------------------------------------------- features
def features(st):
    i, s = st['i'], st['s']; e = st['entry']; R = st['risk']; a89 = A[i]; a14 = A14[i]
    f = {}
    f['sl_atr89'] = R / a89
    f['sl_atr14'] = R / a14 if a14 else None
    f['risk_usd'] = R
    f['room_R'] = min(st['room'], 10.0)
    opp = _pool_eng.target_pool(i, -s)
    f['support_behind'] = sum(1 for p, k in opp if (p - st['stop']) * s > 0 and (e - p) * s > 0)
    f['ext_ema20_atr'] = (C[i] - E20[i]) * s / a14 if a14 else None
    f['ext_st_atr'] = (C[i] - ST_LINE[i]) * s / a14 if a14 and ST_LINE[i] else None
    f['chop5_14'] = CHOP5[i]; f['chop5_48'] = CHOP48[i]; f['er48'] = ER48[i]
    for name in ('15m', '1h', '4h'):
        d = HTF[name]['done'][i]
        f['st_' + name] = (1 if HTF[name]['st'][d] == s else 0) if d is not None and HTF[name]['st'][d] else None
        f['chop_' + name] = HTF[name]['chop'][d] if d is not None else None
        em = HTF[name]['ema50'][d] if d is not None else None
        f['above_ema50_' + name] = (1 if (C[i] - em) * s > 0 else 0) if em else None
    adr = ADR10[i]
    if adr:
        f['adr_used'] = (DHI[i] - DLO[i]) / adr
        f['adr_room_R'] = ((DLO[i] + adr - e) if s == 1 else (e - (DHI[i] - adr))) / R
    f['day_dir'] = 1 if (C[i] - DOPEN[i]) * s > 0 else 0
    f['ny_hour'] = NYH[i]; f['dow'] = DOW[i]
    mh, ml = X['macroHigh'][i], X['macroLow'][i]
    if mh and ml and mh > ml:
        loc = (C[i] - ml) / (mh - ml)
        f['loc4h_side'] = loc if s == 1 else 1 - loc        # low = buying in discount / selling in premium
    f['vol_ratio'] = a14 / a89 if a14 else None
    brk = st.get('brk') or (ITOPY[i] if s == 1 else IBTMY[i])
    f['impulse_atr'] = abs(brk - st['ext']) / a89 if brk else None
    f['pb_bars'] = i - st['pbar'] if st['pbar'] is not None else None
    f['choch'] = 1 if EV['bull_ichoch' if s == 1 else 'bear_ichoch'][i] else 0
    # pullback depth relative to the leg that made the broken pivot
    if st['pbar'] is not None:
        if s == 1:
            pv = prior_pivot(BTMS, BTM_BARS, st['pbar'])
            if pv and brk and brk > pv[1]: f['pb_depth'] = (brk - st['ext']) / (brk - pv[1])
        else:
            pv = prior_pivot(TOPS, TOP_BARS, st['pbar'])
            if pv and brk and pv[1] > brk: f['pb_depth'] = (st['ext'] - brk) / (pv[1] - brk)
    pdh, pdl = X['pdh'][i], X['pdl'][i]
    if pdh and pdl:
        f['beyond_pd'] = 1 if ((C[i] > pdh) if s == 1 else (C[i] < pdl)) else 0
    f['side'] = s
    return f


def wr(lst):
    return sum(1 for x in lst if x['win']) / len(lst) if lst else float('nan')


def pf(lst):
    gp = sum(x['R'] for x in lst if x['R'] > 0); gl = -sum(x['R'] for x in lst if x['R'] < 0)
    return gp / gl if gl else float('inf')


def split_report(rows, key, cuts=None, label=None):
    vals = [r for r in rows if r['f'].get(key) is not None]
    if len(vals) < 30: return
    if cuts is None:
        isv = sorted(r['f'][key] for r in vals if T[r['i']] < SPLIT)
        if len(isv) < 15: return
        cuts = [isv[len(isv) // 3], isv[2 * len(isv) // 3]]
        if cuts[0] == cuts[1]: cuts = [cuts[0]]
    bins = [[] for _ in range(len(cuts) + 1)]
    for r in vals:
        b = sum(1 for c in cuts if r['f'][key] >= c); bins[b].append(r)
    parts = []
    for k, b in enumerate(bins):
        bi = [r for r in b if T[r['i']] < SPLIT]; bo = [r for r in b if T[r['i']] >= SPLIT]
        lo = '-inf' if k == 0 else '%.2f' % cuts[k - 1]
        parts.append('[%s..) n=%d WR %4.1f%% (IS %4.1f%% OOS %4.1f%%) PF %.2f' % (lo, len(b), 100 * wr(b), 100 * wr(bi), 100 * wr(bo), pf(b)))
    print('%-16s %s' % (label or key, ' | '.join(parts)))


if __name__ == '__main__':
    rows = setups()
    for r in rows: r['f'] = features(r)
    pickle.dump([{k: v for k, v in r.items()} for r in rows], open('data/v75_setups.pkl', 'wb'))
    isr = [r for r in rows if T[r['i']] < SPLIT]; oos = [r for r in rows if T[r['i']] >= SPLIT]
    print('V7.4 setups (each alone): n=%d WR %.1f%% PF %.2f | IS n=%d %.1f%% | OOS n=%d %.1f%%' % (
        len(rows), 100 * wr(rows), pf(rows), len(isr), 100 * wr(isr), len(oos), 100 * wr(oos)))
    for key in ['sl_atr89', 'sl_atr14', 'risk_usd', 'room_R', 'support_behind', 'ext_ema20_atr', 'ext_st_atr', 'chop5_14',
                'chop5_48', 'er48', 'st_15m', 'st_1h', 'st_4h', 'chop_15m', 'chop_1h', 'chop_4h', 'above_ema50_15m',
                'above_ema50_1h', 'above_ema50_4h', 'adr_used', 'adr_room_R', 'day_dir', 'ny_hour', 'dow', 'loc4h_side',
                'vol_ratio', 'impulse_atr', 'pb_bars', 'choch', 'pb_depth', 'beyond_pd', 'side']:
        cuts = [0.5] if key in ('st_15m', 'st_1h', 'st_4h', 'above_ema50_15m', 'above_ema50_1h', 'above_ema50_4h', 'day_dir', 'choch', 'beyond_pd') else \
               [0] if key == 'side' else None
        split_report(rows, key, cuts)


def sequential(rows):
    """One position at a time, as the Execution script trades: a setup is taken only
    if it fires at or after the exit bar of the previous trade."""
    out = []; free = -1
    for r in sorted(rows, key=lambda r: (r['i'], -r['s'])):
        if r['i'] >= free:
            out.append(r); free = r['exit']
    return out


def stats(rows, days=719):
    if not rows: return dict(n=0)
    rs = [r['R'] for r in rows]
    eq = pk = dd = 0.0; mcl = cur = 0
    for r in rows:
        eq += r['R']; pk = max(pk, eq); dd = max(dd, pk - eq)
        cur = 0 if r['win'] else cur + 1; mcl = max(mcl, cur)
    i = [r for r in rows if T[r['i']] < SPLIT]; o = [r for r in rows if T[r['i']] >= SPLIT]
    return dict(n=len(rows), perday=len(rows) / days, wr=wr(rows), pf=pf(rows), net=sum(rs), exp=sum(rs) / len(rs), dd=dd, mcl=mcl,
                wr_is=wr(i), wr_oos=wr(o), pf_is=pf(i), pf_oos=pf(o), days=len(set(NYD[r['i']] for r in rows)))


def fmt(s):
    if not s.get('n'): return 'n=0'
    return 'n=%4d %.2f/d WR %5.1f%% PF %.2f net %+6.1fR exp %+.2f DD %4.1f MCL %2d | IS %5.1f%%/%.2f OOS %5.1f%%/%.2f | days %d' % (
        s['n'], s['perday'], 100 * s['wr'], s['pf'], s['net'], s['exp'], s['dd'], s['mcl'], 100 * s['wr_is'], s['pf_is'], 100 * s['wr_oos'], s['pf_oos'], s['days'])


# 1H Choppiness as Pine reads it: inside hour H the value of the completed hour H-1
CHOP1H_PINE = [None] * N
_cur = None; _idx = -1
for _i in range(N):
    if K1H[_i] != _cur: _cur = K1H[_i]; _idx += 1
    CHOP1H_PINE[_i] = HTF['1h']['chop'][_idx - 1] if _idx >= 1 else None
