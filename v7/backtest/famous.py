"""Standard, non-repainting formulas of widely used TradingView indicators, with
their published default settings (no tuning). All values use data up to and
including the current 5m bar; higher-timeframe values use the last COMPLETED bar.

Volume note: HistData has no volume, so VWAP is approximated by a session
TWAP of the typical price (equal weights).
"""
import math
import ta
from lab import H, L, C, O, T, N, A, DAYKEY

def sma(x, n):
    out = [None] * len(x); s = 0.0; q = []
    for i, v in enumerate(x):
        q.append(v); s += v
        if len(q) > n: s -= q.pop(0)
        if len(q) == n: out[i] = s / n
    return out

def ema(x, n):
    out = [None] * len(x); e = None; a = 2 / (n + 1)
    for i, v in enumerate(x):
        if v is None: out[i] = e; continue
        e = v if e is None else e + a * (v - e); out[i] = e
    return out

def stdev(x, n):
    out = [None] * len(x)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]; m = sum(w) / n
        out[i] = math.sqrt(sum((v - m) ** 2 for v in w) / n)
    return out

def rsi(x, n=14):
    g = [0.0] + [max(x[i] - x[i - 1], 0) for i in range(1, len(x))]
    l = [0.0] + [max(x[i - 1] - x[i], 0) for i in range(1, len(x))]
    ag, al = ta.rma(g, n), ta.rma(l, n)
    return [None if ag[i] is None or al[i] is None else (100.0 if al[i] == 0 else 100 - 100 / (1 + ag[i] / al[i])) for i in range(len(x))]

def supertrend(period=10, mult=3.0):
    """Exact port of Pine v5 ta.supertrend(factor, atrPeriod). Returns +1 (up) / -1 (down)
    in trade-side convention (Pine's own direction is -1 for up)."""
    atr = ta.atr(H, L, C, period); d = [0] * N
    lower_prev = upper_prev = None; st_prev = None; pdir = None
    for i in range(N):
        if atr[i] is None:
            continue
        src = (H[i] + L[i]) / 2
        lower = src - mult * atr[i]; upper = src + mult * atr[i]
        plb = lower_prev if lower_prev is not None else 0.0
        pub = upper_prev if upper_prev is not None else 0.0
        lower = lower if (lower > plb or C[i - 1] < plb) else plb
        upper = upper if (upper < pub or C[i - 1] > pub) else pub
        if atr[i - 1] is None or st_prev is None:
            direction = 1
        elif st_prev == pub:
            direction = -1 if C[i] > upper else 1
        else:
            direction = 1 if C[i] < lower else -1
        st = lower if direction == -1 else upper
        lower_prev, upper_prev, st_prev = lower, upper, st
        d[i] = 1 if direction == -1 else -1
    return d

def dmi_adx(n=14):
    tr = ta.tr(H, L, C)
    pdm = [0.0] + [max(H[i] - H[i - 1], 0) if H[i] - H[i - 1] > L[i - 1] - L[i] else 0.0 for i in range(1, N)]
    mdm = [0.0] + [max(L[i - 1] - L[i], 0) if L[i - 1] - L[i] > H[i] - H[i - 1] else 0.0 for i in range(1, N)]
    atr, sp, sm = ta.rma(tr, n), ta.rma(pdm, n), ta.rma(mdm, n)
    pdi = [None if atr[i] in (None, 0) or sp[i] is None else 100 * sp[i] / atr[i] for i in range(N)]
    mdi = [None if atr[i] in (None, 0) or sm[i] is None else 100 * sm[i] / atr[i] for i in range(N)]
    dx = [None if pdi[i] is None or mdi[i] is None or pdi[i] + mdi[i] == 0 else 100 * abs(pdi[i] - mdi[i]) / (pdi[i] + mdi[i]) for i in range(N)]
    adx = ta.rma([0.0 if v is None else v for v in dx], n)
    return pdi, mdi, adx

def session_twap():
    out = [None] * N; s = c = 0.0; cur = None
    for i in range(N):
        if DAYKEY[i] != cur: cur = DAYKEY[i]; s = c = 0.0
        s += (H[i] + L[i] + C[i]) / 3; c += 1; out[i] = s / c
    return out

def squeeze(length=20, bb_mult=2.0, kc_mult=1.5):
    """LazyBear Squeeze Momentum: squeeze on = BB inside KC; momentum = linreg."""
    basis = sma(C, length); dev = stdev(C, length)
    rng = sma(ta.tr(H, L, C), length)
    on = [False] * N; mom = [None] * N
    hh = ta.sliding_max(H, length); ll = ta.sliding_min(L, length)
    for i in range(N):
        if basis[i] is None or dev[i] is None or rng[i] is None: continue
        on[i] = (basis[i] - bb_mult * dev[i] > basis[i] - kc_mult * rng[i]) and (basis[i] + bb_mult * dev[i] < basis[i] + kc_mult * rng[i])
    # momentum: linreg of (close - avg(avg(hh,ll), sma)) over length
    val = [None] * N
    for i in range(N):
        if hh[i] is None or basis[i] is None: continue
        val[i] = C[i] - ((hh[i] + ll[i]) / 2 + basis[i]) / 2
    for i in range(length - 1, N):
        w = val[i - length + 1:i + 1]
        if any(v is None for v in w): continue
        n = length; xs = range(n); mx = (n - 1) / 2; my = sum(w) / n
        b = sum((x - mx) * (y - my) for x, y in zip(xs, w)) / sum((x - mx) ** 2 for x in xs)
        mom[i] = my + b * (n - 1 - mx)
    return on, mom

