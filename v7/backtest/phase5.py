"""Port of the V7 Brain Phase 5 (MTF state) and the 5m chart engines that
Engine 6 consumes. Faithful to the Pine source; presentation-only code omitted.
"""
import ta
from data_load import key_fixed, key_4h, key_day, key_week, key_month

MINTICK = 0.001


def pcdiff(a, b):
    return abs((b - a) / a * 100)


def by_pc(amount, pc, add):
    x = amount * (pc / 100)
    return amount + x if add else amount - x


def rnd(x):
    return round(x / MINTICK) * MINTICK


def range_location(price, rh, rl):
    if price is None or rh is None or rl is None or not rh > rl:
        return 9
    prem = 0.95 * rh + 0.05 * rl
    eqh = 0.525 * rh + 0.475 * rl
    eql = 0.525 * rl + 0.475 * rh
    disc = 0.95 * rl + 0.05 * rh
    if price >= prem:
        return 1
    if price <= disc:
        return -1
    if eql <= price <= eqh:
        return 0
    return 2 if price > eqh else -2


def crossover(a, b, a1, b1):
    return a is not None and b is not None and a1 is not None and b1 is not None and a > b and a1 <= b1


def crossunder(a, b, a1, b1):
    return a is not None and b is not None and a1 is not None and b1 is not None and a < b and a1 >= b1


# ---------------------------------------------------------------------------
# HTF structure packet (4H macro / 1H bias)
# ---------------------------------------------------------------------------
def structure_states(bars, length=50):
    O = [b[1] for b in bars]; H = [b[2] for b in bars]; L = [b[3] for b in bars]; C = [b[4] for b in bars]
    top, btm = ta.swings(H, L, length)
    lastHigh = lastLow = None
    state = 0
    hcb = lcb = True
    out = []
    prevLastHigh = prevLastLow = None
    for i in range(len(bars)):
        plh, pll = lastHigh, lastLow
        if top[i] != 0:
            lastHigh = top[i]; hcb = True
        if btm[i] != 0:
            lastLow = btm[i]; lcb = True
        c1 = C[i - 1] if i > 0 else None
        bull = lastHigh is not None and hcb and crossover(C[i], lastHigh, c1, plh)
        bear = lastLow is not None and lcb and crossunder(C[i], lastLow, c1, pll)
        if bull:
            state = 1; hcb = False
        elif bear:
            state = -1; lcb = False
        out.append((state, lastHigh, lastLow))
    return out


# ---------------------------------------------------------------------------
# 15m setup packet
# ---------------------------------------------------------------------------
def three_candidates(zones, mode, close):
    """zones: list of [top,bottom,origin,confirmed,fresh,...]; newest first."""
    best = []  # list of (dist, zone)
    for z in zones:
        p = z[0] if mode == 1 else z[1] if mode == -1 else (z[0] + z[1]) / 2
        d = abs(close - p)
        if len(best) == 0 or d < best[0][0]:
            best.insert(0, (d, z))
        elif len(best) == 1 or d < best[1][0]:
            best.insert(1, (d, z))
        elif len(best) == 2 or d < best[2][0]:
            best.insert(2, (d, z))
        if len(best) > 3:
            best.pop()
    res = [(b[1][0], b[1][1], b[1][2], b[1][3], b[1][4]) for b in best]
    while len(res) < 3:
        res.append(None)
    return res


def three_levels(levels, above, close):
    best = []
    for lv in levels:
        lvl = lv[0]
        if not (lvl > close if above else lvl < close):
            continue
        d = abs(close - lvl)
        if len(best) == 0 or d < best[0][0]:
            best.insert(0, (d, lvl))
        elif len(best) == 1 or d < best[1][0]:
            best.insert(1, (d, lvl))
        elif len(best) == 2 or d < best[2][0]:
            best.insert(2, (d, lvl))
        if len(best) > 3:
            best.pop()
    res = [b[1] for b in best]
    while len(res) < 3:
        res.append(None)
    return res


def overlaps_strict(tT, tB, sT, sB):
    return (tT > sB and tT < sT) or (tB < sT and tB > sB) or (tT > sT and tB < sB) or (tB > sB and tT < sT)


