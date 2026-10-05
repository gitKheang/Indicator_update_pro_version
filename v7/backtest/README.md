# V7 backtester (Python port)

A bar-by-bar Python port of the V7 Brain (Phase 5, Engine 6, Engine 7) and the
Execution + UI lifecycle, used to measure every change in V7.1 on a large
sample. TradingView only loads about 10,000 five-minute bars (about 50 days)
on the current plan, far too few for 100+ trades. Results and method are in
`../README.md`, Part 1.

| File | Content |
|---|---|
| `data_load.py` | Loads 1-minute XAUUSD data and builds TradingView-style bars (5m, 15m, 1H, 4H aligned to the 17:00 New York session, D, W, M) |
| `ta.py` | Pine `ta.*` equivalents (RMA ATR, swings, pivots, Heikin-Ashi) |
| `phase5.py` | Phase 5 port: 15m zones (D/S, OB, FVG, pivot S/R, EQH/EQL), 4H/1H structure, 5m structure, confirmed `[1]` alignment |
| `engine.py` | Engine 6 + Engine 7 + Execution port; the default config is the original V7 |
| `v71_rules.py` | The V7.1 rules as config + hooks |
| `run_v71.py` | Reproduces the published V7.1 figures |
| `fwd.py`, `multi.py` | Research helpers (bracket simulation, multi-AOI tracking test) |
| `fetch_hd.py`, `fetch_dukascopy.py` | Data download helpers |

## Data

1. From this folder run `python3 fetch_hd.py`. It downloads the free
   HistData.com XAUUSD M1 files (Dukascopy-sourced) into `data/hd/`: one
   yearly file for 2024, then monthly files Jan 2025 – Sep 2026. Edit the
   ranges at the top to extend it.
2. Optional: `fetch_dukascopy.py` downloads daily files into `data/raw/` for
   the days after the last HistData month. Edit its date range first; the
   feed rate-limits, so it is slow.

HistData timestamps are UTC-5, or UTC-4 while London is on summer time;
`data_load.py` converts them. This was verified against Dukascopy UTC data and
against the OANDA bars on TradingView (closes differ by about $0.3, a feed
offset).

Then run `python3 run_v71.py`. The first run builds and caches `data/ctx.pkl`.
Keep `data/` out of version control.

## Port fidelity

On 9 Aug – 4 Oct 2026 the port and TradingView produced the same funnel within
about 5% (old V7) and the same trade count and win/loss split (V7.1: 36 trades
each, 20/16 vs 18/18). About three quarters of the individual trades are
identical; the rest differ because OANDA and Dukascopy prices differ slightly
and SMC swing detection is sensitive to that. Use the port for statistics,
not for reproducing a single chart trade.

## V7.2 research files

| File | Content |
|---|---|
| `simple_engine.py` | V7.2 engine: 4H+1H-aligned 5m internal break, protected-swing stop (≤ $15), TP1 1.51R with clean room, TP2 2.5R or before the next opposing zone, no break-even |
| `v72_final.py` | The V7.2 default config (`V72`) and the trades in the TradingView window |
| `v72_report.py` | Reproduces the V7.2 comparison tables in `../README.md` |
| `r2_common.py` | Old AOI pipeline under the new SL/TP rules (baseline) |
| `zone_study.py`, `htf_zone_study.py` | First-touch hold rate of every 15m / 1H / 4H zone |
| `sig_search.py`, `feat3.py` | Signal-family and feature studies at 1.5R |
| `render.py` | Draws review charts: zones (held/failed at first touch) and trades |

## V7.3 research files

| File | Content |
|---|---|
| `v72_final.py` | Configs `V72` and **`V73`** (maintained: clean-room obstacles = Pivot S/R + EQH/EQL + 4H swing) |
| `v73_report.py` | Reproduces the V7.3 tables in `../README.md` |
| `lab.py`, `lab_events.py` | Shared constructor (structural SL, liquidity/structure target pool, no break-even) and the researched setup families (sweep+CHoCH, Asia false breakout, FVG retrace, NY ORB, AOI touch, trend) |
| `lab1.py` … `lab3.py`, `v72_iter*.py` | The iteration experiments listed in the iteration log |
| `ml_dataset.py`, `ml_ceiling.py` | Statistical ceiling test (needs numpy + scikit-learn; run with a separate venv) |
