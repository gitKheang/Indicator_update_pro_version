"""V7.3 research lab: one trade constructor shared by every setup family.

Rules (user specification):
  * SL = structural invalidation of the setup + volatility-adaptive buffer
    (optionally capped in $). No break-even.
  * TP1 = first real liquidity/structure level beyond 1.5R (front-run by a
    small buffer); TP2 = the next level beyond TP1. No such levels -> NO TRADE.
  * 50% closed at TP1, runner keeps the original SL. TP1/TP2 = WIN, SL = LOSS.
"""
import datetime, bisect
from zoneinfo import ZoneInfo
import ta
from run_v71 import context

NY = ZoneInfo('America/New_York')
UTC = datetime.timezone.utc
ctx = context()
H, L, C, O, T, A = ctx['H'], ctx['L'], ctx['C'], ctx['O'], ctx['T'], ctx['atr']
N = ctx['N']; EV = ctx['ev']; MB, B1 = ctx['macroBias'], ctx['bias1H']
A14 = ta.atr(H, L, C, 14)
SPLIT = int(datetime.datetime(2025, 7, 1, tzinfo=UTC).timestamp() * 1000)
TWO_Y = int(datetime.datetime(2024, 10, 1, tzinfo=UTC).timestamp() * 1000)
TRADING_DAYS = (T[-1] - T[0]) / 86400000 * 5 / 7

# ---------------------------------------------------------------- sessions (NY time)
ET_H = [0] * N; ET_M = [0] * N; DAYKEY = [0] * N
for i in range(N):
    d = datetime.datetime.fromtimestamp(T[i] / 1000, NY)
    ET_H[i] = d.hour; ET_M[i] = d.minute
    # trading day starts 18:00 ET
    DAYKEY[i] = (d + datetime.timedelta(hours=6)).date().toordinal()
def in_et(i, h0, m0, h1, m1):
    t = ET_H[i] * 60 + ET_M[i]
    return h0 * 60 + m0 <= t < h1 * 60 + m1

# Asian range = 20:00-00:00 ET (ICT), London = 02:00-05:00 ET, NY AM = 07:00-11:00 ET.
# For each bar: the completed Asia high/low of the current trading day (na until 00:00 ET),
# the London high/low once completed, and the running day high/low before this bar.
ASIA_H = [None] * N; ASIA_L = [None] * N; LON_H = [None] * N; LON_L = [None] * N
DAY_OPEN = [None] * N; MID_OPEN = [None] * N
_ah = _al = _lh = _ll = None; _cur = None; _dopen = _mopen = None
for i in range(N):
    if DAYKEY[i] != _cur:
        _cur = DAYKEY[i]; _ah = _al = _lh = _ll = None; _dopen = O[i]; _mopen = None
    hh = ET_H[i]
    if 20 <= hh <= 23:
        _ah = H[i] if _ah is None else max(_ah, H[i]); _al = L[i] if _al is None else min(_al, L[i])
    if hh == 0 and _mopen is None:
        _mopen = O[i]
    if 2 <= hh <= 4:
        _lh = H[i] if _lh is None else max(_lh, H[i]); _ll = L[i] if _ll is None else min(_ll, L[i])
    asia_done = hh < 18 and _ah is not None
    lon_done = 5 <= hh < 18 and _lh is not None
    ASIA_H[i] = _ah if asia_done else None; ASIA_L[i] = _al if asia_done else None
    LON_H[i] = _lh if lon_done else None; LON_L[i] = _ll if lon_done else None
    DAY_OPEN[i] = _dopen; MID_OPEN[i] = _mopen

# ---------------------------------------------------------------- unswept 5m fractal swings
FR = 5
_ph = ta.pivothigh(H, FR, FR); _pl = ta.pivotlow(L, FR, FR)
SWH = [None] * N; SWL = [None] * N   # tuples of unswept swing levels (nearest first) at each bar
_hs = []; _ls = []
for i in range(N):
    if _ph[i] is not None: _hs.append(_ph[i])
    if _pl[i] is not None: _ls.append(_pl[i])
    _hs = [x for x in _hs if x > H[i]][-30:]
    _ls = [x for x in _ls if x < L[i]][-30:]
    SWH[i] = tuple(_hs); SWL[i] = tuple(_ls)
# internal (5-bar) swing pivot bars, for protected extremes
_itop, _ibtm = ta.swings(H, L, 5)
PTOP = [None] * N; PBTM = [None] * N
_pt = _pb = None
for i in range(N):
    if _itop[i]: _pt = i - 5
    if _ibtm[i]: _pb = i - 5
    PTOP[i] = _pt; PBTM[i] = _pb

ZONES_UP = (('supply', 1), ('bearOb', 1), ('pRes', 1), ('bearFvg', 1))      # near edge index for longs = bottom
ZONES_DN = (('demand', 0), ('bullOb', 0), ('pSup', 0), ('bullFvg', 0))      # near edge for shorts = top

