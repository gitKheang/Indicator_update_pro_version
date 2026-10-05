"""Research variant: Engine 6 tracking up to K AOIs at once (untouched slots
are the top-K eligible candidates; touched slots are frozen until READY or
release). Execution still runs one trade at a time."""
from engine import Engine, ZONE_FAMILIES_LONG, ZONE_FAMILIES_SHORT


class MultiEngine(Engine):
    def run(self):
        x = self.x; c = self.c
        K = c.get('slots', 3)
        self.consumed = []; self.consumedSet = set()
        self.trades = []; self.readyLog = []; self.events = []
        self.funnel = dict(locks=0, touches=0, ready=0, valid=0, rejected={}, fills=0, busy=0)
        slots = []
        ex = None
        ident = lambda d: (d['side'], d['anchor'], d['origin'])
        for i in range(self.start, self.end):
            if x['setupTime'][i] is None or x['pk'][i]['swingHigh'] is None:
                continue
            t = x['T'][i]; h, l = x['H'][i], x['L'][i]
            pk = x['pk'][i]
            cands = []
            for fam, anchor, mask in ZONE_FAMILIES_LONG + ZONE_FAMILIES_SHORT:
                side = 1 if anchor in ('DEMAND', 'BULL_OB', 'PIVOT_SUPPORT') else -1
                for z in pk[fam]:
                    cd = self.build_candidate(i, z, side, anchor, mask)
                    if cd is not None and cd['score'] >= c['minScore']:
                        cands.append(cd)
            # 1) lifecycle of existing slots
            keep = []
            for s in slots:
                sc = x['setupClose'][i]
                inv = sc is not None and (sc < s['bottom'] if s['side'] == 1 else sc > s['top'])
                tgt = s['liq'] is not None and ((h >= s['liq']) if s['side'] == 1 else (l <= s['liq']))
                lexp = s['st'] == 1 and i - s['bar'] >= c['maxLockBars']
                cexp = s['st'] == 2 and i - s['touchBar'] >= c['maxConfirmBars']
                if inv or tgt or lexp or cexp:
                    self.mark_consumed(s['side'], s['anchor'], s['origin'])
                    continue
                if s['st'] == 1 and i > s['bar'] and l <= s['top'] and h >= s['bottom']:
                    s['st'] = 2; s['touchBar'] = i
                    self.funnel['touches'] += 1
                keep.append(s)
            slots = keep
            # 2) refill untouched slots with the top eligible candidates
            touched = [s for s in slots if s['st'] == 2]
            untouched = {ident(s): s for s in slots if s['st'] == 1}
            taken = {ident(s) for s in touched}
            cands.sort(key=lambda d: (-d['score'], d['dist'], -d['confirmed']))
            newU = []
            for cd in cands:
                if len(touched) + len(newU) >= K:
                    break
                k = ident(cd)
                if k in taken:
                    continue
                taken.add(k)
                if k in untouched:
                    newU.append(untouched[k])
                else:
                    d = dict(cd); d['st'] = 1; d['bar'] = i; d['touchBar'] = None
                    newU.append(d)
                    self.funnel['locks'] += 1
            slots = touched + newU
            # 3) confirmation for touched slots
            pkg = None
            for s in list(slots):
                if s['st'] != 2 or i <= s['touchBar']:
                    continue
                ev = x['ev']; sd = s['side']
                ich = ev['bull_ichoch'][i] if sd == 1 else ev['bear_ichoch'][i]
                sch = ev['bull_choch'][i] if sd == 1 else ev['bear_choch'][i]
                ibos = (not ich) and (ev['bull_ibreak'][i] if sd == 1 else ev['bear_ibreak'][i])
                rea = x['bullReact'][i] if sd == 1 else x['bearReact'][i]
                ct = c['confirmTypes']
                event = (ich and 'ichoch' in ct) or (ibos and 'ibos' in ct) or (sch and 'schoch' in ct) or (rea and 'react' in ct)
                self.lock = s; self.side = sd; self.touchBar = s['touchBar']
                if 'confirm' in self.hooks:
                    event = self.hooks['confirm'](self, i, event, dict(ich=ich, ibos=ibos, sch=sch, rea=rea))
                if not event:
                    continue
                self.funnel['ready'] += 1
                p, reason, info = self.build_package(i)
                self.mark_consumed(sd, s['anchor'], s['origin'])
                slots.remove(s)
                if p is not None and pkg is None:
                    pkg = dict(p)
                    pkg.update(side=sd, readyBar=i, readyTime=t, aoi=(s['top'], s['bottom']), anchor=s['anchor'],
                               score=s['score'], touchBar=s['touchBar'], lockBar=s['bar'], **info)
                    self.funnel['valid'] += 1
            # 4) execution (market packages only)
            if ex is not None:
                sd = ex['side']
                stopHit = (l <= ex['stopNow']) if sd == 1 else (h >= ex['stopNow'])
                tp1Hit = (h >= ex['tp1']) if sd == 1 else (l <= ex['tp1'])
                tp2Hit = (h >= ex['tp2']) if sd == 1 else (l <= ex['tp2'])
                if stopHit or tp2Hit:
                    ex['outcome'] = ('BE_AFTER_TP1' if c['mgmt'] == 'be' else 'STOP_AFTER_TP1') if (stopHit and ex['tp1Hit']) else 'STOP' if stopHit else 'TP2'
                    if not stopHit:
                        ex['tp1Hit'] = True
                    ex['exitBar'] = i
                    self.trades.append(ex)
                    ex = None
                elif tp1Hit and not ex['tp1Hit']:
                    ex['tp1Hit'] = True
                    if c['mgmt'] == 'be':
                        ex['stopNow'] = ex['entry']
            if pkg is not None:
                if ex is not None:
                    self.funnel['busy'] += 1
                else:
                    ex = dict(pkg); ex['state'] = 2; ex['fillBar'] = i; ex['stopNow'] = ex['stop']; ex['tp1Hit'] = False
                    self.funnel['fills'] += 1
        return self
