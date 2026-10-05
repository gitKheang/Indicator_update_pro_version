"""Research helpers for the V7.2 task: structure SL (<= $15), structural TP1 > 1.5R,
TP2 > TP1, no break-even (50% at TP1, runner keeps the original stop)."""
import datetime, collections
from run_v71 import context
from engine import Engine, stats, r_multiple
UTC = datetime.timezone.utc
ctx = context()
T = ctx['T']
SPLIT = int(datetime.datetime(2025, 7, 1, tzinfo=UTC).timestamp() * 1000)
TWO_Y = int(datetime.datetime(2024, 10, 1, tzinfo=UTC).timestamp() * 1000)
DAYS_ALL = (T[-1] - T[0]) / 86400000 * 5 / 7
DAYS_2Y = (T[-1] - TWO_Y) / 86400000 * 5 / 7
BASE = dict(minScore=50.0, maxConfirmBars=36, confirmTypes=('ichoch', 'ibos', 'schoch'), readyRetention=1, mgmt='orig', cost=0.3)


def structural_hook(buf_atr=0.5, max_sl=15.0, min_sl=0.0, min_tp1_r=1.5, clean_room=False, sl_mode='aoi_or_A',
                    entry_mode='close', body_conf=None):
    def hook(eng, i, evals, info):
        x = eng.x; s = eng.side; a = x['atr'][i]
        A = info.get('A')
        if A is None or a is None:
            return None, 'INVALID', info
        L = eng.lock
        far = L['bottom'] if s == 1 else L['top']
        if sl_mode == 'aoi_or_A':
            inval = min(far, A) if s == 1 else max(far, A)
        elif sl_mode == 'A':
            inval = A
        else:
            inval = far
        entry = x['C'][i]
        stop = inval - buf_atr * a if s == 1 else inval + buf_atr * a
        risk = (entry - stop) * s
        if risk <= 0:
            return None, 'BAD_STOP', info
        if risk > max_sl:
            return None, 'SL_TOO_WIDE', info
        if risk < min_sl:
            return None, 'SL_TOO_TIGHT', info
        pool = eng.target_pool(i, s)
        h, l = x['H'][i], x['L'][i]
        lv = sorted(set(round(p, 3) for p, k in pool if ((p > entry and p > h) if s == 1 else (p < entry and p < l))), key=lambda p: abs(p - entry))
        if not lv:
            return None, 'NO_TARGET', info
        if clean_room and abs(lv[0] - entry) <= min_tp1_r * risk:
            return None, 'NO_ROOM', info
        beyond = [p for p in lv if abs(p - entry) > min_tp1_r * risk]
        if len(beyond) < 2:
            return None, 'NO_TP1_TP2', info
        tp1, tp2 = beyond[0], beyond[1]
        pkg = dict(valid=True, reason='VALID_TRADE', kind='CLOSE', entry=entry, stop=stop, tp1=tp1, tp2=tp2,
                   tp1Kind='S', tp2Kind='S', tp1R=abs(tp1 - entry) / risk, tp2R=abs(tp2 - entry) / risk, market=True)
        return pkg, 'VALID_TRADE', info
    return hook


def body_confirm(th):
    def f(eng, i, event, flags):
        if not event:
            return False
        x = eng.x; a = x['atr'][i]
        return a is not None and (x['C'][i] - x['O'][i]) * eng.side >= th * a
    return f


def report(e, cfg, label):
    tr = e.trades
    def row(sel, days=None):
        s = stats(sel, cfg, 'partial', days)
        if not s['n']:
            return 'n=0'
        mcl = cur = 0
        for t in sel:
            cur = cur + 1 if t['outcome'] == 'STOP' else 0
            mcl = max(mcl, cur)
        return 'n=%3d %s WR %4.1f%% PF %.2f exp %+.3f net %+6.1fR DD %4.1f MCL %d' % (
            s['n'], ('%.2f/d' % s['perday']) if days else '', 100 * s['wr'], s['pf'], s['exp'], s['total'], s['maxdd'], mcl)
    print('%-36s ALL  %s' % (label, row(tr, DAYS_ALL)))
    print('%-36s 2Y   %s' % ('', row([t for t in tr if t['readyTime'] >= TWO_Y], DAYS_2Y)))
    print('%-36s IS   %s' % ('', row([t for t in tr if t['readyTime'] < SPLIT])))
    print('%-36s OOS  %s' % ('', row([t for t in tr if t['readyTime'] >= SPLIT])))


def run(hook, cfg=None, confirm=None, label=''):
    c = dict(BASE); c.update(cfg or {})
    hooks = {'package': hook}
    if confirm:
        hooks['confirm'] = confirm
    e = Engine(ctx, c, hooks=hooks).run()
    report(e, c, label)
    return e
