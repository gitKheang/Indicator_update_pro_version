"""V7.6 lab — latest 6 months only (2026-04-03 .. data end), on the repaired data.

Earlier history is used only to warm up indicators (as TradingView loads history before
the first visible bar); no trade before 2026-04-03 is counted. Train = Apr-Jul,
test = Aug-Oct (chronological hold-out).

Audit fixes are switches so each can be measured:
  pe_after_pivot : protected extreme searched from the bar AFTER the broken pivot
  swept4h        : a 4H swing high/low already traded through since it formed is not
                   "unswept liquidity" any more (no obstacle)
  min_sl         : minimum stop distance ($)
  pivot_fresh    : 15m pivot S/R zones block TP1 only while fresh (untouched)
"""
import datetime, math
from v75_lab import (H, L, C, O, T, A, N, EV, MB, B1, PTOP, PBTM, ITOPY, IBTMY, X, A14, ST_LINE, ST_SIDE,
                     CHOP1H_PINE, HTF, NYH, NYD, simulate, sequential, wr, pf, supertrend)
UTC = datetime.timezone.utc
W0 = int(datetime.datetime(2026, 4, 3, tzinfo=UTC).timestamp() * 1000)
SPLIT6 = int(datetime.datetime(2026, 8, 1, tzinfo=UTC).timestamp() * 1000)
I0 = next(i for i in range(N) if T[i] >= W0)
DAYS6 = len({NYD[i] for i in range(I0, N) if NYD[i] is not None}) - 1   # trading days in the window

# 4H swing levels already traded through since they became the current level
SWEPT_HI = [False] * N; SWEPT_LO = [False] * N
_lh = _ll = None; _sh = _sl = False
for i in range(N):
    mh, ml = X['macroHigh'][i], X['macroLow'][i]
    if mh != _lh: _lh = mh; _sh = False
    if ml != _ll: _ll = ml; _sl = False
    SWEPT_HI[i] = _sh; SWEPT_LO[i] = _sl          # state BEFORE this bar (known at its open)
    if mh is not None and H[i] >= mh: _sh = True
    if ml is not None and L[i] <= ml: _sl = True


def liq_unswept_now(i, price, side):
    """Same 15m-window check the Brain uses (phase7_level_unswept)."""
    st = X['setupTime'][i]
    if price is None or st is None: return False
    snap = st + 15 * 60000
    for off in (0, 1, 2):
        j = i - off
        if j >= 0 and T[j] >= snap and ((H[j] >= price) if side == 1 else (L[j] <= price)):
            return False
    return True


def obstacles(i, s, cfg):
    """Clean-room obstacles for side s at bar i: (price, kind) list."""
    pk = X['pk'][i]; out = []
    zones = pk['pRes'] if s == 1 else pk['pSup']
    for z in zones:
        if z is None: continue
        if cfg.get('pivot_fresh') and not z[4]: continue
        out.append((z[1] if s == 1 else z[0], 'PIVOT'))
    eq = pk['eqh'] if s == 1 else pk['eql']
    for v in eq:
        if v is not None and liq_unswept_now(i, v, s): out.append((v, 'EQ'))
    m4 = X['macroHigh'][i] if s == 1 else X['macroLow'][i]
    if m4 is not None and liq_unswept_now(i, m4, s):
        swept = SWEPT_HI[i] if s == 1 else SWEPT_LO[i]
        if not (cfg.get('swept4h') and swept): out.append((m4, '4H'))
    if cfg.get('pdh'):
        pd = X['pdh'][i] if s == 1 else X['pdl'][i]
        if pd is not None and liq_unswept_now(i, pd, s): out.append((pd, 'PD'))
    return out


DEF = dict(htf='both', use_st=True, pb_max=11, chop_max=50.0, buf=0.3, max_sl=15.0, min_sl=2.0, tp1r=1.51, tp2r=2.5,
           front=0.1, cost=0.3, clean=True, pe_after_pivot=False, swept4h=False, pivot_fresh=False, pdh=False, extra=None)