def levels(i, s, kinds='all'):
    """Liquidity / structure levels in the trade direction at bar i: [(price, kind)]."""
    pk = ctx['pk'][i]; out = []
    if s == 1:
        cand = [(ctx['pdh'][i], 'PDH'), (ctx['pwh'][i], 'PWH'), (ASIA_H[i], 'ASIA_H'), (LON_H[i], 'LON_H'),
                (pk['swingHigh'], 'SW15'), (ctx['macroHigh'][i], 'SW4H')] + [(v, 'EQH') for v in pk['eqh']] + [(v, 'SW5') for v in SWH[i][-6:]]
        zones = [(z[1] if z else None, f) for f, _ in ZONES_UP for z in pk[f]]
    else:
        cand = [(ctx['pdl'][i], 'PDL'), (ctx['pwl'][i], 'PWL'), (ASIA_L[i], 'ASIA_L'), (LON_L[i], 'LON_L'),
                (pk['swingLow'], 'SW15'), (ctx['macroLow'][i], 'SW4H')] + [(v, 'EQL') for v in pk['eql']] + [(v, 'SW5') for v in SWL[i][-6:]]
        zones = [(z[0] if z else None, f) for f, _ in ZONES_DN for z in pk[f]]
    if kinds in ('all', 'liq'):
        out += [(p, k) for p, k in cand if p is not None]
    if kinds in ('all', 'zones'):
        out += [(p, k) for p, k in zones if p is not None]
    return out

DEF = dict(buf_k=0.3, buf_src='atr89', max_sl=15.0, min_sl=2.0, min_r=1.5, tp_front=0.05, tp_kinds='all',
           clean='none', max_tp1_r=99.0, part=0.5, cost=0.3, entry='close', fill_bars=12, one_at_a_time=True)

def construct(i, s, inval, c, entry=None):
    """Returns trade dict or (None, reason)."""
    a = A[i] if c['buf_src'] == 'atr89' else A14[i]
    if a is None: return None, 'na'
    e = C[i] if entry is None else entry
    stop = inval - s * c['buf_k'] * a
    risk = (e - stop) * s
    if risk <= 0: return None, 'bad'
    if risk > c['max_sl']: return None, 'sl_wide'
    if risk < c['min_sl']: return None, 'sl_tight'
    front = c['tp_front'] * a
    lv = sorted(set(round(p, 3) for p, k in levels(i, s, c['tp_kinds']) if (p - e) * s > 0 and (p - (H[i] if s == 1 else L[i])) * s > 0),
                key=lambda p: abs(p - e))
    tg = [p - s * front for p in lv]
    if c['clean'] == 'zones':
        obst = [p for p, k in levels(i, s, 'zones') if 0 < (p - e) * s <= c['min_r'] * risk]
        if obst: return None, 'blocked'
    if c['clean'] == 'all':
        if any(0 < (p - e) * s <= c['min_r'] * risk for p in lv): return None, 'blocked'
    if c.get('tp_mode') == 'hybrid':
        tp1 = e + s * c['hyb_tp1'] * risk
        beyond = [p for p in tg if (p - tp1) * s > c.get('hyb_gap', 0.25) * risk]
        if not beyond or (beyond[0] - e) * s > c.get('hyb_max', 99) * risk: return None, 'no_tp2'
        return dict(side=s, entry=e, stop=stop, tp1=tp1, tp2=beyond[0], risk=risk, tp1R=c['hyb_tp1'], tp2R=(beyond[0] - e) * s / risk), None
    beyond = [p for p in tg if (p - e) * s > c['min_r'] * risk]
    if len(beyond) < 2: return None, 'no_room'
    tp1, tp2 = beyond[0], beyond[1]
    if (tp1 - e) * s > c['max_tp1_r'] * risk: return None, 'tp1_far'
    return dict(side=s, entry=e, stop=stop, tp1=tp1, tp2=tp2, risk=risk, tp1R=(tp1 - e) * s / risk, tp2R=(tp2 - e) * s / risk), None

def simulate(tr, i0, c, max_bars=2000):
    """Stop-first, no break-even. Fills at i0 close (market) or a limit within fill_bars."""
    s = tr['side']; start = i0
    if c['entry'] != 'close':
        f = None
        for j in range(i0 + 1, min(N, i0 + 1 + c['fill_bars'])):
            if (H[j] >= tr['tp1']) if s == 1 else (L[j] <= tr['tp1']): return None
            if L[j] <= tr['entry'] <= H[j]:
                f = j; break
        if f is None: return None
        if (L[f] <= tr['stop']) if s == 1 else (H[f] >= tr['stop']):
            tr.update(fill=f, exit=f, outcome='STOP', tp1Hit=False); return tr
        start = f
    t1 = False
    for j in range(start + 1, min(N, start + max_bars)):
        st = (L[j] <= tr['stop']) if s == 1 else (H[j] >= tr['stop'])
        h1 = (H[j] >= tr['tp1']) if s == 1 else (L[j] <= tr['tp1'])
        h2 = (H[j] >= tr['tp2']) if s == 1 else (L[j] <= tr['tp2'])
        if st:
            tr.update(fill=start, exit=j, outcome='STOP_AFTER_TP1' if t1 else 'STOP', tp1Hit=t1); return tr
        if h2:
            tr.update(fill=start, exit=j, outcome='TP2', tp1Hit=True); return tr
        if h1: t1 = True
    tr.update(fill=start, exit=min(N - 1, start + max_bars), outcome='OPEN', tp1Hit=t1); return tr