def align_zone_arrays(src, tgt):
    if len(tgt) > 0:
        for z in list(src) if src is not tgt else src:
            t0 = tgt[0]
            if overlaps_strict(t0[0], t0[1], z[0], z[1]):
                tgt[0] = [z[0], z[1], min(t0[2], z[2]), max(t0[3], z[3]), t0[4] and z[4], t0[5]]


def setup_packets(bars, cfg):
    """Returns list: state after processing each 15m bar (dict)."""
    length = cfg.get('length', 50)
    ds_min = cfg.get('ds_min_pc_change', 0.2)
    ds_max = cfg.get('ds_max_pc_zone', 0.05)
    cap = cfg.get('cap', 100)
    left, right, mult, per, nPiv = 20, 15, 0.5, 5.0, 1
    eq_len, eq_thr = 3, 0.1
    T = [b[0] for b in bars]; O = [b[1] for b in bars]; H = [b[2] for b in bars]; L = [b[3] for b in bars]; C = [b[4] for b in bars]
    TC = [t + 15 * 60000 for t in T]
    N = len(bars)
    atr200 = ta.atr(H, L, C, 200)
    bearRun = ta.barssince([O[i] < C[i] for i in range(N)])
    bullRun = ta.barssince([O[i] > C[i] for i in range(N)])
    stop, sbtm = ta.swings(H, L, length)
    hao, hac = ta.ha_body(O, H, L, C)
    sH = [max(hao[i], hac[i]) for i in range(N)]
    sL = [min(hao[i], hac[i]) for i in range(N)]
    ph = ta.pivothigh(sH, left, right)
    pl = ta.pivotlow(sL, left, right)
    atr30 = ta.atr(H, L, C, 30)
    bandRaw = [None if atr30[i] is None else min(atr30[i] * mult, C[i] * (per / 100)) for i in range(N)]
    eqTop = ta.pivothigh(H, eq_len, eq_len)
    eqBot = ta.pivotlow(L, eq_len, eq_len)

    s1Level = None; s1Time = None
    demand = []; supply = []  # [top,bottom,origin,confirmed,fresh]
    bullOb = []; bearOb = []
    bullFvg = []; bearFvg = []
    pHigh = []; pLow = []  # [top,bottom,origin,confirmed,fresh,bullish]
    eqh = []; eql = []  # [level, origin, confirmed]
    lastSH = lastSL = None; lastSHBar = lastSLBar = None
    shcb = slcb = True
    prevEqTop = prevEqBot = None; prevEqTopTime = prevEqBotTime = None
    cumDelta = 0.0
    pretention = min(cap, max(nPiv, 3))
    out = []
    for i in range(N):
        t, o, h, l, c, tc = T[i], O[i], H[i], L[i], C[i], TC[i]
        br, ur = bearRun[i], bullRun[i]
        # --- D/S
        o1 = O[i - 1] if i >= 1 else None; c1 = C[i - 1] if i >= 1 else None
        o2 = O[i - 2] if i >= 2 else None; c2 = C[i - 2] if i >= 2 else None
        smallBase = o1 is not None and pcdiff(o1, c1) < 0.02
        if smallBase and o2 is not None and ((ur == 1 and o2 > c2) or (br == 1 and o2 < c2)):
            s1Level = o2
        elif ur == 1 or br == 1:
            s1Level = o1
        elif (ur is not None and ur > 1) or (br is not None and br > 1):
            pass
        else:
            s1Level = None
        if ur == 1 or br == 1:
            s1Time = T[i - 1]
        elif (ur is not None and ur > 1) or (br is not None and br > 1):
            pass
        else:
            s1Time = None
        demand = [z for z in demand if not (t >= z[3] and l <= z[0])]
        supply = [z for z in supply if not (t >= z[3] and h >= z[1])]
        db = ur
        if db is not None and 1 <= db < 500 and i - db >= 0:
            chg = pcdiff(c, O[i - (db - 1)])
            if s1Time is not None and s1Level is not None and not any(z[2] == s1Time for z in demand) and chg >= ds_min:
                top_ = s1Level
                bot = min(L[i - db], L[i - db + 1])
                height = pcdiff(top_, bot)
                base = pcdiff(O[i - db], C[i - db])
                bot = by_pc(top_, ds_max, False) if height > ds_max else bot
                if height > ds_max and base <= ds_max:
                    top_ = s1Level
                elif height > ds_max:
                    top_ = by_pc(C[i - db], ds_max / 5, True)
                top_, bot = rnd(top_), rnd(bot)
                top_, bot = max(top_, bot), min(top_, bot)
                demand.insert(0, [top_, bot, s1Time, tc, True])
        sb = br
        if sb is not None and 1 <= sb < 500 and i - sb >= 0:
            chg = pcdiff(c, O[i - (sb - 1)])
            if s1Time is not None and s1Level is not None and not any(z[2] == s1Time for z in supply) and chg >= ds_min:
                top_ = max(H[i - sb], H[i - sb + 1])
                bot = s1Level
                height = pcdiff(top_, bot)
                base = pcdiff(O[i - sb], C[i - sb])
                if height > ds_max and base <= ds_max:
                    bot = s1Level
                elif height > ds_max:
                    bot = by_pc(C[i - sb], ds_max / 5, False)
                top_ = by_pc(bot, ds_max, True) if height > ds_max else top_
                top_, bot = rnd(top_), rnd(bot)
                top_, bot = max(top_, bot), min(top_, bot)
                supply.insert(0, [top_, bot, s1Time, tc, True])
        if len(demand) > cap: demand.pop()
        if len(supply) > cap: supply.pop()
        d3 = three_candidates(demand, 1, c)
        s3 = three_candidates(supply, -1, c)

        # --- swing OB
        plSH, plSL = lastSH, lastSL
        if stop[i] != 0:
            lastSH = stop[i]; lastSHBar = i - length; shcb = True
        if sbtm[i] != 0:
            lastSL = sbtm[i]; lastSLBar = i - length; slcb = True
        bullOb = [z for z in bullOb if not (c < z[1])]
        bearOb = [z for z in bearOb if not (c > z[0])]
        for z in bullOb:
            if t >= z[3] and h >= z[1] and l <= z[0]:
                z[4] = False
        for z in bearOb:
            if t >= z[3] and h >= z[1] and l <= z[0]:
                z[4] = False
        if lastSH is not None and shcb and crossover(c, lastSH, c1, plSH):
            if lastSHBar is not None:
                scan = min(i - lastSHBar - 1, 499)
                sel = None
                for s in range(1, scan + 1):
                    j = i - s
                    if j < 0: break
                    a = atr200[j]
                    if a is not None and H[j] - L[j] < a * 2:
                        if sel is None or L[j] < sel[1]:
                            sel = (H[j], L[j], T[j])
                if sel is not None:
                    bullOb.insert(0, [sel[0], sel[1], sel[2], tc, True])
            shcb = False
        if lastSL is not None and slcb and crossunder(c, lastSL, c1, plSL):
            if lastSLBar is not None:
                scan = min(i - lastSLBar - 1, 499)
                sel = None
                for s in range(1, scan + 1):
                    j = i - s
                    if j < 0: break
                    a = atr200[j]
                    if a is not None and H[j] - L[j] < a * 2:
                        if sel is None or H[j] > sel[0]:
                            sel = (H[j], L[j], T[j])
                if sel is not None:
                    bearOb.insert(0, [sel[0], sel[1], sel[2], tc, True])
            slcb = False
        if len(bullOb) > cap: bullOb.pop()
        if len(bearOb) > cap: bearOb.pop()
        bo3 = three_candidates(bullOb, 1, c)
        so3 = three_candidates(bearOb, -1, c)

        # --- FVG
        bullFvg = [z for z in bullFvg if not (l < z[1])]
        bearFvg = [z for z in bearFvg if not (h > z[0])]
        for z in bullFvg:
            if t >= z[3] and h >= z[1] and l <= z[0]:
                z[4] = False
        for z in bearFvg:
            if t >= z[3] and h >= z[1] and l <= z[0]:
                z[4] = False
        if i >= 1:
            delta = (C[i - 1] - O[i - 1]) / O[i - 1] * 100
            cumDelta += abs(delta)
        else:
            delta = None
        thr = cumDelta / max(i, 1) * 2
        if i >= 2 and delta is not None:
            if l > H[i - 2] and C[i - 1] > H[i - 2] and delta > thr:
                bullFvg.insert(0, [l, H[i - 2], T[i - 1], tc, True])
            if h < L[i - 2] and C[i - 1] < L[i - 2] and -delta > thr:
                bearFvg.insert(0, [L[i - 2], h, T[i - 1], tc, True])
        if len(bullFvg) > cap: bullFvg.pop()
        if len(bearFvg) > cap: bearFvg.pop()
        bf3 = three_candidates(bullFvg, 0, c)
        sf3 = three_candidates(bearFvg, 0, c)

        # --- 15m pivot S/R
        band = bandRaw[i - right] / 2 if i - right >= 0 and bandRaw[i - right] is not None else None
        if ph[i] is not None and band is not None:
            pHigh.insert(0, [ph[i] + band, ph[i] - band, T[i - right], tc, True, False])
            if len(pHigh) > pretention: pHigh.pop()
        if pl[i] is not None and band is not None:
            pLow.insert(0, [pl[i] + band, pl[i] - band, T[i - right], tc, True, True])
            if len(pLow) > pretention: pLow.pop()
        align_zone_arrays(pHigh, pHigh)
        align_zone_arrays(pHigh, pLow)
        align_zone_arrays(pLow, pLow)
        align_zone_arrays(pLow, pHigh)
        for arr in (pHigh, pLow):
            for z in arr:
                if c > z[0] and not z[5]:
                    z[5] = True
                elif c < z[1] and z[5]:
                    z[5] = False
                if t >= z[3] and h >= z[1] and l <= z[0]:
                    z[4] = False
        sup = [z for z in pHigh if z[5]] + [z for z in pLow if z[5]]
        res = [z for z in pHigh if not z[5]] + [z for z in pLow if not z[5]]
        ps3 = three_candidates(sup, 1, c)
        pr3 = three_candidates(res, -1, c)

        # --- EQH / EQL
        eqh = [z for z in eqh if not (t >= z[2] and h > z[0])]
        eql = [z for z in eql if not (t >= z[2] and l < z[0])]
        a200 = atr200[i]
        if eqTop[i] is not None:
            et = eqTop[i]
            if prevEqTop is not None and a200 is not None and max(et, prevEqTop) < min(et, prevEqTop) + a200 * eq_thr:
                if not any(z[0] == et for z in eqh):
                    eqh.insert(0, [et, prevEqTopTime, tc])
            prevEqTop = et; prevEqTopTime = T[i - eq_len]
        if eqBot[i] is not None:
            eb = eqBot[i]
            if prevEqBot is not None and a200 is not None and min(eb, prevEqBot) > max(eb, prevEqBot) - a200 * eq_thr:
                if not any(z[0] == eb for z in eql):
                    eql.insert(0, [eb, prevEqBotTime, tc])
            prevEqBot = eb; prevEqBotTime = T[i - eq_len]
        if len(eqh) > cap: eqh.pop()
        if len(eql) > cap: eql.pop()
        eqh3 = three_levels(eqh, True, c)
        eql3 = three_levels(eql, False, c)

        out.append({
            'demand': d3, 'supply': s3, 'bullOb': bo3, 'bearOb': so3,
            'bullFvg': bf3, 'bearFvg': sf3, 'pSup': ps3, 'pRes': pr3,
            'eqh': eqh3, 'eql': eql3, 'swingHigh': lastSH, 'swingLow': lastSL,
        })
    return out


