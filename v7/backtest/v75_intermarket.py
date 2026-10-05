"""Intermarket study for V7.4 setups: silver (XAGUSD) SMT divergence / confirmation and
US Dollar Index (UDXUSD) confirmation. HistData M1, same timezone rule as gold."""
import os, glob, io, zipfile, datetime, pickle, bisect
from zoneinfo import ZoneInfo
from v75_lab import setups, features, sequential, stats, fmt, supertrend, T, N, H, L, C, SPLIT, wr, pf, ITOPY, IBTMY, BTMS, TOPS, BTM_BARS, TOP_BARS, prior_pivot
LON = ZoneInfo('Europe/London'); UTC = datetime.timezone.utc
HERE = os.path.dirname(os.path.abspath(__file__))


def load_5m(folder):
    cache = os.path.join(HERE, 'data', folder + '_5m.pkl')
    if os.path.exists(cache):
        return pickle.load(open(cache, 'rb'))
    bars = {}
    for fn in sorted(glob.glob(os.path.join(HERE, 'data', folder, '*.zip'))):
        z = zipfile.ZipFile(fn)
        name = [n for n in z.namelist() if n.endswith('.csv')][0]
        for line in io.TextIOWrapper(z.open(name)):
            p = line.strip().split(';')
            if len(p) < 5: continue
            dt = datetime.datetime.strptime(p[0], '%Y%m%d %H%M%S')
            guess = dt.replace(tzinfo=UTC) + datetime.timedelta(hours=5)
            off = 4 if guess.astimezone(LON).dst() else 5
            t = int((dt.replace(tzinfo=UTC) + datetime.timedelta(hours=off)).timestamp()) * 1000
            k = t - t % 300000
            o, h, l, c = float(p[1]), float(p[2]), float(p[3]), float(p[4])
            b = bars.get(k)
            if b is None: bars[k] = [o, h, l, c]
            else: b[1] = max(b[1], h); b[2] = min(b[2], l); b[3] = c
    pickle.dump(bars, open(cache, 'wb'))
    return bars


def align(bars):
    """Arrays aligned to gold's 5m bars; a missing bar repeats the last close."""
    h = [None] * N; l = [None] * N; c = [None] * N; last = None
    for i in range(N):
        b = bars.get(T[i])
        if b: h[i], l[i], c[i] = b[1], b[2], b[3]; last = b[3]
        elif last is not None: h[i] = l[i] = c[i] = last
    return h, l, c


def ffill(x):
    out = list(x); prev = None
    for i, v in enumerate(out):
        if v is None: out[i] = prev
        else: prev = v
    return out


def window_min(a, i0, i1):
    v = [a[k] for k in range(max(0, i0), i1 + 1) if a[k] is not None]
    return min(v) if v else None


def window_max(a, i0, i1):
    v = [a[k] for k in range(max(0, i0), i1 + 1) if a[k] is not None]
    return max(v) if v else None


SH, SL_, SC = align(load_5m('hd_xagusd'))
DH, DL, DC = align(load_5m('hd_udxusd'))
cov_s = sum(1 for v in SC if v is not None) / N; cov_d = sum(1 for v in DC if v is not None) / N
_shf, _slf, _scf = ffill(SH), ffill(SL_), ffill(SC)
_dhf, _dlf, _dcf = ffill(DH), ffill(DL), ffill(DC)
S_ST = supertrend([v or 0 for v in _shf], [v or 0 for v in _slf], [v or 0 for v in _scf], 10, 3.0)[1]
D_ST = supertrend([v or 0 for v in _dhf], [v or 0 for v in _dlf], [v or 0 for v in _dcf], 10, 3.0)[1]
# 15m Supertrend of DXY from 15m aggregation (last completed 15m bar)
from v75_lab import htf, K15
_dh15 = []; _dl15 = []; _dc15 = []; _d15done = [None] * N; _cur = None
for i in range(N):
    if _dcf[i] is None: _d15done[i] = None; continue
    if K15[i] != _cur:
        _cur = K15[i]; _dh15.append(_dhf[i]); _dl15.append(_dlf[i]); _dc15.append(_dcf[i])
    else:
        _dh15[-1] = max(_dh15[-1], _dhf[i]); _dl15[-1] = min(_dl15[-1], _dlf[i]); _dc15[-1] = _dcf[i]
    last = i == N - 1 or K15[i + 1] != K15[i]
    _d15done[i] = len(_dc15) - 1 if last else len(_dc15) - 2
