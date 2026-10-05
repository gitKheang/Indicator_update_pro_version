"""V7.1 rules on top of the V7 port in engine.py.

engine.Engine with its DEFAULT config reproduces the original V7 (F38.2/F61.8
limit entries, fixed $10 stop, TP1 >= 1.5R to structure). V71_CONFIG plus
v71_hooks() reproduce the maintained Pine scripts:

  Engine 6: minimum score 50, confirmation window 36 bars, structure-break
            confirmation only (internal CHoCH / internal BOS / swing CHoCH) with
            a displacement body >= 0.3 x ATR(89); READY released on the next bar.
  Engine 7: entry at the READY close; stop = A -/+ 0.5 x ATR(89), capped at
            4 x ATR(89) from entry; TP1 = 1R, TP2 = 2.5R.
  Execution: 50% at TP1, stop to entry, rest to TP2; stop-first on ambiguous bars.
"""

V71_CONFIG = dict(
    minScore=50.0,
    maxConfirmBars=36,
    confirmTypes=('ichoch', 'ibos', 'schoch'),
    readyRetention=1,
    mgmt='be',
    cost=0.3,          # $ per round trip (spread/slippage), charged in R
)


def package_hook(stop_buffer_atr=0.5, max_stop_atr=4.0, tp1_r=1.0, tp2_r=2.5):
    def hook(eng, i, evals, info):
        x = eng.x
        s = eng.side
        A = info.get('A'); a = x['atr'][i]
        if A is None or a is None:
            return None, 'INVALID_RISK', info
        c = x['C'][i]
        raw = (c - (A - stop_buffer_atr * a)) if s == 1 else ((A + stop_buffer_atr * a) - c)
        risk = min(raw, max_stop_atr * a)
        if risk <= 0.001:
            return None, 'INVALID_RISK', info
        pkg = dict(valid=True, reason='VALID_TRADE', kind='READY_CLOSE', entry=c, stop=c - s * risk,
                   tp1=c + s * tp1_r * risk, tp2=c + s * tp2_r * risk, tp1Kind='R', tp2Kind='R',
                   tp1R=tp1_r, tp2R=tp2_r, market=True)
        return pkg, 'VALID_TRADE', info
    return hook


def confirm_hook(min_body_atr=0.3):
    def hook(eng, i, event, flags):
        if not event:
            return False
        x = eng.x
        a = x['atr'][i]
        return a is not None and (x['C'][i] - x['O'][i]) * eng.side >= min_body_atr * a
    return hook


def v71_hooks(**kw):
    body = kw.pop('min_body_atr', 0.3)
    return {'package': package_hook(**kw), 'confirm': confirm_hook(body)}