def setups(cfg=None, i0=None, i1=None, ev=None, ptop=None, pbtm=None, itopy=None, ibtmy=None):
    c = dict(DEF); c.update(cfg or {})
    ev = ev or EV; ptop = ptop or PTOP; pbtm = pbtm or PBTM; itopy = itopy or ITOPY; ibtmy = ibtmy or IBTMY
    out = []; rej = {}
    for i in range(i0 if i0 is not None else I0, i1 or N - 1):
        a = A[i]
        if a is None: continue
        for s, kb in ((1, 'bull_ibreak'), (-1, 'bear_ibreak')):
            if not ev[kb][i]: continue
            if c['htf'] == 'both' and not (MB[i] == s and B1[i] == s): continue
            if c['htf'] == '1h' and B1[i] != s: continue
            if c['htf'] == '4h' and MB[i] != s: continue
            if c['use_st'] and ST_SIDE[i] != s: continue
            pbar = ptop[i] if s == 1 else pbtm[i]
            if pbar is None: continue
            if c['pb_max'] and i - pbar > c['pb_max']: continue
            if c['chop_max'] and (CHOP1H_PINE[i] is None or CHOP1H_PINE[i] >= c['chop_max']): continue
            if c['extra'] and not c['extra'](i, s): continue
            j0 = pbar + 1 if c['pe_after_pivot'] else pbar
            if i - pbar <= 200 and j0 <= i:
                ext = min(L[j0:i + 1]) if s == 1 else max(H[j0:i + 1])
            else:
                ext = min(L[i - 12:i + 1]) if s == 1 else max(H[i - 12:i + 1])
            stop = ext - s * c['buf'] * a; entry = C[i]; risk = (entry - stop) * s
            if risk <= 0: rej['bad'] = rej.get('bad', 0) + 1; continue
            if risk > c['max_sl']: rej['sl_wide'] = rej.get('sl_wide', 0) + 1; continue
            if risk < c['min_sl']: rej['sl_tight'] = rej.get('sl_tight', 0) + 1; continue
            tp1 = entry + s * c['tp1r'] * risk
            obst = sorted([p for p, k in obstacles(i, s, c) if (p - entry) * s > 0], key=lambda p: abs(p - entry)) if c['clean'] else []
            if obst and (obst[0] - tp1) * s < 0: rej['no_room'] = rej.get('no_room', 0) + 1; continue
            beyond = [p for p in obst if (p - tp1) * s > 0]; cap2 = entry + s * c['tp2r'] * risk
            tp2 = cap2 if not beyond or (beyond[0] - cap2) * s >= 0 else beyond[0] - s * c['front'] * a
            if (tp2 - tp1) * s <= 0.25 * risk: rej['no_tp2'] = rej.get('no_tp2', 0) + 1; continue
            st = dict(i=i, s=s, entry=entry, stop=stop, tp1=tp1, tp2=tp2, risk=risk, pbar=pbar, ext=ext,
                      brk=(itopy[i] if s == 1 else ibtmy[i]), room=(abs(obst[0] - entry) / risk if obst else 99.0))
            simulate(st, c['cost']); out.append(st)
    return out, rej


def stats(rows, days=None):
    if not rows: return dict(n=0)
    rs = [r['R'] for r in rows]; eq = pk = dd = 0.0; mcl = cur = 0
    for r in rows:
        eq += r['R']; pk = max(pk, eq); dd = max(dd, pk - eq); cur = 0 if r['win'] else cur + 1; mcl = max(mcl, cur)
    tr = [r for r in rows if T[r['i']] < SPLIT6]; te = [r for r in rows if T[r['i']] >= SPLIT6]
    return dict(n=len(rows), perday=len(rows) / (days or DAYS6), wr=wr(rows), pf=pf(rows), net=sum(rs), exp=sum(rs) / len(rs),
                dd=dd, mcl=mcl, n_tr=len(tr), wr_tr=wr(tr), n_te=len(te), wr_te=wr(te), pf_tr=pf(tr), pf_te=pf(te),
                maxrisk=max(r['risk'] for r in rows), tp1r=min((r['tp1'] - r['entry']) * r['s'] / r['risk'] for r in rows))


def fmt(s):
    if not s.get('n'): return 'n=0'
    return ('n=%3d %.2f/d WR %5.1f%% PF %.2f net %+6.1fR exp %+.2f DD %4.1f MCL %d | train n=%3d %5.1f%% PF %.2f | test n=%3d %5.1f%% PF %.2f'
            % (s['n'], s['perday'], 100 * s['wr'], s['pf'], s['net'], s['exp'], s['dd'], s['mcl'], s['n_tr'], 100 * s['wr_tr'], s['pf_tr'],
               s['n_te'], 100 * s['wr_te'], s['pf_te']))


def run(cfg=None, seq=True):
    rows, rej = setups(cfg)
    sel = sequential(rows) if seq else rows
    return sel, rej


if __name__ == '__main__':
    print('window %s .. %s, %d trading days (train to 2026-07-31, test from 2026-08-01)' % (
        datetime.datetime.fromtimestamp(T[I0] / 1000, UTC).date(), datetime.datetime.fromtimestamp(T[-1] / 1000, UTC).date(), DAYS6))
    base = dict()
    for lab, cfg in (('V7.5 as deployed', {}),
                     ('+ fix 4H swept liquidity', dict(swept4h=True)),
                     ('+ fix protected extreme after pivot', dict(pe_after_pivot=True)),
                     ('+ both fixes', dict(swept4h=True, pe_after_pivot=True)),
                     ('+ both fixes, min SL $0', dict(swept4h=True, pe_after_pivot=True, min_sl=0.0)),
                     ('+ both fixes, fresh pivots only', dict(swept4h=True, pe_after_pivot=True, pivot_fresh=True))):
        sel, rej = run(cfg)
        print('%-40s %s' % (lab, fmt(stats(sel))))
        print('%-40s rejections %s' % ('', rej))