D15_ST = supertrend(_dh15, _dl15, _dc15, 10, 3.0)[1]


def inter_features(st):
    i, s = st['i'], st['s']; f = {}
    pbar = st['pbar']
    if SC[i] is not None:
        f['silver_st'] = 1 if S_ST[i] == s else 0
        # silver confirms the break: its close beyond its own high/low at gold's broken pivot bar (+-2 bars)
        if pbar is not None:
            ref = window_max(SH, pbar - 2, pbar + 2) if s == 1 else window_min(SL_, pbar - 2, pbar + 2)
            if ref is not None:
                f['silver_break'] = 1 if (SC[i] - ref) * s > 0 else 0
            # SMT at the pullback extreme: compare pullback extreme vs the prior opposite pivot
            if s == 1:
                pv = prior_pivot(BTMS, BTM_BARS, pbar)
                if pv:
                    g_ll = st['ext'] < pv[1]
                    s_prev = window_min(SL_, pv[0] - 2, pv[0] + 2); s_pb = window_min(SL_, pbar, i)
                    if s_prev is not None and s_pb is not None:
                        s_ll = s_pb < s_prev
                        f['smt'] = 1 if g_ll != s_ll else 0
                        f['smt_gold_holds'] = 1 if (not g_ll and s_ll) else 0
            else:
                pv = prior_pivot(TOPS, TOP_BARS, pbar)
                if pv:
                    g_hh = st['ext'] > pv[1]
                    s_prev = window_max(SH, pv[0] - 2, pv[0] + 2); s_pb = window_max(SH, pbar, i)
                    if s_prev is not None and s_pb is not None:
                        s_hh = s_pb > s_prev
                        f['smt'] = 1 if g_hh != s_hh else 0
                        f['smt_gold_holds'] = 1 if (not g_hh and s_hh) else 0
    if DC[i] is not None:
        f['dxy_st_opp'] = 1 if D_ST[i] == -s else 0
        d = _d15done[i]
        if d is not None and d >= 0 and D15_ST[d]:
            f['dxy15_st_opp'] = 1 if D15_ST[d] == -s else 0
        if i >= 12 and DC[i - 12] is not None:
            f['dxy_1h_opp'] = 1 if (DC[i] - DC[i - 12]) * s < 0 else 0
    return f


def split(rows, key):
    a = [r for r in rows if r['g'].get(key) is not None]
    out = []
    for v in (0, 1):
        b = [r for r in a if r['g'][key] == v]
        bi = [r for r in b if T[r['i']] < SPLIT]; bo = [r for r in b if T[r['i']] >= SPLIT]
        out.append('%s=%d n=%4d WR %5.1f%% (IS %5.1f%% OOS %5.1f%%) PF %.2f' % (key, v, len(b), 100 * wr(b), 100 * wr(bi), 100 * wr(bo), pf(b)))
    print(' | '.join(out))


if __name__ == '__main__':
    print('coverage silver %.1f%% dxy %.1f%%' % (100 * cov_s, 100 * cov_d))
    rows = setups()
    for r in rows: r['f'] = features(r); r['g'] = inter_features(r)
    print('V7.4 setups (each alone) n=%d WR %.1f%%' % (len(rows), 100 * wr(rows)))
    for key in ('silver_st', 'silver_break', 'smt', 'smt_gold_holds', 'dxy_st_opp', 'dxy15_st_opp', 'dxy_1h_opp'):
        split(rows, key)
    pickle.dump(rows, open(os.path.join(HERE, 'data', 'v75_inter_rows.pkl'), 'wb'))
