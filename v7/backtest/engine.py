"""Port of V7 Engine 6 (AOI lock/touch/confirm), Engine 7 (package
construction) and the Execution + UI lifecycle. Config-driven so variants can
be tested; defaults reproduce the current deployed V7 exactly.
"""
from phase5 import range_location

DEFAULT = dict(
    minScore=55.0, wSource=10.0, wMacro=15.0, wBias=10.0, wLoc=10.0, wFresh=15.0,
    wMeta=5.0, wLiq=5.0, wRecent=5.0, recentHours=168,
    rejectOpposite=True,
    maxLockBars=288, maxConfirmBars=24, maxLockDistATR=6.0, readyRetention=24,
    retarget=True,
    confirmTypes=('ichoch', 'ibos', 'schoch', 'react'),
    minImpulseATR=0.75,
    stopDist=10.0, minTP1R=1.5,
    entries=('F38.2', 'F61.8'),
    pendingBars=24,
    mgmt='be',            # after TP1: 'be' = stop to entry, 'orig' = keep stop
    cost=0.0,             # round-trip cost in price units, charged on every fill
)

ZONE_FAMILIES_LONG = (('demand', 'DEMAND', 1), ('bullOb', 'BULL_OB', 2), ('pSup', 'PIVOT_SUPPORT', 8))
ZONE_FAMILIES_SHORT = (('supply', 'SUPPLY', 1), ('bearOb', 'BEAR_OB', 2), ('pRes', 'PIVOT_RESISTANCE', 8))