def r_of(t, c):
    p = c['part']; cost = c['cost'] / t['risk']
    if t['outcome'] == 'STOP': return -1 - cost
    if t['outcome'] == 'STOP_AFTER_TP1': return p * t['tp1R'] - (1 - p) - cost
    if t['outcome'] == 'TP2': return p * t['tp1R'] + (1 - p) * t['tp2R'] - cost
    return 0.0

def backtest(events, cfg=None, label=None, show=True):
    """events: iterable of (i, side, invalidation[, entry_price, tag])."""
    c = dict(DEF); c.update(cfg or {})
    trades = []; rej = {}; busy_until = -1
    for evt in events:
        i, s, inval = evt[0], evt[1], evt[2]
        ent = evt[3] if len(evt) > 3 else None
        if c['one_at_a_time'] and i <= busy_until:
            rej['busy'] = rej.get('busy', 0) + 1; continue
        tr, why = construct(i, s, inval, c, None if c['entry'] == 'close' else ent)
        if tr is None:
            rej[why] = rej.get(why, 0) + 1; continue
        tr['i'] = i; tr['t'] = T[i]; tr['tag'] = evt[4] if len(evt) > 4 else ''
        res = simulate(tr, i, c)
        if res is None:
            rej['nofill'] = rej.get('nofill', 0) + 1; continue
        if res['outcome'] == 'OPEN': continue
        trades.append(res); busy_until = res['exit']
    out = dict(trades=trades, rej=rej, cfg=c)
    if show: summarize(out, label or '')
    return out

def metrics(tr, c, days=None):
    if not tr: return None
    rs = [r_of(t, c) for t in tr]
    w = sum(1 for t in tr if t['tp1Hit'])
    gp = sum(r for r in rs if r > 0); gl = -sum(r for r in rs if r < 0)
    eq = pk = dd = 0; mcl = cur = 0
    for t, r in zip(tr, rs):
        eq += r; pk = max(pk, eq); dd = max(dd, pk - eq)
        cur = cur + 1 if not t['tp1Hit'] else 0; mcl = max(mcl, cur)
    days_traded = len(set(datetime.datetime.fromtimestamp(t['t'] / 1000, NY).date() for t in tr))
    return dict(n=len(tr), perday=len(tr) / days if days else None, wins=w, losses=len(tr) - w, wr=w / len(tr),
                pf=gp / gl if gl else float('inf'), exp=sum(rs) / len(rs), net=sum(rs), dd=dd, mcl=mcl,
                tp1R=sum(t['tp1R'] for t in tr) / len(tr), tp2R=sum(t['tp2R'] for t in tr) / len(tr),
                risk=sorted(t['risk'] for t in tr)[len(tr) // 2], days=days_traded)

def fmt(m):
    if not m: return 'n=0'
    return 'n=%4d%s W/L %d/%d WR %4.1f%% PF %.2f exp %+.3f net %+6.1fR DD %4.1f MCL %2d | TP1 %.2fR TP2 %.2fR SL$ %.1f' % (
        m['n'], (' %.2f/d' % m['perday']) if m['perday'] else '', m['wins'], m['losses'], 100 * m['wr'], m['pf'], m['exp'],
        m['net'], m['dd'], m['mcl'], m['tp1R'], m['tp2R'], m['risk'])

def summarize(res, label):
    tr, c = res['trades'], res['cfg']
    print('== %s' % label)
    print('   ALL', fmt(metrics(tr, c, TRADING_DAYS)))
    print('   IS ', fmt(metrics([t for t in tr if t['t'] < SPLIT], c)))
    print('   OOS', fmt(metrics([t for t in tr if t['t'] >= SPLIT], c)))

# ---------------------------------------------------------------- setup families
def protected(i, s):
    pbar = PTOP[i] if s == 1 else PBTM[i]
    if pbar is not None and i - pbar <= 200:
        return min(L[pbar:i + 1]) if s == 1 else max(H[pbar:i + 1])
    return min(L[i - 12:i + 1]) if s == 1 else max(H[i - 12:i + 1])

def ev_trend(htf='both', trig=('ibreak',)):
    out = []
    for i in range(600, N - 1):
        for s, kb, kc in ((1, 'bull_ibreak', 'bull_ichoch'), (-1, 'bear_ibreak', 'bear_ichoch')):
            f = ('ibreak' in trig and EV[kb][i]) or ('ichoch' in trig and EV[kc][i])
            if not f: continue
            if htf == 'both' and not (MB[i] == s and B1[i] == s): continue
            if htf == '4h' and MB[i] != s: continue
            out.append((i, s, protected(i, s), None, 'trend'))
    return out