def wavetrend(n1=10, n2=21):
    ap = [(H[i] + L[i] + C[i]) / 3 for i in range(N)]
    esa = ema(ap, n1); d = ema([abs(ap[i] - esa[i]) for i in range(N)], n1)
    ci = [0.0 if d[i] in (None, 0) else (ap[i] - esa[i]) / (0.015 * d[i]) for i in range(N)]
    wt1 = ema(ci, n2); wt2 = sma(wt1, 4)
    return wt1, wt2

def range_filter(per=100, mult=3.0):
    """DonovanWall Range Filter direction."""
    absd = [0.0] + [abs(C[i] - C[i - 1]) for i in range(1, N)]
    avr = ema(absd, per); smr = ema(avr, per * 2 - 1)
    filt = [C[0]] + [None] * (N - 1); d = [0] * N; up = 0
    for i in range(1, N):
        r = (smr[i] or 0) * mult; f0 = filt[i - 1]
        if C[i] > f0: f = f0 if C[i] - r < f0 else C[i] - r
        else: f = f0 if C[i] + r > f0 else C[i] + r
        filt[i] = f
        up = 1 if f > f0 else -1 if f < f0 else up
        d[i] = up
    return d

def ut_bot(key=1.0, atr_period=10):
    """QuantNomad UT Bot: ATR trailing stop direction."""
    atr = ta.atr(H, L, C, atr_period); stop = [None] * N; d = [0] * N
    for i in range(1, N):
        if atr[i] is None: continue
        nl = key * atr[i]; p = stop[i - 1] if stop[i - 1] is not None else C[i]
        if C[i] > p and C[i - 1] > p: s = max(p, C[i] - nl)
        elif C[i] < p and C[i - 1] < p: s = min(p, C[i] + nl)
        elif C[i] > p: s = C[i] - nl
        else: s = C[i] + nl
        stop[i] = s; d[i] = 1 if C[i] > s else -1
    return d

def ichimoku(t=9, k=26, b=52):
    def mid(n):
        hh = ta.sliding_max(H, n); ll = ta.sliding_min(L, n)
        return [None if hh[i] is None else (hh[i] + ll[i]) / 2 for i in range(N)]
    tenkan, kijun, spanb = mid(t), mid(k), mid(b)
    spana = [None if tenkan[i] is None or kijun[i] is None else (tenkan[i] + kijun[i]) / 2 for i in range(N)]
    # cloud plotted 26 bars ahead -> the cloud at bar i was computed at i-26
    top = [None] * N; bot = [None] * N
    for i in range(k, N):
        a, bb = spana[i - k], spanb[i - k]
        if a is not None and bb is not None: top[i] = max(a, bb); bot[i] = min(a, bb)
    return tenkan, kijun, top, bot

def hull(n=55):
    def wma(x, m):
        out = [None] * len(x); den = m * (m + 1) / 2
        for i in range(m - 1, len(x)):
            w = x[i - m + 1:i + 1]
            if any(v is None for v in w): continue
            out[i] = sum((j + 1) * v for j, v in enumerate(w)) / den
        return out
    w1 = wma(C, n // 2); w2 = wma(C, n)
    diff = [None if w1[i] is None or w2[i] is None else 2 * w1[i] - w2[i] for i in range(N)]
    return wma(diff, int(math.sqrt(n)))

def donchian(n=20):
    return ta.sliding_max(H, n), ta.sliding_min(L, n)

def build_all():
    F = {}
    F['st'] = supertrend()
    F['pdi'], F['mdi'], F['adx'] = dmi_adx()
    F['vwap'] = session_twap()
    F['sqz'], F['sqzmom'] = squeeze()
    F['wt1'], F['wt2'] = wavetrend()
    F['rf'] = range_filter()
    F['ut'] = ut_bot()
    F['tenkan'], F['kijun'], F['ktop'], F['kbot'] = ichimoku()
    F['hma'] = hull()
    F['dch'], F['dcl'] = donchian()
    F['rsi'] = rsi(C, 14)
    F['e9'], F['e21'], F['e50'], F['e200'] = ema(C, 9), ema(C, 21), ema(C, 50), ema(C, 200)
    bb_mid = sma(C, 20); bb_sd = stdev(C, 20)
    F['bbpct'] = [None if bb_mid[i] is None or bb_sd[i] in (None, 0) else (C[i] - (bb_mid[i] - 2 * bb_sd[i])) / (4 * bb_sd[i]) for i in range(N)]
    return F