class Engine:
    def __init__(self, ctx, cfg=None, start=0, end=None, hooks=None):
        self.x = ctx
        self.c = dict(DEFAULT)
        if cfg:
            self.c.update(cfg)
        self.start = start
        self.end = ctx['N'] if end is None else end
        self.hooks = hooks or {}

    # ------------------------------------------------------------------ helpers
    def touched_since_snapshot(self, i, top, bottom):
        x = self.x
        st = x['setupTime'][i]
        if st is None or top is None or bottom is None or top < bottom:
            return False
        snap = st + 15 * 60000
        for off in (0, 1, 2):
            j = i - off
            if j < 0:
                continue
            if x['T'][j] >= snap and x['L'][j] <= top and x['H'][j] >= bottom:
                return True
        return False

    def fresh_overlap(self, i, aT, aB, zones):
        for z in zones:
            if z is None:
                continue
            zT, zB, zf = z[0], z[1], z[4]
            if zf and not self.touched_since_snapshot(i, zT, zB) and zT >= zB and max(aB, zB) <= min(aT, zT):
                return True
        return False

    def liquidity(self, i, side, ref):
        x = self.x; pk = x['pk'][i]
        h, l = x['H'][i], x['L'][i]
        if side == 1:
            levels = [(v, 'EQH') for v in pk['eqh']] + [(x['pdh'][i], 'PDH'), (x['pwh'][i], 'PWH'), (x['pmh'][i], 'PMH'),
                                                        (pk['swingHigh'], '15M_SWING_HIGH'), (x['macroHigh'][i], '4H_SWING_HIGH')]
            bound = max(ref, h)
        else:
            levels = [(v, 'EQL') for v in pk['eql']] + [(x['pdl'][i], 'PDL'), (x['pwl'][i], 'PWL'), (x['pml'][i], 'PML'),
                                                        (pk['swingLow'], '15M_SWING_LOW'), (x['macroLow'][i], '4H_SWING_LOW')]
            bound = min(ref, l)
        best, kind = None, 'NONE'
        for v, k in levels:
            if v is None:
                continue
            if (v > bound) if side == 1 else (v < bound):
                if best is None or abs(v - ref) < abs(best - ref):
                    best, kind = v, k
        return best, kind

    def location_score(self, side, price, pk):
        c = self.c
        loc = range_location(price, pk['swingHigh'], pk['swingLow'])
        if (side == 1 and loc == -1) or (side == -1 and loc == 1):
            return c['wLoc']
        if (side == 1 and loc == -2) or (side == -1 and loc == 2):
            return c['wLoc'] * 0.5
        if (side == 1 and loc == 1) or (side == -1 and loc == -1):
            return -c['wLoc']
        if (side == 1 and loc == 2) or (side == -1 and loc == -2):
            return -c['wLoc'] * 0.5
        return 0.0

    def is_consumed(self, side, anchor, origin):
        return origin is not None and (side, anchor, origin) in self.consumedSet

    def mark_consumed(self, side, anchor, origin):
        if side != 0 and origin is not None and (side, anchor, origin) not in self.consumedSet:
            self.consumed.insert(0, (side, anchor, origin))
            self.consumedSet.add((side, anchor, origin))
            if len(self.consumed) > 250:
                old = self.consumed.pop()
                self.consumedSet.discard(old)

    def build_candidate(self, i, z, side, anchor, mask):
        x = self.x; c = self.c; pk = x['pk'][i]
        if z is None:
            return None
        top, bottom, origin, confirmed, fresh = z
        close = x['C'][i]
        if top is None or bottom is None or top < bottom:
            return None
        if origin is None or confirmed is None or not fresh:
            return None
        if not (top <= close if side == 1 else bottom >= close):
            return None
        if self.touched_since_snapshot(i, top, bottom):
            return None
        if self.is_consumed(side, anchor, origin):
            return None
        macro, b1 = x['macroBias'][i], x['bias1H'][i]
        if c['rejectOpposite'] and macro == -side and b1 == -side:
            return None
        dist = max(close - top, 0.0) if side == 1 else max(bottom - close, 0.0)
        atr = x['atr'][i]
        if atr is None or atr <= 0 or dist > c['maxLockDistATR'] * atr:
            return None
        if side == 1:
            hasDs = self.fresh_overlap(i, top, bottom, pk['demand'])
            hasOb = self.fresh_overlap(i, top, bottom, pk['bullOb'])
            hasFvg = self.fresh_overlap(i, top, bottom, pk['bullFvg'])
            hasPv = self.fresh_overlap(i, top, bottom, pk['pSup'])
        else:
            hasDs = self.fresh_overlap(i, top, bottom, pk['supply'])
            hasOb = self.fresh_overlap(i, top, bottom, pk['bearOb'])
            hasFvg = self.fresh_overlap(i, top, bottom, pk['bearFvg'])
            hasPv = self.fresh_overlap(i, top, bottom, pk['pRes'])
        ds = hasDs or mask == 1
        ob = hasOb or mask == 2
        pv = hasPv or mask == 8
        n = int(ds) + int(ob) + int(hasFvg) + int(pv)
        liq, liqKind = self.liquidity(i, side, top if side == 1 else bottom)
        ctxScore = (c['wMacro'] if macro == side else -c['wMacro'] if macro == -side else 0.0) + \
                   (c['wBias'] if b1 == side else -c['wBias'] if b1 == -side else 0.0)
        t = x['T'][i]
        recent = t >= confirmed and t - confirmed <= c['recentHours'] * 3600000
        score = n * c['wSource'] + ctxScore + self.location_score(side, (top + bottom) / 2, pk) + \
            c['wFresh'] + c['wMeta'] + (c['wRecent'] if recent else 0.0) + (c['wLiq'] if liq is not None else 0.0)
        cand = dict(side=side, top=top, bottom=bottom, anchor=anchor, origin=origin, confirmed=confirmed,
                    score=score, liq=liq, liqKind=liqKind, dist=dist, n=n,
                    mask=(1 if ds else 0) + (2 if ob else 0) + (4 if hasFvg else 0) + (8 if pv else 0))
        if 'candidate' in self.hooks:
            cand = self.hooks['candidate'](self, i, cand)
        return cand

    # ------------------------------------------------------------- Engine 7
    def liq_unswept(self, i, price, side):
        x = self.x
        st = x['setupTime'][i]
        if price is None or st is None:
            return False
        snap = st + 15 * 60000
        for off in (0, 1, 2):
            j = i - off
            if j < 0:
                continue
            if x['T'][j] >= snap and ((x['H'][j] >= price) if side == 1 else (x['L'][j] <= price)):
                return False
        return True

    def target_pool(self, i, side):
        x = self.x; pk = x['pk'][i]
        liq = []
        st = []
        if side == 1:
            liq = [(v, 'EQH') for v in pk['eqh']] + [(x['pdh'][i], 'PDH'), (x['pwh'][i], 'PWH'), (x['pmh'][i], 'PMH'),
                                                     (pk['swingHigh'], '15M_SWING_HIGH'), (x['macroHigh'][i], '4H_SWING_HIGH')]
            for fam, kind in (('supply', 'SUPPLY'), ('bearOb', 'BEAR_OB'), ('bearFvg', 'BEAR_FVG'), ('pRes', 'PIVOT_RESISTANCE')):
                for z in pk[fam]:
                    st.append((None if z is None else z[1], kind))
        else:
            liq = [(v, 'EQL') for v in pk['eql']] + [(x['pdl'][i], 'PDL'), (x['pwl'][i], 'PWL'), (x['pml'][i], 'PML'),
                                                     (pk['swingLow'], '15M_SWING_LOW'), (x['macroLow'][i], '4H_SWING_LOW')]
            for fam, kind in (('demand', 'DEMAND'), ('bullOb', 'BULL_OB'), ('bullFvg', 'BULL_FVG'), ('pSup', 'PIVOT_SUPPORT')):
                for z in pk[fam]:
                    st.append((None if z is None else z[0], kind))
        liq = [(v, k) for v, k in liq if v is not None and self.liq_unswept(i, v, side)]
        st = [(v, k) for v, k in st if v is not None]
        return liq + st

    def evaluate(self, i, side, kind, entry, aoiTop, aoiBottom, impA, pool):
        c = self.c; x = self.x
        close, h, l = x['C'][i], x['H'][i], x['L'][i]
        stop = entry - c['stopDist'] if side == 1 else entry + c['stopDist']
        pending = close > entry if side == 1 else close < entry
        mean = (aoiTop + aoiBottom) / 2
        stopValid = stop <= min(mean, impA) if side == 1 else stop >= max(mean, impA)
        tg = [(p, k) for p, k in pool if ((p > entry and p > h) if side == 1 else (p < entry and p < l))]
        nearest = None
        for p, k in tg:
            d = abs(p - entry)
            if d > 0.0005 and (nearest is None or d < nearest[0]):
                nearest = (d, p, k)
        second = None
        if nearest is not None:
            for p, k in tg:
                d = abs(p - entry)
                if d > nearest[0] + 0.0005 and (second is None or d < second[0]):
                    second = (d, p, k)
        risk = c['stopDist']
        tp1R = nearest[0] / risk if nearest else None
        hasRoom = nearest is not None and tp1R >= c['minTP1R']
        hasTP2 = hasRoom and second is not None
        tp2R = second[0] / risk if hasTP2 else None
        valid = pending and stopValid and hasRoom and hasTP2
        reason = 'ENTRY_ALREADY_PASSED' if not pending else 'FIXED_SL_INSIDE_STRUCTURE' if not stopValid else \
            'NO_STRUCTURAL_TARGET' if nearest is None else 'NO_1_5R_ROOM' if not hasRoom else \
            'NO_VALID_TP2' if not hasTP2 else 'VALID_TRADE'
        return dict(valid=valid, reason=reason, kind=kind, entry=entry, stop=stop,
                    tp1=nearest[1] if nearest else None, tp1Kind=nearest[2] if nearest else 'NONE',
                    tp2=second[1] if hasTP2 else None, tp2Kind=second[2] if hasTP2 else 'NONE',
                    tp1R=tp1R, tp2R=tp2R)

    def build_package(self, i):
        """Engine 7 on a new READY. Returns (package or None, reason, info)."""
        x = self.x; c = self.c
        side = self.side
        bars = i - self.touchBar if self.touchBar is not None else None
        info = {}
        if bars is None or bars < 1 or bars > 499:
            return None, 'INVALID_IMPULSE_HISTORY', info
        A = B = None; aStep = bStep = None
        for step in range(0, bars + 1):
            j = i - (bars - step)
            o, h, l, cl = x['O'][j], x['H'][j], x['L'][j], x['C'][j]
            if side == 1:
                if A is None or l < A:
                    A = l; aStep = step
                    B = h if cl > o else None
                    bStep = step if cl > o else None
                if step > aStep and (B is None or h > B):
                    B = h; bStep = step
            else:
                if A is None or h > A:
                    A = h; aStep = step
                    B = l if cl < o else None
                    bStep = step if cl < o else None
                if step > aStep and (B is None or l < B):
                    B = l; bStep = step
        seqOk = A is not None and B is not None and bStep is not None and bStep >= aStep and ((B > A) if side == 1 else (B < A))
        if not seqOk:
            return None, 'INVALID_IMPULSE_SEQUENCE', info
        size = abs(B - A)
        atr = x['atr'][i]
        if atr is None or atr <= 0:
            return None, 'ATR_UNAVAILABLE', info
        strength = size / atr
        info.update(A=A, B=B, size=size, strength=strength)
        if strength < c['minImpulseATR']:
            return None, 'WEAK_IMPULSE', info
        pool = self.target_pool(i, side)
        evals = []
        for kind in c['entries']:
            f = {'F38.2': 0.382, 'F50': 0.5, 'F61.8': 0.618, 'F78.6': 0.786}[kind]
            e = B - f * size if side == 1 else B + f * size
            evals.append(self.evaluate(i, side, kind, e, self.lock['top'], self.lock['bottom'], A, pool))
        if 'package' in self.hooks:
            return self.hooks['package'](self, i, evals, info)
        valid = [e for e in evals if e['valid']]
        if not valid:
            return None, ' / '.join(e['reason'] for e in evals), info
        # Original rule: prefer F38.2 when its TP2R is larger (or equal with >= TP1R).
        best = valid[0]
        for e in valid[1:]:
            if e['tp2R'] > best['tp2R'] or (e['tp2R'] == best['tp2R'] and e['tp1R'] > best['tp1R']):
                best = e
        if len(valid) == 2 and c['entries'] == ('F38.2', 'F61.8'):
            e3, e6 = evals
            use382 = e3['valid'] and (not e6['valid'] or e3['tp2R'] > e6['tp2R'] or (e3['tp2R'] == e6['tp2R'] and e3['tp1R'] >= e6['tp1R']))
            best = e3 if use382 else e6
        return best, 'VALID_TRADE', info

    # ------------------------------------------------------------------- run
    def reset_lock(self):
        self.lock = None
        self.side = 0
        self.touchBar = None
        self.readyBar = None
        self.readyEvaluated = False
        self.readyAccepted = False

    def run(self):
        x = self.x; c = self.c
        self.consumed = []; self.consumedSet = set()
        self.state = 0
        self.reset_lock()
        self.lastReason = 'NONE'
        self.events = []
        self.readyLog = []
        self.trades = []
        self.funnel = dict(locks=0, retargets=0, touches=0, ready=0, valid=0, rejected={}, fills=0,
                           cancelMiss=0, cancelExp=0, cancelInv=0, busy=0)
        ex = None  # execution state dict
        for i in range(self.start, self.end):
            if x['setupTime'][i] is None or x['pk'][i]['swingHigh'] is None:
                continue
            t = x['T'][i]; o, h, l, cl = x['O'][i], x['H'][i], x['L'][i], x['C'][i]
            pk = x['pk'][i]
            # ---- candidates
            cands = []
            fams = ZONE_FAMILIES_LONG + ZONE_FAMILIES_SHORT
            for fam, anchor, mask in fams:
                side = 1 if anchor in ('DEMAND', 'BULL_OB', 'PIVOT_SUPPORT') else -1
                for z in pk[fam]:
                    cd = self.build_candidate(i, z, side, anchor, mask)
                    if cd is not None:
                        cands.append(cd)
            best = None
            for cd in cands:
                if cd['score'] < c['minScore']:
                    continue
                if best is None or cd['score'] > best['score'] or (cd['score'] == best['score'] and cd['dist'] < best['dist']) or \
                        (cd['score'] == best['score'] and cd['dist'] == best['dist'] and cd['confirmed'] > best['confirmed']):
                    best = cd
            released = False
            retargeted = False
            if self.state == 4:
                self.state = 0
                self.reset_lock()
                released = True
            if 1 <= self.state <= 3:
                L_ = self.lock
                sc = x['setupClose'][i]
                invalid = sc is not None and (sc < L_['bottom'] if self.side == 1 else sc > L_['top'])
                tgtPassed = c.get('oppGone', True) and self.state <= 2 and L_['liq'] is not None and ((h >= L_['liq']) if self.side == 1 else (l <= L_['liq']))
                lockExp = self.state == 1 and i - L_['bar'] >= c['maxLockBars']
                confExp = self.state == 2 and self.touchBar is not None and i - self.touchBar >= c['maxConfirmBars']
                rejReady = self.state == 3 and self.readyEvaluated and not self.readyAccepted
                retExp = self.state == 3 and self.readyEvaluated and self.readyAccepted and i - self.readyBar >= c['readyRetention']
                if invalid:
                    self.mark_consumed(self.side, L_['anchor'], L_['origin'])
                    self.lastReason = 'AOI_INVALIDATED'
                    self.events.append((t, 'INVALIDATED', self.side))
                    self.state = 4
                    released = True
                elif tgtPassed or lockExp or confExp or rejReady or retExp:
                    self.mark_consumed(self.side, L_['anchor'], L_['origin'])
                    self.lastReason = 'OPPORTUNITY_GONE' if tgtPassed else 'LOCK_EXPIRED' if lockExp else \
                        'CONFIRMATION_EXPIRED' if confExp else 'READY_REJECTED' if rejReady else 'READY_RETENTION_EXPIRED'
                    self.events.append((t, 'RELEASE_' + self.lastReason, self.side))
                    self.state = 0
                    self.reset_lock()
                    released = True
                elif self.state == 1 and i > L_['bar']:
                    if l <= L_['top'] and h >= L_['bottom']:
                        self.touchBar = i
                        self.state = 2
                        self.funnel['touches'] += 1
                        self.events.append((t, 'TOUCH', self.side))
            if c['retarget'] and self.state == 1 and not released and best is not None:
                L_ = self.lock
                lockedDist = max(cl - L_['top'], 0.0) if self.side == 1 else max(L_['bottom'] - cl, 0.0)
                same = best['side'] == self.side and best['anchor'] == L_['anchor'] and best['origin'] == L_['origin']
                if not same and (best['score'] > L_['score'] or (best['score'] == L_['score'] and best['dist'] < lockedDist)):
                    self.state = 0
                    retargeted = True
                    self.funnel['retargets'] += 1
            if self.state == 0 and not released and best is not None:
                self.lock = dict(best)
                self.lock['bar'] = i
                self.side = best['side']
                self.touchBar = None; self.readyBar = None
                self.readyEvaluated = False; self.readyAccepted = False
                self.lastReason = 'RETARGETED' if retargeted else 'NONE'
                self.state = 1
                if not retargeted:
                    self.funnel['locks'] += 1
                self.events.append((t, 'LOCK', self.side, best['anchor'], best['top'], best['bottom'], best['score']))
            # ---- confirmation
            newReady = False
            if self.state == 2 and i > self.touchBar:
                ev = x['ev']; s = self.side
                ich = ev['bull_ichoch'][i] if s == 1 else ev['bear_ichoch'][i]
                sch = ev['bull_choch'][i] if s == 1 else ev['bear_choch'][i]
                ibos = (not ich) and (ev['bull_ibreak'][i] if s == 1 else ev['bear_ibreak'][i])
                rea = x['bullReact'][i] if s == 1 else x['bearReact'][i]
                ct = c['confirmTypes']
                event = (ich and 'ichoch' in ct) or (ibos and 'ibos' in ct) or (sch and 'schoch' in ct) or (rea and 'react' in ct)
                if 'confirm' in self.hooks:
                    event = self.hooks['confirm'](self, i, event, dict(ich=ich, ibos=ibos, sch=sch, rea=rea))
                if event:
                    self.readyBar = i
                    self.state = 3
                    newReady = True
                    self.funnel['ready'] += 1
                    self.lock['confirm'] = ('ICHOCH ' if ich else '') + ('IBOS ' if ibos else '') + ('SCHOCH ' if sch else '') + ('REACT' if rea else '')
                    self.readyLog.append(dict(i=i, t=t, side=self.side, lock=dict(self.lock), touchBar=self.touchBar,
                                              macro=x['macroBias'][i], b1=x['bias1H'][i], atr=x['atr'][i],
                                              ich=ich, ibos=ibos, sch=sch, rea=rea))
            # ---- Engine 7
            pkg = None
            if newReady:
                pkg, reason, info = self.build_package(i)
                self.readyLog[-1].update(reason=reason, info=info, pkg=pkg)
                self.readyEvaluated = True
                self.readyAccepted = pkg is not None
                if pkg is not None:
                    self.funnel['valid'] += 1
                    pkg = dict(pkg)
                    pkg.update(side=self.side, readyBar=i, readyTime=t, aoi=(self.lock['top'], self.lock['bottom']),
                               anchor=self.lock['anchor'], score=self.lock['score'], mask=self.lock['mask'],
                               confirm=self.lock.get('confirm', ''), touchBar=self.touchBar, lockBar=self.lock['bar'], **info)
                    self.events.append((t, 'PACKAGE', self.side, pkg['kind'], pkg['entry'], pkg['stop'], pkg['tp1'], pkg['tp2']))
                else:
                    self.funnel['rejected'][reason] = self.funnel['rejected'].get(reason, 0) + 1
                    self.events.append((t, 'READY_REJECTED', self.side, reason))
            # ---- Execution lifecycle (manage first, then consume new package)
            if ex is not None and ex['state'] == 1:
                touched = l <= ex['entry'] <= h
                parentInv = self.state == 4
                expired = i - ex['pkgBar'] >= c['pendingBars']
                opp = (h >= ex['tp1']) if ex['side'] == 1 else (l <= ex['tp1'])
                if parentInv or (not touched and (expired or opp)):
                    k = 'cancelInv' if parentInv else 'cancelExp' if expired else 'cancelMiss'
                    self.funnel[k] += 1
                    ex = None
                elif touched:
                    ex['state'] = 2; ex['fillBar'] = i; ex['fillTime'] = t
                    ex['stopNow'] = ex['stop']
                    self.funnel['fills'] += 1
            if ex is not None and ex['state'] == 2:
                s = ex['side']
                onFill = i == ex['fillBar']
                stopHit = (l <= ex['stopNow']) if s == 1 else (h >= ex['stopNow'])
                tp1Hit = (not onFill) and ((h >= ex['tp1']) if s == 1 else (l <= ex['tp1']))
                tp2Hit = (not onFill) and ((h >= ex['tp2']) if s == 1 else (l <= ex['tp2']))
                if stopHit or tp2Hit:
                    if stopHit:
                        outcome = ('BE_AFTER_TP1' if c['mgmt'] == 'be' else 'STOP_AFTER_TP1') if ex['tp1Hit'] else 'STOP'
                    else:
                        outcome = 'TP2'
                        ex['tp1Hit'] = True
                    ex['exitBar'] = i; ex['exitTime'] = t; ex['outcome'] = outcome
                    self.trades.append(ex)
                    ex = None
                elif tp1Hit and not ex['tp1Hit']:
                    ex['tp1Hit'] = True; ex['tp1Bar'] = i
                    if c['mgmt'] == 'be':
                        ex['stopNow'] = ex['entry']
            if pkg is not None:
                if ex is not None:
                    self.funnel['busy'] += 1
                else:
                    ex = dict(pkg); ex['state'] = 1; ex['pkgBar'] = i; ex['tp1Hit'] = False
                    if pkg.get('market'):
                        ex['state'] = 2; ex['fillBar'] = i; ex['fillTime'] = t; ex['stopNow'] = ex['stop']
                        self.funnel['fills'] += 1
        self.open_at_end = ex
        return self


