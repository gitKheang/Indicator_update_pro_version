from lab import *
import time
t0 = time.time()
E = ev_trend()
print('trend events', len(E), round(time.time() - t0, 1), 's')
# Baseline under the new target rule: TP1 = first real level beyond 1.5R, TP2 = next level
backtest(E, dict(), 'trend 4H+1H, TP1/TP2 = liquidity+zone levels, no clean room')
backtest(E, dict(clean='zones'), '  + clean room (opposing zones)')
backtest(E, dict(tp_kinds='liq'), '  TP from liquidity only (no zones)')
backtest(E, dict(tp_kinds='liq', clean='zones'), '  TP liquidity only + clean room zones')
backtest(E, dict(max_tp1_r=2.0), '  TP1 must be <= 2.0R')
backtest(E, dict(max_sl=999), '  no $15 cap')
