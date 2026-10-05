"""Setup families from the research, all producing (i, side, invalidation, limit_entry, tag)."""
from lab import *

def _liq_levels_below(i):
    pk = ctx['pk'][i]
    return [(ctx['pdl'][i], 'PDL'), (ASIA_L[i], 'ASIA'), (LON_L[i], 'LON'), (pk['swingLow'], 'SW15')] + [(v, 'EQL') for v in pk['eql']]
def _liq_levels_above(i):
    pk = ctx['pk'][i]
    return [(ctx['pdh'][i], 'PDH'), (ASIA_H[i], 'ASIA'), (LON_H[i], 'LON'), (pk['swingHigh'], 'SW15')] + [(v, 'EQH') for v in pk['eqh']]

def ev_sweep(win=12, need_body=0.0, htf=None, kz=False):
    """Liquidity sweep then internal CHoCH back the other way (ICT turtle-soup / MSS).
    Long: within `win` bars a low traded below a liquidity level and the CHoCH bar closes above it."""
    out = []
    for i in range(600, N - 1):
        for s, key in ((1, 'bull_ichoch'), (-1, 'bear_ichoch')):
            if not EV[key][i]: continue
            if htf == '4h' and MB[i] != s: continue
            if htf == 'both' and not (MB[i] == s and B1[i] == s): continue
            if need_body and (C[i] - O[i]) * s < need_body * A[i]: continue
            if kz and not (in_et(i, 2, 0, 5, 0) or in_et(i, 7, 0, 11, 0)): continue
            ext = min(L[i - win:i + 1]) if s == 1 else max(H[i - win:i + 1])
            lv = _liq_levels_below(i - win) if s == 1 else _liq_levels_above(i - win)
            hit = [k for v, k in lv if v is not None and ((ext < v < C[i]) if s == 1 else (ext > v > C[i]))]
            if hit:
                out.append((i, s, ext, None, 'sweep:' + hit[0]))
    return out

def ev_asia_fb(kz_only=True):
    """Asian range false breakout: a 5m close outside the completed Asia range, then a close back inside."""
    out = []; state = {}
    for i in range(600, N - 1):
        ah, al = ASIA_H[i], ASIA_L[i]
        if ah is None: continue
        d = DAYKEY[i]
        st = state.setdefault(d, {'up': None, 'dn': None, 'done': set()})
        if C[i] > ah and st['up'] is None: st['up'] = i
        if C[i] < al and st['dn'] is None: st['dn'] = i
        if kz_only and not (in_et(i, 2, 0, 11, 0)): continue
        if st['up'] is not None and 'S' not in st['done'] and C[i] < ah and i - st['up'] <= 24:
            ext = max(H[st['up']:i + 1]); st['done'].add('S'); out.append((i, -1, ext, None, 'asiaFB'))
        if st['dn'] is not None and 'L' not in st['done'] and C[i] > al and i - st['dn'] <= 24:
            ext = min(L[st['dn']:i + 1]); st['done'].add('L'); out.append((i, 1, ext, None, 'asiaFB'))
    return out

def ev_fvg(disp=1.0, htf='both', kz=False):
    """Displacement candle (body >= disp*ATR) that leaves a 5m FVG in the trend direction;
    limit entry at the FVG midpoint; invalidation = low (high) of the candle before the displacement."""
    out = []
    for i in range(600, N - 1):
        a = A[i]
        if a is None: continue
        for s in (1, -1):
            if htf == 'both' and not (MB[i] == s and B1[i] == s): continue
            if htf == '4h' and MB[i] != s: continue
            body = (C[i - 1] - O[i - 1]) * s
            if body < disp * a: continue
            gap = (L[i] - H[i - 2]) if s == 1 else (L[i - 2] - H[i])
            if gap <= 0: continue
            if kz and not (in_et(i, 2, 0, 5, 0) or in_et(i, 7, 0, 11, 0)): continue
            mid = (L[i] + H[i - 2]) / 2 if s == 1 else (L[i - 2] + H[i]) / 2
            inval = min(L[i - 2], L[i - 1]) if s == 1 else max(H[i - 2], H[i - 1])
            out.append((i, s, inval, mid, 'fvg'))
    return out

def ev_orb(minutes=15, htf='4h'):
    """NY opening range (09:30 ET + minutes) breakout by a 5m close, in the 4H bias direction."""
    out = []; rng = {}
    nb = minutes // 5
    for i in range(600, N - 1):
        d = DAYKEY[i]
        if in_et(i, 9, 30, 9, 30 + minutes):
            r = rng.setdefault(d, [H[i], L[i], 0, False])
            r[0] = max(r[0], H[i]); r[1] = min(r[1], L[i]); r[2] += 1
            continue
        r = rng.get(d)
        if not r or r[2] < nb or r[3] or not in_et(i, 9, 30 + minutes, 12, 0): continue
        for s in (1, -1):
            if htf == '4h' and MB[i] != s: continue
            if (C[i] > r[0]) if s == 1 else (C[i] < r[1]):
                r[3] = True; out.append((i, s, r[1] if s == 1 else r[0], None, 'orb'))
    return out

def ev_aoi(min_disp=0.0, htf=None, conf='ibreak', win=24):
    """First touch of a fresh 15m zone, then (within win bars) an internal break back in the zone's
    direction. Invalidation = zone far edge or the extreme since the touch, whichever is further."""
    out = []; seen = set(); pending = []
    fams = (('demand', 1), ('bullOb', 1), ('pSup', 1), ('supply', -1), ('bearOb', -1), ('pRes', -1))
    for i in range(600, N - 1):
        pk = ctx['pk'][i]
        for fam, s in fams:
            for z in pk[fam]:
                if z is None or not z[4]: continue
                key = (fam, z[2])
                if key in seen: continue
                top, bot = z[0], z[1]
                if (s == 1 and C[i - 1] < bot) or (s == -1 and C[i - 1] > top): seen.add(key); continue
                if L[i] <= top and H[i] >= bot:
                    seen.add(key)
                    if htf == 'both' and not (MB[i] == s and B1[i] == s): continue
                    if htf == '4h' and MB[i] != s: continue
                    pending.append(dict(s=s, top=top, bot=bot, t0=i, fam=fam))
        keep = []
        for p in pending:
            s = p['s']
            if i - p['t0'] > win: continue
            far = p['bot'] if s == 1 else p['top']
            if (C[i] < far) if s == 1 else (C[i] > far): continue
            k = ('bull_ibreak' if s == 1 else 'bear_ibreak') if conf == 'ibreak' else ('bull_ichoch' if s == 1 else 'bear_ichoch')
            if i > p['t0'] and EV[k][i] and (C[i] - O[i]) * s >= min_disp * A[i]:
                ext = min(L[p['t0']:i + 1]) if s == 1 else max(H[p['t0']:i + 1])
                inval = min(ext, far) if s == 1 else max(ext, far)
                out.append((i, s, inval, None, 'aoi:' + p['fam']))
                continue
            keep.append(p)
        pending = keep
    return out
