from lab_events import *
fams = {
  'trend (V7.2 trigger)': ev_trend(),
  'sweep+CHoCH': ev_sweep(),
  'sweep+CHoCH 4H bias': ev_sweep(htf='4h'),
  'sweep+CHoCH killzone': ev_sweep(kz=True),
  'Asia false breakout (02-11 ET)': ev_asia_fb(),
  'FVG retrace (disp 1 ATR, 4H+1H)': ev_fvg(),
  'FVG retrace killzone': ev_fvg(kz=True),
  'NY ORB 15m (4H bias)': ev_orb(),
  'AOI touch + ibreak': ev_aoi(),
  'AOI touch + ibreak, 4H+1H': ev_aoi(htf='both'),
}
for name, E in fams.items():
    cfg = dict(entry='limit') if name.startswith('FVG') else {}
    print('events', len(E))
    backtest(E, cfg, name)