def r_multiple(tr, cfg=None, mode='partial'):
    """R for a closed trade. mode: 'partial' = 50% at TP1, rest TP2/BE/stop;
    'tp1' = full exit at TP1; 'tp2' = all-in to TP2 with the same stop rules."""
    c = dict(DEFAULT)
    if cfg:
        c.update(cfg)
    risk = abs(tr['entry'] - tr['stop'])
    cost = c['cost'] / risk
    o = tr['outcome']
    if o == 'STOP':
        return -1.0 - cost
    tp1R, tp2R = tr['tp1R'], tr['tp2R']
    if mode == 'tp1':
        return tp1R - cost
    if mode == 'partial':
        if o == 'TP2':
            return 0.5 * tp1R + 0.5 * tp2R - cost
        if o == 'BE_AFTER_TP1':
            return 0.5 * tp1R - cost
        if o == 'STOP_AFTER_TP1':
            return 0.5 * tp1R - 0.5 - cost
    if mode == 'tp2':
        if o == 'TP2':
            return tp2R - cost
        if o == 'BE_AFTER_TP1':
            return 0.0 - cost
        return -1.0 - cost
    raise ValueError(o)


def stats(trades, cfg=None, mode='partial', days=None):
    rs = [r_multiple(t, cfg, mode) for t in trades]
    n = len(rs)
    if n == 0:
        return dict(n=0)
    wins = sum(1 for t in trades if t['outcome'] != 'STOP')
    gp = sum(r for r in rs if r > 0)
    gl = -sum(r for r in rs if r < 0)
    eq = peak = dd = 0.0
    for r in rs:
        eq += r
        peak = max(peak, eq)
        dd = max(dd, peak - eq)
    out = dict(n=n, wins=wins, losses=n - wins, wr=wins / n, pf=(gp / gl) if gl > 0 else float('inf'),
               exp=sum(rs) / n, total=sum(rs), maxdd=dd,
               tp2=sum(1 for t in trades if t['outcome'] == 'TP2'))
    if days:
        out['perday'] = n / days
    return out
