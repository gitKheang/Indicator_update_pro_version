from lab_events import *
E = ev_trend()
backtest(E, dict(), 'A struct TP1/TP2 (baseline)')
for fr in (0.0, 0.2, 0.4):
    backtest(E, dict(tp_front=fr), 'A front-run %.1f ATR' % fr)
backtest(E, dict(tp_mode='hybrid', hyb_tp1=1.51), 'B hybrid: TP1 1.51R partial, TP2 = first real level beyond')
backtest(E, dict(tp_mode='hybrid', hyb_tp1=1.51, clean='zones'), 'B + clean room zones')
backtest(E, dict(tp_mode='hybrid', hyb_tp1=1.51, clean='zones', hyb_max=4.0), 'B + clean room, TP2 <= 4R')
backtest(E, dict(tp_mode='hybrid', hyb_tp1=1.51, clean='zones', tp_kinds='liq'), 'B + clean room, TP2 liquidity only')
L_ = [e for e in E if e[1] == 1]; S_ = [e for e in E if e[1] == -1]
backtest(L_, dict(tp_mode='hybrid', hyb_tp1=1.51, clean='zones'), 'B+clean, LONGS only')
backtest(S_, dict(tp_mode='hybrid', hyb_tp1=1.51, clean='zones'), 'B+clean, SHORTS only')
# daily trend filter: trade only in the direction of (close - day open)
Ed = [e for e in E if DAY_OPEN[e[0]] and (C[e[0]] - DAY_OPEN[e[0]]) * e[1] > 0]
backtest(Ed, dict(tp_mode='hybrid', hyb_tp1=1.51, clean='zones'), 'B+clean, with intraday direction (vs day open)')