EMPTY_PACKET = {
    'demand': [None] * 3, 'supply': [None] * 3, 'bullOb': [None] * 3, 'bearOb': [None] * 3,
    'bullFvg': [None] * 3, 'bearFvg': [None] * 3, 'pSup': [None] * 3, 'pRes': [None] * 3,
    'eqh': [None] * 3, 'eql': [None] * 3, 'swingHigh': None, 'swingLow': None,
}


# ---------------------------------------------------------------------------
# 5m chart engines (structure + pivot reaction) and ATR(89)
# ---------------------------------------------------------------------------
def exec_context(bars):
    T = [b[0] for b in bars]; O = [b[1] for b in bars]; H = [b[2] for b in bars]; L = [b[3] for b in bars]; C = [b[4] for b in bars]
    N = len(bars)
    top, btm = ta.swings(H, L, 50)
    itop, ibtm = ta.swings(H, L, 5)
    top_y = btm_y = itop_y = ibtm_y = 0.0
    tc = bc = itc = ibc = True
    trend = itrend = 0
    ev = {k: [False] * N for k in ('bull_ichoch', 'bear_ichoch', 'bull_ibreak', 'bear_ibreak', 'bull_choch', 'bear_choch')}
    itr = [0] * N; tr_ = [0] * N
    for i in range(N):
        p_top_y, p_btm_y, p_itop_y, p_ibtm_y = top_y, btm_y, itop_y, ibtm_y
        if top[i]:
            tc = True; top_y = top[i]
        if btm[i]:
            bc = True; btm_y = btm[i]
        if itop[i]:
            itc = True; itop_y = itop[i]
        if ibtm[i]:
            ibc = True; ibtm_y = ibtm[i]
        c, c1 = C[i], (C[i - 1] if i > 0 else None)
        if crossover(c, itop_y, c1, p_itop_y) and itc and top_y != itop_y:
            if itrend < 0:
                ev['bull_ichoch'][i] = True
            ev['bull_ibreak'][i] = True
            itc = False; itrend = 1
        if crossover(c, top_y, c1, p_top_y) and tc:
            if trend < 0:
                ev['bull_choch'][i] = True
            tc = False; trend = 1
        if crossunder(c, ibtm_y, c1, p_ibtm_y) and ibc and btm_y != ibtm_y:
            if itrend > 0:
                ev['bear_ichoch'][i] = True
            ev['bear_ibreak'][i] = True
            ibc = False; itrend = -1
        if crossunder(c, btm_y, c1, p_btm_y) and bc:
            if trend > 0:
                ev['bear_choch'][i] = True
            bc = False; trend = -1
        itr[i] = itrend; tr_[i] = trend

    # Pivot S/R reaction (lean core, nPiv = 1)
    hao, hac = ta.ha_body(O, H, L, C)
    sH = [max(hao[i], hac[i]) for i in range(N)]
    sL = [min(hao[i], hac[i]) for i in range(N)]
    ph = ta.pivothigh(sH, 20, 15)
    pl = ta.pivotlow(sL, 20, 15)
    a30 = ta.atr(H, L, C, 30)
    bandRaw = [None if a30[i] is None else min(a30[i] * 0.5, C[i] * 0.05) for i in range(N)]
    hz = [None, None, None]  # top, bottom, bull
    lz = [None, None, None]
    trackH = trackL = 1
    pTrackH = pTrackL = None
    resBreak1 = supBreak1 = False
    bullCheck = [False] * N; bearCheck = [False] * N
    for i in range(N):
        band = bandRaw[i - 15] / 2 if i >= 15 and bandRaw[i - 15] is not None else None
        if ph[i] and band is not None:
            hz = [ph[i] + band, ph[i] - band, False]
        if pl[i] and band is not None:
            lz = [pl[i] + band, pl[i] - band, True]

        def ov(t_, s_):
            if t_[0] is None or s_[0] is None:
                return False
            return overlaps_strict(t_[0], t_[1], s_[0], s_[1])
        # align (High->High no-op, High->Low, Low->Low no-op, Low->High)
        if ov(lz, hz):
            lz = [hz[0], hz[1], lz[2]]
        if ov(hz, lz):
            hz = [lz[0], lz[1], hz[2]]
        c = C[i]
        for z, which in ((hz, 'h'), (lz, 'l')):
            if z[0] is None:
                continue
            isBull = bool(z[2])
            if c > z[0] and not isBull:
                z[2] = True
                if which == 'h': trackH += 1
                else: trackL += 1
            if c < z[1] and isBull:
                z[2] = False
                if which == 'h': trackH -= 1
                else: trackL -= 1
        moveAbove = pTrackH is not None and trackH > pTrackH
        moveBelow = pTrackL is not None and trackL < pTrackL
        resBreak = (pTrackL is not None and trackL > pTrackL) or moveAbove
        supBreak = (pTrackH is not None and trackH < pTrackH) or moveBelow
        fh = hz[0] is not None and L[i] < hz[0] and H[i] > hz[1]
        fl = lz[0] is not None and L[i] < lz[0] and H[i] > lz[1]
        hb = bool(hz[2]) if fh else False
        lb = bool(lz[2]) if fl else False
        bullCheck[i] = (not resBreak) and (not resBreak1) and (fh or fl) and C[i] > O[i] and (hb or lb)
        bearCheck[i] = (not supBreak) and (not supBreak1) and (fh or fl) and C[i] < O[i] and not (hb or lb)
        resBreak1, supBreak1 = resBreak, supBreak
        pTrackH, pTrackL = trackH, trackL
    atr89 = ta.atr(H, L, C, 89)
    return {'T': T, 'O': O, 'H': H, 'L': L, 'C': C, 'ev': ev, 'itrend': itr, 'trend': tr_,
            'bullReact': bullCheck, 'bearReact': bearCheck, 'atr': atr89}


