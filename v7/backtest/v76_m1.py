"""Creative test: keep the V7 trend stack on its usual timeframes (4H + 1H major
structure, 5m Supertrend, 15m clean-room obstacles, all from COMPLETED bars), but take the
entry trigger from the 1-minute chart: LuxAlgo internal BOS/CHoCH on 1m, fast pullback on 1m,
structural stop = 1m protected extreme - 0.3 x ATR(89, 1m), <= $15, TP1 1.51R, TP2 2.5R or
before the next obstacle. Latest 6 months, repaired data, one position at a time.
"""
import bisect, datetime
import ta, data_load
from v76_lab import I0, T, N, MB, B1, X, A, obstacles, DEF, SPLIT6, DAYS6, fmt, stats as stats5
from v75_lab import ST_SIDE, CHOP1H_PINE, wr, pf, sequential
UTC = datetime.timezone.utc
rows = data_load.load_minutes()
t_start = T[I0] - 20 * 86400000            # 1m warm-up before the window
m = [r for r in rows if r[0] >= t_start]
MT = [r[0] for r in m]; MO = [r[1] for r in m]; MH = [r[2] for r in m]; ML = [r[3] for r in m]; MC = [r[4] for r in m]
M = len(m)
MA = ta.atr(MH, ML, MC, 89)
# completed 5m bar index for each 1m bar (the 5m bar that ended at or before this minute's close)
T5 = T


def done5(k):
    j = bisect.bisect_right(T5, MT[k] + 60000 - 300000) - 1    # 5m bar whose close <= this minute's close
    return j


# LuxAlgo internal structure on 1m
top, btm = ta.swings(MH, ML, 50); itop, ibtm = ta.swings(MH, ML, 5)
top_y = btm_y = itop_y = ibtm_y = 0.0; itc = ibc = True; itr = 0
EVB = [False] * M; EVS = [False] * M; PT = [None] * M; PB = [None] * M; pt = pb = None
for k in range(M):
    p_it, p_ib = itop_y, ibtm_y
    if top[k]: top_y = top[k]
    if btm[k]: btm_y = btm[k]
    if itop[k]: itc = True; itop_y = itop[k]; pt = k - 5
    if ibtm[k]: ibc = True; ibtm_y = ibtm[k]; pb = k - 5
    if k > 0 and MC[k] > itop_y and MC[k - 1] <= p_it and itc and top_y != itop_y:
        EVB[k] = True; itc = False
    if k > 0 and MC[k] < ibtm_y and MC[k - 1] >= p_ib and ibc and btm_y != ibtm_y:
        EVS[k] = True; ibc = False
    PT[k] = pt; PB[k] = pb


def sim1(st, cost=0.3):
    k, s = st['k'], st['s']; stop, tp1, tp2 = st['stop'], st['tp1'], st['tp2']
    hit1 = False; res = None; j = k + 1
    while j < M:
        stop_hit = (ML[j] <= stop) if s == 1 else (MH[j] >= stop)
        if not hit1:
            if stop_hit: res = 'STOP'; break
            if (MH[j] >= tp1) if s == 1 else (ML[j] <= tp1):
                hit1 = True
                if (MH[j] >= tp2) if s == 1 else (ML[j] <= tp2): res = 'TP2'; break
        else:
            if stop_hit: res = 'STOP_AFTER_TP1'; break
            if (MH[j] >= tp2) if s == 1 else (ML[j] <= tp2): res = 'TP2'; break
        j += 1
    st['win'] = hit1; st['exit_k'] = j
    r1 = (tp1 - st['entry']) * s / st['risk']; r2 = (tp2 - st['entry']) * s / st['risk']; c = cost / st['risk']
    st['R'] = (-1 - c) if res == 'STOP' else (0.5 * r1 - 0.5 - c) if res == 'STOP_AFTER_TP1' else (0.5 * r1 + 0.5 * r2 - c) if res == 'TP2' else 0.0
    return st


def setups1(pb_max=11, use_st=True, chop_max=0, clean=True, buf=0.3, max_sl=15.0, min_sl=0.0, tp1r=1.51, tp2r=2.5, htf='both'):
    out = []
    for k in range(M):
        if MT[k] < T[I0]: continue
        for s, ev in ((1, EVB), (-1, EVS)):
            if not ev[k]: continue
            i5 = done5(k)
            if i5 < 0 or A[i5] is None: continue
            if htf == 'both' and not (MB[i5] == s and B1[i5] == s): continue
            if use_st and ST_SIDE[i5] != s: continue
            if chop_max and (CHOP1H_PINE[i5] is None or CHOP1H_PINE[i5] >= chop_max): continue
            pbar = PT[k] if s == 1 else PB[k]
            if pbar is None or (pb_max and k - pbar > pb_max): continue
            j0 = pbar + 1
            ext = min(ML[j0:k + 1]) if s == 1 else max(MH[j0:k + 1])
            a1 = MA[k] or 0.0
            stop = ext - s * buf * a1; entry = MC[k]; risk = (entry - stop) * s
            if risk <= 0 or risk > max_sl or risk < min_sl: continue
            tp1 = entry + s * tp1r * risk
            obst = sorted([p for p, kk in obstacles(i5, s, DEF) if (p - entry) * s > 0], key=lambda p: abs(p - entry)) if clean else []
            if obst and (obst[0] - tp1) * s < 0: continue
            beyond = [p for p in obst if (p - tp1) * s > 0]; cap2 = entry + s * tp2r * risk
            tp2 = cap2 if not beyond or (beyond[0] - cap2) * s >= 0 else beyond[0] - s * 0.1 * A[i5]
            if (tp2 - tp1) * s <= 0.25 * risk: continue
            st = dict(k=k, i=i5, s=s, entry=entry, stop=stop, tp1=tp1, tp2=tp2, risk=risk)
            out.append(sim1(st))
    return out


def seq1(rows):
    out = []; free = -1
    for r in sorted(rows, key=lambda r: r['k']):
        if r['k'] >= free: out.append(r); free = r['exit_k']
    return out


def line(lab, sel):
    tr = [r for r in sel if MT[r['k']] < SPLIT6]; te = [r for r in sel if MT[r['k']] >= SPLIT6]
    risk = sorted(r['risk'] for r in sel)
    print('%-46s n=%4d %.2f/d WR %5.1f%% PF %.2f net %+6.1fR | train n=%3d %5.1f%% | test n=%3d %5.1f%% | median SL $%.1f' % (
        lab, len(sel), len(sel) / DAYS6, 100 * wr(sel), pf(sel), sum(r['R'] for r in sel), len(tr), 100 * wr(tr), len(te), 100 * wr(te), risk[len(risk) // 2] if risk else 0))


if __name__ == '__main__':
    print('1m bars in window+warmup: %d' % M)
    for lab, kw in (('1m trigger, full V7 stack (fast<=11, ST, clean)', {}),
                    ('1m trigger, fast<=20', dict(pb_max=20)),
                    ('1m trigger, no fast filter', dict(pb_max=0)),
                    ('1m trigger, + chop<50', dict(chop_max=50)),
                    ('1m trigger, no clean room', dict(clean=False)),
                    ('1m trigger, min SL $3', dict(min_sl=3.0)),
                    ('1m trigger, min SL $5', dict(min_sl=5.0))):
        rows1 = setups1(**kw)
        line(lab + ' SEQ', seq1(rows1))
        line(lab + ' ALL', rows1)