def build_context(bars, cfg):
    """Everything Engine 6/7 reads, aligned to 5m bars."""
    m5 = bars['m5']
    ex = exec_context(m5)
    pk = setup_packets(bars['m15'], cfg)
    h4 = structure_states(bars['h4'])
    h1 = structure_states(bars['h1'])

    def index_map(htf, keyfn):
        idx = {b[0]: j for j, b in enumerate(htf)}
        return [idx.get(keyfn(b[0])) for b in m5]
    k15 = index_map(bars['m15'], key_fixed(15 * 60000))
    k1 = index_map(bars['h1'], key_fixed(3600000))
    k4 = index_map(bars['h4'], key_4h)
    kd = index_map(bars['d'], key_day)
    kw = index_map(bars['w'], key_week)
    km = index_map(bars['mo'], key_month)
    N = len(m5)
    ctx = dict(ex)
    ctx['pk'] = [pk[k - 1] if k is not None and k >= 1 else EMPTY_PACKET for k in k15]
    ctx['setupTime'] = [bars['m15'][k - 1][0] if k is not None and k >= 1 else None for k in k15]
    ctx['setupClose'] = [bars['m15'][k - 1][4] if k is not None and k >= 1 else None for k in k15]
    ctx['setupStart'] = [bars['m15'][k][0] if k is not None else None for k in k15]
    ctx['macroBias'] = [h4[k - 1][0] if k is not None and k >= 1 else None for k in k4]
    ctx['macroHigh'] = [h4[k - 1][1] if k is not None and k >= 1 else None for k in k4]
    ctx['macroLow'] = [h4[k - 1][2] if k is not None and k >= 1 else None for k in k4]
    ctx['bias1H'] = [h1[k - 1][0] if k is not None and k >= 1 else None for k in k1]
    ctx['pdh'] = [bars['d'][k - 1][2] if k is not None and k >= 1 else None for k in kd]
    ctx['pdl'] = [bars['d'][k - 1][3] if k is not None and k >= 1 else None for k in kd]
    ctx['pwh'] = [bars['w'][k - 1][2] if k is not None and k >= 1 else None for k in kw]
    ctx['pwl'] = [bars['w'][k - 1][3] if k is not None and k >= 1 else None for k in kw]
    ctx['pmh'] = [bars['mo'][k - 1][2] if k is not None and k >= 1 else None for k in km]
    ctx['pml'] = [bars['mo'][k - 1][3] if k is not None and k >= 1 else None for k in km]
    ctx['N'] = N
    return ctx
