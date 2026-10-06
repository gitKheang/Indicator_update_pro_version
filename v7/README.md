# v7 — XAUUSD Smart Trade V7.8

Indicator system for XAUUSD on the 5-minute chart (TradingView, Pine Script v5).

## Files

| File | Name on TradingView | What it does |
|---|---|---|
| `1 Brain - Signal Engine.pine` | XAUUSD Smart Trade — 1. Signal Engine (Brain) | Decides every trade (details below). Sends the trade to the Trade Manager through ten hidden `BRIDGE_*` plots, and shows a status table and the decision levels on the chart |
| `2 Execution - Trade Manager.pine` | XAUUSD Smart Trade — 2. Trade Manager (Execution) | Runs each trade with your win/loss rule (details below). Draws entry/SL/TP lines and result labels, and keeps the scoreboard and alerts |
| `3 Strategy Tester.pine` | XAUUSD Smart Trade — 3. Strategy Tester | The Signal Engine logic as a `strategy()` for TradingView's Strategy Tester: same rules, fixed $ risk per trade, costs included. Needs no link to another indicator |
| `4 Chart Overlay - SMC ICT.pine` | XAUUSD Smart Trade — 4. Chart Overlay (SMC & ICT) | Visual reference only: SMC structure, order blocks, FVGs, EQH/EQL, premium/discount, supply/demand, pivots, candle patterns and the nine-indicator direction panel. No trade decision uses it |
| `README.md` | — | This file: rules, results, research, deployment notes and history |
| `backtest/` | — | Python port of the system and the research scripts. Price data is downloaded locally and not stored in git |

- **1. Signal Engine decides every trade:**
  - **Trend:** 4H + 1H trend must agree.
  - **Trigger:** 5m structure break with the 5m Supertrend agreeing. Since V7.8 the Ichimoku Tenkan/Kijun, RSI(14) cap, fast-pullback and calm-1H filters are inputs that are OFF by default (chosen for profit, not win rate).
  - **Stop:** structural, at most $15.
  - **Targets:** TP1 at 1.51R with clean room, TP2 beyond it.
- **2. Trade Manager runs each trade:**
  - Entry at the trigger close.
  - 50% closes at TP1, which makes the trade a WIN.
  - The runner goes for TP2 with the original stop (no break-even).
  - The trade is a LOSS only if the SL comes first.

**Setup on a 5-minute XAUUSD chart:**
1. Add **1. Signal Engine**.
2. Add **2. Trade Manager** and map its ten *Brain Bridge* inputs, in order,
   to the Signal Engine's `BRIDGE_*` plots.
3. Optionally, add **4. Chart Overlay** for the visual drawings.
4. To see the Strategy Tester, add **3. Strategy Tester** on its own.

Your Essential plan allows one indicator-on-indicator link per chart layout,
and the link from 2 to 1 uses it.

**Renamed on 5 October 2026.** Part 2 keeps the names used at the time:

| Old name in Part 2 | Current name |
|---|---|
| Brain | 1. Signal Engine |
| Execution + UI | 2. Trade Manager |
| V7.5 Strategy Test | 3. Strategy Tester |
| Visual Reference | 4. Chart Overlay |
| `SPLIT_REPLAY_MEMORY.md` | this `README.md` |

This file has two parts:

1. **Current system: V7.8** (below): V7.6 with three filters switched off,
   chosen for profit. The V7.6 sections that follow it still describe the
   engine, the data and the research. Read this first.
2. **Change history.** V7.5, V7.4, V7.3, V7.2, V7.1, the earlier logic review, and the split,
   memory, bridge and lifecycle repairs. Anything there that conflicts with
   Part 1 is superseded.

---

## Part 1 — Current system: V7.8 (6 October 2026)

### V7.8: chosen for profit, not win rate

You asked which tested rule set makes the most money if the win rate does not
matter, and chose the recommended one. V7.8 is V7.6 with three filters
switched **off** by default:

- the fast-pullback filter (break at most 11 bars after the broken pivot);
- Ichimoku Tenkan/Kijun agreement;
- the RSI(14) overextension cap.

They remain inputs in *Engine 6 — Trigger*. Everything else is unchanged: 4H +
1H trend, 5m structure break with Supertrend, structural SL ≤ $15, clean room,
TP1 1.51R, TP2 > TP1, 50% at TP1, no break-even. The Trade Manager is
unchanged.

**Every tested rule set, net profit** (repaired data, $0.30/oz costs, one
trade at a time, 1R risk per trade):

| Rule set | Older 2.25 years (Jan 2024 – Apr 2026) | Latest 6 months | Full 2.75 years | Trades / win rate / max drawdown (full) |
|---|---|---|---|---|
| V7.3-style (no Supertrend, fast or chop filter) | +116.0R | +29.7R | +145.7R | 557 / 50.4% / 13.5R |
| V7.6 without Ichimoku/RSI | +116.5R | +26.9R | +143.4R | 332 / 56.3% / 10.2R |
| **V7.8 (no fast-pullback, no Ichimoku/RSI)** | **+116.3R** | **+27.0R** | **+143.3R** | **417 / 53.0% / 8.5R** |
| V7.5 (calm-1H filter) | +110.7R | +13.5R | +124.2R | 241 / 59.8% / 8.0R |
| 1H trend only | +101.6R | +19.8R | +121.4R | 611 / 47.8% / 11.2R |
| V7.6 | +86.3R | +28.3R | +114.5R | 250 / 58.4% / 8.3R |
| No clean room | +93.8R | +18.9R | +112.7R | 789 / 45.2% / 39.2R |
| No higher-timeframe trend | +27.9R | +11.1R | +39.0R | 1,047 / 42.1% / 26.2R |

- **Why V7.8:** practically tied for the most profit, the smallest drawdown
  of the top three, near the top in both periods, and fewer filters tuned on
  the latest 6 months.
- **Break-even After TP1** adds 2–4R in the latest 6 months but costs 6–21R
  on the older history, so it stays off.

**V7.8 backtest, Jan 2024 – Oct 2026** (`backtest/v78_report.py`):

| Period | Trades | Win rate | Net | PF | Max drawdown |
|---|---|---|---|---|---|
| 2024 | 158 | 49.4% | +38.9R | 1.46 | 7.4R |
| 2025 | 190 | 51.6% | +61.3R | 1.64 | 6.7R |
| 2026 (to 4 Oct) | 69 | 65.2% | +43.1R | 2.75 | 5.5R |
| **All** | **417** | **53.0%** | **+143.3R** | **1.70** | **8.5R** |

- Outcomes: 177 TP2, 44 TP1 then stop, 196 SL. Longest losing streak: 7.
- Largest stop $14.92, median $7.62.
- Losing months: 4 of 31. The worst was −3.3R (November 2024).
- About $14,300 over the 2.75 years at $100 risk per trade.
- No trades from 5 September to 4 October 2026: the 4H and 1H trends
  disagreed the whole time.

**TradingView Strategy Tester** (OANDA, 9 Aug – 5 Oct 2026, the history your
plan loads):

| | V7.6 | **V7.8** |
|---|---|---|
| Trades | 7 | **11** |
| Wins / losses | 5 / 2 | **7 / 4** |
| Win rate | 71.4% | **63.6%** |
| Net R | +5.95R | **+6.21R** |
| Net profit at $100 risk (after costs) | $573 | **$587** |
| Profit factor ($) | 3.24 | **2.14** |
| Max drawdown ($) | — | **$296** |

- The Trade Manager shows the same 7 / 4, +6.21R.
- The Python backtest has 9 of these trades (7 W / 2 L, +7.8R). The two
  extra TradingView losers are borderline setups decided by small OANDA price
  differences, as found in V7.6.

**Deployment (6 October 2026):**

- **Versions:** Signal Engine v16, Strategy Tester v8. The Trade Manager (v14)
  and Chart Overlay (v5) are unchanged.
- **Inputs:** the three filters read OFF on both chart instances.
- **Link:** "All 10 sources connected".
- **Layout:** saved as you had it (5m, your manual price range, your 5
  drawings).

**Fingerprints:**

- `1 Brain - Signal Engine.pine`: SHA-256 `f79745b52ebf815d403eb9697cf215920fbf563619922236f408a647b0c22c42` (TradingView v16)
- `3 Strategy Tester.pine`: SHA-256 `59b7741eaef87bcf3eb95beaff68f40a471c1a6fd3c03309dda257573e0a5e40` (TradingView v8)
- `2 Execution - Trade Manager.pine`: unchanged from V7.6 (`d5d9d9de…`, TradingView v14)


### Your rules and targets (latest request)

- SL structure-based, at most **$15**; TP1 **> 1.5R**; TP2 **> TP1**; otherwise
  **NO TRADE**. No break-even: TP1 or TP2 = WIN, SL before TP1 = LOSS.
- Test and tune on the **latest 6 months only**, on data that is verified.
- Target: **at least 200 trades in those 6 months, at about 85% win rate**,
  with logic that survives in the market (not curve-fitted).

### Bottom line

**The target (≥ 200 trades and ~85% in 6 months) was not reached, and nothing
tested comes close.** The table shows the best result found at each trade
count. Every row uses your SL/TP rules, the repaired data and the latest 6
months: 5 April – 4 October 2026, 130 trading days. Tuning used April–July;
August–October was held out.

| Trades in 6 months | Best rule set found | Win rate |
|---|---|---|
| **32** | **V7.6 (shipped)** | **81.2%** (Apr–Jul 76.9%, Aug–Oct 6 of 6) |
| 40 | V7.6 without the Ichimoku/RSI filters | 72.5% |
| 66 | V7.3-style (no Supertrend, chop or fast filter) | 60.6% |
| 110 | Clean room off, no chop or fast filter | 50.0% |
| ~200–300 | Best famous-indicator systems with the trend filter (Hull turn, EMA20 pullback) | 44–45% |
| ~300 | V7 trend stack with a 1-minute trigger | 41.9% |
| ~1.5/day | Machine-learning pick from 49 features, on unseen Aug–Oct data | 48–52% |

- **Why it can't be reached:**
  - A trade wins only if price moves 1.5× the stop distance in your favour
    before it touches the stop. A random entry does that about 40% of the
    time.
  - Every extra trade comes from a weaker setup.
  - The oracle test showed that even perfect knowledge of the next hour's
    direction reaches only ~72% with these stops and targets.
- **V7.6's 81% depends on the regime.** The same rules won **55.0%** on the
  older data (Jan 2024 – Apr 2026, 218 trades), where V7.5 won 58.5%. Expect
  live results between those levels, depending on whether the market behaves
  like 2026 (strong, clean trends) or like 2024–25.

### Break-even was tested and removed (6 October 2026)

You asked for break-even logic with the TP1/TP2 rules unchanged. It was built
(Off / After TP1 / Before TP1 at +R), deployed, measured, and then **removed**
because it does not improve the system. The Trade Manager and Strategy Tester
are back to the V7.6 code above (same fingerprints); research scripts stay in
`backtest/v77_*.py`.

V7.6 signals, latest 6 months (W = wins, L = losses, BE = stopped at entry):

| Break-even | Trades | W / L / BE | W/(W+L) | Net |
|---|---|---|---|---|
| **Off (kept)** | 32 | 26 / 6 / 0 | 81.2% | +28.3R |
| After TP1 | 32 | 26 / 6 / 0 | 81.2% | +30.3R |
| +0.3R | 38 | 12 / 4 / 22 | 75.0% | +14.5R |
| +0.5R | 36 | 16 / 5 / 15 | 76.2% | +19.0R |
| +0.75R | 33 | 21 / 4 / 8 | 84.0% | +25.1R |
| +1.0R | 33 | 24 / 5 / 4 | 82.8% | +28.5R |

- **Only +0.75R raises the win rate (+2.8 points)**, and it lowers net profit.
  Of its 8 BE trades, 6 would have reached TP1 without it and 2 would have lost.
- **Older history (Jan 2024 – Apr 2026):** Off 55.0%, +86R; +0.75R 53.7%, +46R;
  After TP1 55.1%, +80R. Break-even lowered profit in every setting.
- **Other triggers** (Supertrend, Chandelier Exit, higher low past entry): 79–81%.
- **Last month (5 Sep – 4 Oct), the test after training:** V7.6 made 0 trades.
  The 4H structure stayed bullish while the 1H turned bearish on 2 September.
  Faster trend filters (4H/1H Supertrend, 4H EMA50, 1H only) trade that month
  at 25–57%, and mean-reversion entries for range regimes (Bollinger, RSI,
  Stochastic RSI, pivot bounce) win 38–43%. None was adopted
  (`v77_htf.py`, `v77_range.py`).
- **Still not reached:** 200+ trades at 85%.

### V7.6 results (latest 6 months)

| | V7.5 (as deployed) | **V7.6** |
|---|---|---|
| Trades (per day) | 24 (0.18) | **32 (0.25)** |
| Wins / losses | 17 / 7 | **26 / 6** |
| Win rate (Apr–Jul / Aug–Oct) | 70.8% (66.7% / 3 of 3) | **81.2% (76.9% / 6 of 6)** |
| PF / net / expectancy | 2.87 / +13.5R / +0.56R | **5.59 / +28.3R / +0.88R** |
| Max drawdown / longest losing streak | 2.1R / 2 | **1.0R / 1** |
| Outcomes | 10 TP2, 7 TP1 then stop, 7 SL | 17 TP2, 9 TP1 then stop, 6 SL |
| Older data (Jan 2024 – Apr 2026) | 217 trades, 58.5%, PF 2.17 | 218 trades, 55.0%, PF 1.83 |

- **Checks on every V7.6 trade:**
  - The largest stop was $14.70 (median $10.60).
  - Every TP1 is 1.51R and every TP2 is beyond TP1.
- **Direction by period:** April–July were all shorts (gold fell from 4,600
  to 3,960); August were longs.
- **On TradingView's own OANDA data** (9 Aug – 5 Oct, the history your plan
  loads), the Strategy Tester and the Trade Manager both show **7 trades,
  5 W / 2 L (71.4%), +5.95R**, $573 net at $100 risk, PF 3.24.

### Data: verified and repaired

The backtest data is HistData M1, which is sourced from Dukascopy.

1. **Duplicated minutes.** HistData's June–September 2026 files contain
   **774 duplicated minutes**: the same minute twice, with different prices.
   - The loader merges them in file order: open of the first row, high/low
     over both, close of the last row.
   - The rule was checked against the Dukascopy original (28 Jun 2026).
2. **A missing day.** **Friday 25 September 2026 was missing** (1,260
   minutes). It was downloaded from Dukascopy and filled in.
3. **Illiquid minutes removed.** OANDA does not quote the last minute before
   the 17:00 New York close or the first four minutes after the 18:00
   reopen, while the Dukascopy bid prints $5–17 spread spikes there. Those
   minutes are dropped.
4. **Check against TradingView's OANDA 5m bars** (9 Aug – 2 Oct 2026, 11,034
   bars):
   - Every bar is present.
   - Time alignment is exact: the median close difference is $0.33 at zero
     shift and $1.86 at ±1 bar.
   - Our bid sits $0.35 below OANDA.
   - 99% of highs are within $0.96 and 99% of lows within $1.27.
   - The shorter sessions on 25 May, 19 Jun, 3 Jul and 7 Sep are real US
     holidays.

`backtest/data_check.py` reruns the comparison. `backtest/data/tv_oanda_5m.csv`
holds the TradingView bars.

### The external audit, claim by claim

| Claim | Verified | Action | Effect (latest 6 months) |
|---|---|---|---|
| 4H swing treated as "unswept" after being traded through | **Real** (wrong label) | Kept as an obstacle, definition corrected: resting liquidity if untouched, flipped S/R if traded through | Treating traded-through levels as clear added 2 trades, both losses (71.8% → 68.3%) |
| Protected extreme includes the broken pivot candle | **Real** | **Fixed**: starts the bar after the pivot (input, ON) | +1 trade (a win); older data −1.2 points |
| $2 minimum stop | Real rule | Kept | No trade in 6 months was rejected by it |
| Pivot freshness tracked but ignored | Real | Kept all pivot zones as obstacles | Fresh-only: 71 trades at 57.7% (vs 42 at 69%) |
| 4H/1H bias very slow | True by design | Kept | Faster readings tested worse on 2.75 years (V7.5 notes) |
| Order Block not "professional" | LuxAlgo's definition, display only | Unchanged | No trading effect |
| Chart Overlay zones differ from the Brain | True, the overlay is third-party display | The Brain draws its own decision levels | — |
| TP1 not structural | True by design (1.51R + structural veto) | Kept | Structural TP1 tested at 38% (V7.2) |
| One position at a time | True | Kept | Overlapping trades add volume at lower win rate |
| Strategy Tester parity unverified | Checked by diff | — | Only header, declaration, two display defaults and the order block differ |

### What was tested this round (latest 6 months only)

1. **Famous free indicators as complete systems**, each under your SL/TP
   rules (`backtest/v76_families.py`). These were Supertrend flip, UT Bot,
   Range Filter, Donchian breakout, EMA 9/21 cross, Squeeze Momentum, Connors
   RSI(2), Bollinger re-entry, EMA20 pullback and Hull turn.
   - **Without a trend filter:** 37–42%.
   - **With the 4H+1H trend filter:** 34–50%. The best was Bollinger re-entry
     at 50% on 148 trades, but only 41.5% in August–October.
2. **Famous indicators as filters on V7.6** (`v76_famous.py`). Ichimoku
   Tenkan/Kijun (+4.6 points) and RSI(14) not overextended (+3.2 points) were
   the only consistent gains, and they were adopted. Stacking more filters
   peaked at about 81% on fewer trades.
3. **1-minute triggers under the V7 trend stack** (`v76_m1.py`): 301 trades
   at 41.9%. The 5m edge does not carry over to 1m structure.
4. **Machine-learning ceiling** (`v76_ml.py`): out-of-sample AUC 0.58–0.65.
   At 1.54 trades/day (the 200-trade rate) it picks 48–52% winners.
5. **Feature scan** (`v76_features.py`): tight structure (impulse < 2 ATR)
   and fast pullbacks help, but they overlap with the adopted filters.

### How V7.6 works

```
Trend    : 4H AND 1H major structure (50-bar LuxAlgo swings) agree
Trigger  : 5m internal BOS/CHoCH in that direction AND
           5m Supertrend(10, 3) agrees AND
           Ichimoku Tenkan(9) vs Kijun(26) agrees (5m)                 <- V7.6
           RSI(14) < 70 for longs / > 30 for shorts                    <- V7.6
           break <= 11 bars after the broken internal pivot
           [optional] 1H Choppiness(14) < 50 (OFF by default)          <- V7.6
Stop     : pullback extreme from the bar AFTER the broken pivot        <- V7.6
           +/- 0.3 x ATR(89); NO TRADE if > $15 (or < $2)
TP1      : 1.51R, only if no obstacle before it (15m pivot S/R zones,
           unswept 15m EQH/EQL, 4H swing level)
TP2      : 2.5R, or 0.1 ATR before the next obstacle; must exceed TP1 + 0.25R
Execution: 50% at TP1 = WIN; runner keeps the original SL (no break-even)
```

- **New inputs** (group *Engine 6 — Trigger*):
  - *Require Ichimoku Tenkan/Kijun agreement* (ON);
  - *Skip overextended entries (RSI 14)* (ON, 70/30);
  - *Require calm 1H* (now OFF).
- **Group *Engine 7 — Construction*:** *Protected extreme starts after the
  broken pivot* (ON).
- **New table row:** "Ichimoku TK / RSI(14)". "Trade side allowed now" also
  reports "none (Ichimoku/RSI against)".
- **Script names** on TradingView no longer carry a version: "XAUUSD Smart
  Trade — 1. Signal Engine (Brain)" and so on. The version is in each table
  header.

### TradingView deployment (6 October 2026)

- **Versions:** Signal Engine v15, Trade Manager v12, Strategy Tester v5. The
  Chart Overlay is unchanged (v5).
- **Updates:** each chart instance updated in place and was renamed to the
  version-free names.
- **Link:** the Trade Manager was re-linked to the Signal Engine
  (`6J83Ka$0..$9`, "All 10 sources connected").
- **Compile:** no errors.
- **Layout:** saved as you had it (5m, your manual price range, your 5
  drawings).

### Fingerprints

- `1 Brain - Signal Engine.pine`: 1,719 lines — SHA-256 `05c7f0156fd41ed91a5c3d14055806802e8abe2d8ace4ff9b9cd07001db2719f` (TradingView v15)
- `2 Execution - Trade Manager.pine`: 303 lines — SHA-256 `d5d9d9dedfa6b3af58f1c41d2dbd59db19880de84674f3c3702be7361730261d` (TradingView v12)
- `3 Strategy Tester.pine`: 1,820 lines — SHA-256 `4cad2fbdc96f5b67c0ce05fa099813a1efc1a80e69e8f2e717b7e811b669c442` (TradingView v5)
- `4 Chart Overlay - SMC ICT.pine`: unchanged — SHA-256 `bbe79ea60242cb7973768d9d709dd6736023ab0761a9cf7864a2f34a3f96eb45` (TradingView v5)
- Backtest scripts:
  - `backtest/v76_report.py`: V7.6 and V7.5 on the latest 6 months, plus the
    older-data check;
  - `v76_lab.py`: setups with the audit switches;
  - `v76_frontier.py`, `v76_combos.py`, `v76_features.py`, `v76_famous.py`,
    `v76_families.py`, `v76_m1.py`, `v76_ml.py`;
  - `data_check.py` and `fetch_dukascopy_days.py`: data validation and repair.

---

## Part 2 — Change history (superseded where it conflicts with Part 1)

### V7.5 — 5 October 2026 (superseded by V7.6)

#### Your rules and targets

- SL is structure-based (protected swing, reaction extreme, safety buffer),
  volatility-adaptive and at most **$15** from entry; a wider structural stop
  means **NO TRADE**.
- **TP1 > 1.5R**, **TP2 > TP1**, at levels the market structure allows;
  otherwise **NO TRADE**.
- **No break-even.**
  - TP1 or TP2 = WIN; SL before TP1 = LOSS.
  - After TP1 the runner keeps the original stop. A later stop is still a WIN
    and is not shown as an SL hit.
- Targets (latest request):
  - **about 80–85% wins over 100+ trades**;
  - **about 1 valid trade per trading day**;
  - meaningful profit, good expectancy and profit factor, reasonable
    drawdown.
  - Not by making the system so strict that it barely trades.

#### Bottom line

Measured on 1 Jan 2024 – 4 Oct 2026 (719 trading days), $0.30 cost per trade,
one position at a time (as the Execution script trades):

| | V7.3 | V7.4 | V7.5 balanced (calm 1H off) | **V7.5 default** |
|---|---|---|---|---|
| Trades (per day) | 542 (0.75) | 403 (0.56) | 319 (0.44) | **234 (0.33)** |
| Days with at least one trade | 320 | 267 | 227 | **173** |
| Wins / losses | 268 / 274 | 211 / 192 | 184 / 135 | **142 / 92** |
| Win rate | 49.4% | 52.4% | 57.7% | **60.7%** |
| Win rate in-sample / out-of-sample | 49.8% / 48.9% | 50.8% / 54.7% | 56.5% / 59.4% | **60.1% / 61.5%** |
| Net / expectancy | +129R / +0.24R | +131R / +0.33R | +147R / +0.46R | **+128R / +0.55R** |
| Profit factor (in / out) | 1.45 (1.47 / 1.41) | 1.65 (1.55 / 1.83) | 2.04 (1.90 / 2.24) | **2.32 (2.22 / 2.49)** |
| Max drawdown / longest losing streak | 15.1R / 8 | 8.5R / 7 | 6.6R / 5 | **4.3R / 3** |
| Win rate (PF) 2024 / 2025 / 2026 | 48.1% (1.36) / 47.9% (1.41) / 56.0% (1.78) | 48.1% (1.38) / 51.1% (1.61) / 65.7% (2.80) | 56.9% (1.94) / 55.1% (1.90) / 66.1% (2.77) | **61.5% (2.26) / 56.8% (2.14) / 71.9% (3.52)** |
| Rolling 100-trade win rate (min / median / max) | 39% / 50% / 57% | 45% / 51% / 58% | 52% / 56% / 61% | **54% / 60% / 64%** |

- **V7.5 default outcomes:** 113 TP2, 29 TP1 then runner stopped (WIN), 92
  SL before TP1 (LOSS).
- **2026's 71.9% is only 32 trades.** Use the full-period and out-of-sample
  figures.

**80–85% is not reached, and 1 trade per day is not reached.**
- **Frequency costs edge.** Every rule that adds frequency removes the edge;
  every rule that adds win rate removes trades. The table below shows the
  frontier.
- **The best robust results:**
  - **60.7% at 0.33 trades/day** (default);
  - **63% at 0.29/day** (break within 10 bars + calm 1H);
  - **67% at 0.13/day** (adding the dollar filter, 91 trades only).
- **At about 1 trade per day the win rate is about 50%.**
- **Why 80% is mechanically out of reach:**
  - With perfect knowledge of the next hour's direction, these entries,
    stops and targets win only **71.8%**.
  - A random entry wins about 40%.

| Rules on top of the 4H + 1H + 5m Supertrend trend stack | Trades/day | Win rate | PF | Net |
|---|---|---|---|---|
| Trend stack removed (any 5m internal break) | 1.87 | 40.8% | 0.98 | −13R |
| V7.4 rules, overlapping trades allowed | 1.07 | 50.0% | 1.49 | +200R |
| V7.4 (no extra rule) | 0.56 | 52.4% | 1.65 | +131R |
| Break ≤ 13 bars after the pivot | 0.50 | 56.5% | 1.93 | +154R |
| Break ≤ 11 bars (V7.5 balanced) | 0.44 | 57.7% | 2.04 | +147R |
| Break ≤ 10 bars | 0.40 | 59.3% | 2.17 | +146R |
| **Break ≤ 11 bars + calm 1H (V7.5 default)** | **0.33** | **60.7%** | **2.32** | **+128R** |
| Break ≤ 10 bars + calm 1H | 0.29 | 63.0% | 2.55 | +126R |
| Break ≤ 9 bars + calm 1H + dollar index trending the same way | 0.13 | 67.0% | 2.90 | +60R |

#### V7.5 research round — what was tested

Method: `inspect → research → modify → backtest → visual check → keep or
revert`, every rule judged on both halves of the data (in-sample to June
2025, out-of-sample after).

1. **Feature study** (`backtest/v75_lab.py`). Each of the 770 V7.4 setups
   was simulated alone with 30 context features. Win rates by condition
   (in-sample / out-of-sample):

   | Condition | Better side | Worse side |
   |---|---|---|
   | Bars from the broken internal pivot to the break | ≤ 7 bars: 56.9% (53.8 / 60.9) | ≥ 12 bars: 42.5% (45.0 / 36.5) |
   | Impulse (broken level − protected extreme) | < 1.74 ATR: 56.5% (57.6 / 55.0) | above: 46% |
   | 1H Choppiness Index(14) | < 49: 53% | ≥ 49: 43.7% (42.2 / 46.3) |
   | Session (New York time) | after 16:00: 55.3% | before 07:15: 45.7% |
   | Side | longs 50.9% | shorts 45.2% |

   Pullback depth, extension from EMA 20, ADR used, volatility ratio, day of
   week, premium/discount and CHoCH vs BOS were noise or flipped between the
   halves.

2. **Professional methods and indicators.** Researched: ICT SMT divergence,
   Silver Bullet, OTE retracement, Candle Range Theory, ADR exhaustion,
   Choppiness Index and DXY confirmation. None of them publishes verifiable
   gold backtests, so each was measured here:
   - **Choppiness Index (E.W. Dreiss)** on 1H, as a regime filter: **adopted**.
   - **Silver (XAGUSD) confirming the break:** 52.7% vs 47.5%.
   - **SMT divergence:** no consistent effect (51.5% vs 49.5%).
   - **US Dollar Index.** Gold setups taken while the dollar trends the
     **same** way won 54.4% (52.6 / 57.5). With the dollar falling (the
     textbook confirmation) they won 47.1%. Gold rising against a rising
     dollar is gold-specific demand. This is probably specific to the
     2024–26 regime, so it was not adopted.
   - **ADR exhaustion and OTE depth:** not monotonic, so noise.
3. **Faster 4H / 1H trend readings**, with every other V7.5 rule kept:

   | 4H + 1H reading | Trades | Win rate | PF | Net |
   |---|---|---|---|---|
   | **50-bar structure + 50-bar structure (current)** | **234** | **60.7%** | **2.32** | **+128R** |
   | 4H 50-bar + 1H 20-bar | 219 | 58.4% | 2.19 | +114R |
   | 4H 20-bar + 1H 50-bar | 288 | 55.6% | 1.83 | +111R |
   | 4H Supertrend + 1H 50-bar | 245 | 55.1% | 1.85 | +98R |
   | 4H EMA 50 + 1H 50-bar | 276 | 54.0% | 1.79 | +106R |
   | 4H 10-bar + 1H 50-bar | 319 | 53.9% | 1.74 | +114R |
   | 4H 20-bar + 1H 20-bar | 244 | 54.5% | 1.81 | +94R |
   | 4H Supertrend + 1H Supertrend | 264 | 52.3% | 1.65 | +86R |

4. **More triggers.** Internal swing length 3 or 4 adds trades at 50–53%;
   length 7 is worse. Length 5 (LuxAlgo default) stays.
5. **Entry and stop.**
   - A retest-limit entry at the broken level wins less (53.9–55.6% vs
     57.7%): limit fills come mostly from trades that then fail.
   - A deeper 15m-swing stop rarely fits $15. Changing only those 14 trades
     made no difference.
   - Stop buffers of 0.15, 0.5 and 0.8 ATR are worse than 0.3.
6. **ML ceiling inside the trend stack** (39 features, trained to June 2025):
   - Out-of-sample AUC is 0.55–0.59.
   - The best 20–30% of setups won 57–63%, the same as the hand-built rules.
7. **TP2 cap 2–4R:** net +117R to +129R with no trend, so 2.5R is kept.

#### Visual verification, feature by feature

From the live TradingView chart (5m, 5 Oct 2026) and from review charts
rendered from the same 2024–26 data:

| Feature | What the code produces | Check against a trader's reading | Verdict |
|---|---|---|---|
| 5m market structure (BOS / CHoCH) | LuxAlgo internal structure (5-bar pivots) | Labels sit on the closes that break the last internal pivot. On 5 Oct the rally into the 4,169 equal highs and the following lower highs and bearish break read the same as a pro would | Correct; used as the trigger |
| Trend / bias (4H, 1H) | LuxAlgo swing structure, 50-bar pivots | Reads **major** structure. It stayed bullish through September 2026's 5% pullback (major swing low 3,996 intact), where an intermediate-swing reading says bearish | Interpretation is "major structure"; every faster reading tested worse (above), so it stays |
| Confirmation | 5m Supertrend + fast pullback + calm 1H | Rejected trades on the review charts are the ones a pro would skip (slow pullbacks in ranges, buys into resistance after spikes) | Used |
| Liquidity (EQH / EQL, 4H swing) | 15m equal highs/lows (unswept), 4H swing high/low | 5 Oct: the 4,169 EQH was swept by the rally before the reversal | Used as obstacles |
| 15m Pivot S/R | Heikin-Ashi pivots with an ATR band | 5 Oct: the 4,160–4,165 zone rejected price at 19:30 | Used as obstacles |
| Supply / Demand (15m) | Base-candle zones | Since V7.4 the full base, as a trader draws it; first-touch hold 34–44% | Display only (no edge) |
| Order Blocks, FVG (15m) | LuxAlgo OB; three-candle gaps | Drawn where a pro would draw them; as obstacles or entries they cost trades | Display only |
| AOI | V7.1 AOI pipeline removed in V7.2 | AOI touch + confirmation won 32–38% | Not used; the pullback's protected extreme is the stop anchor |
| Entry | Trigger candle close | Retest entries tested worse | Kept |
| SL | Protected extreme ∓ 0.3 ATR(89), at most $15 | Sits under the pullback low (longs) / above the pullback high (shorts) | Kept |
| TP | TP1 1.51R with clean room; TP2 2.5R or before the next obstacle | TP1 never crosses a 15m pivot zone, unswept EQH/EQL or the 4H swing | Kept |

The "direction" panel (MACD, Stoch RSI, …) of the Visual Reference is
display only; no decision uses it.

#### How V7.5 works

```
Engine 6 trigger: confirmed 5m internal break (CHoCH or BOS) with BOTH 4H and 1H bias
                  AND the 5m Supertrend(10, 3) pointing the same way
                  AND the break comes at most 11 bars after the broken internal pivot   <- V7.5
                  AND Choppiness Index(14) of the last completed 1H bar < 50            <- V7.5
Engine 7 (unchanged):
  entry  = trigger candle close
  SL     = protected extreme of the broken leg ∓ 0.3 × ATR(89); skip if > $15 or < $2
  TP1    = entry ± 1.51R, only if no obstacle lies between entry and TP1
           obstacles = 15m Pivot S/R zones, unswept 15m EQH/EQL, 4H swing high/low
  TP2    = 2.5R, or 0.1 ATR in front of the first obstacle beyond TP1 if nearer;
           must be > TP1 + 0.25R
  otherwise NO TRADE
Execution (unchanged): 50% at TP1 (WIN); the runner keeps the original SL
           (no break-even) and exits at TP2 (WIN) or SL (still a WIN after TP1)
```

- **New inputs** (group *Engine 6 — Trigger*):
  - *Require fast pullback* (ON);
  - *Max bars from broken pivot to break* (11);
  - *Require calm 1H (Choppiness Index)* (ON);
  - *1H Choppiness length* (14);
  - *1H Choppiness maximum* (50).
- **Balanced mode:** switching *Require calm 1H* OFF gives 0.44 trades per day
  at 57.7%, with more total profit (+147R) but a higher drawdown (6.6R).
- **New table rows:**
  - "Bars since pivot L / S (max 11)";
  - "1H Choppiness (max 50)": the value plus calm/choppy;
  - "Trade side allowed now" now also reports "none (1H choppy)".
- **The bridge to Execution is unchanged:** the same ten `BRIDGE_*` plots.
- **R per trade:**
  - loss −1R;
  - TP1 then runner stopped +0.26R;
  - TP1 then TP2 about +1.95R.

#### Diagnosis: too much logic, wrong information, or a market limit?

From the V7.3 investigation; it still holds for V7.5.

Each cause was tested separately (`backtest/audit_bias.py`,
`audit_bias2.py`, `audit_zones.py`, `audit_oracle.py`).

1. **Too much logic: yes, already removed.** The V7.1 AOI score, lock, touch
   and confirmation stack cut trades without adding wins. Under the same rules
   it won 38.5% at 0.23 trades/day; the simpler V7.3 wins 49.4% at 0.75/day.
2. **Wrong trend information: yes, but fixing it does not help.**
   - The 4H "bias" flips only when price closes beyond a swing confirmed 50
     bars later (8+ trading days on 4H). It stayed **bullish through the
     whole September 2026 fall** (4,480 → 4,258), waiting for 3,995.7, and
     took a median of ~2,500 hours to flip after a 3% adverse move.
   - However, every trend reading agrees with the next 24h move only 49–54%
     of the time, including the faster ones that look right on a past chart.
   - Putting those faster readings into V7.3 made it **worse** (PF 1.14–1.36
     vs 1.45). The slow bias captures gold's long-term trend, which persists.
3. **Wrong zone information: yes, but correct zones have no edge either.**
   - Supply/Demand zones are capped at 0.05% height, about $2 (0.5 ATR); a
     trader draws the full base (about 1.5 ATR). Capped zones hold 35.3% at
     1.5R, worse than a level with no edge, because the stop sits in the noise.
     (V7.4 raised the cap to 0.5%; these zones no longer gate trades.)
   - Trader-style zones hold 38.0%. Adding strong departure, trend and
     discount/premium gives 39.6–40.3%; an OB that caused a BOS gives 40.3%.
     All are at the no-edge level of about 40%.
   - V7.3 no longer uses these zones for entries.
4. **The market limit is the main cause.** Given *perfect* (future) knowledge
   of the next 1h / 4h / 24h direction, V7.3's entries, stops and targets reach
   only **71.8% / 70.0% / 59.6%**. Under TP1 > 1.5R with no break-even, 80% is
   beyond even perfect direction knowledge.
5. **Why it looks better by eye.** On a past chart the zones that held are
   visible and the failed ones are mentally discarded (hindsight). Before the
   touch, the same filters cannot separate winners from losers: models trained
   on 35 features score AUC 0.51–0.53 out-of-sample.

#### Research applied

| Source idea | How it was tested | Result under your rules |
|---|---|---|
| Asian-range false breakout, London/NY ([Gold H1 Breakout Failure](https://www.tradingview.com/script/8Iv42BDE-Gold-H1-Breakout-Failure-V11-0), [Session Liquidity Sweep](https://www.mql5.com/en/market/product/167559)) | Close outside the 20:00–24:00 ET range, then a close back inside, 02:00–11:00 ET; stop beyond the excursion | 35% win rate, PF 0.86 |
| ICT: liquidity sweep, then CHoCH ([TradeZella](https://www.tradezella.com/blog/backtest-ict-strategy)) | Sweep of PDH/PDL, Asia/London H/L, EQH/EQL or 15m swing, then an internal CHoCH back inside; stop beyond the sweep | 34%, PF 0.84; killzone-only 33%; with 4H bias 38% |
| ICT displacement, then FVG retrace ([Backtrex FVG](https://backtrex.com/en/blog/fair-value-gap-trading-strategy)) | Body ≥ 1 ATR leaving a 5m FVG in the 4H+1H direction; limit at the FVG midpoint | 35%, PF 1.06 (killzone 36%) |
| Opening-range breakout ([NexusFi](https://nexusfi.com/showthread.php?p=364573)) | NY 09:30–09:45 range, break in the 4H direction | 36%, PF 0.96 |
| Zone quality: fresh, first touch ([LuxAlgo S/D Pro](https://www.luxalgo.com/library/indicator/h0jxhmgn-supply-demand-zones-pro/)) | First touch of every 15m / 1H / 4H zone (15,694 touches) | 34–44% hold at 1.5R, the same as a level with no edge |
| AOI touch, then 5m break (V7.1 style) | First zone touch, then an internal break back out | 32%, PF 0.81 (37% with 4H+1H) |
| **Trend continuation** (pullback-end structure break in the 4H+1H trend) | V7.2/V7.3 trigger | **The only family with a consistent edge** |

#### Clean-room obstacle set (chosen in V7.3, unchanged since)

Which levels block TP1, and in front of which TP2 is placed:

| Obstacles | Trades | Win rate | PF in / out | Net | DD |
|---|---|---|---|---|---|
| V7.2: Supply/Demand + OB + Pivot S/R zones | 320 | 46.2% | 1.21 / 1.45 | +54R | 8.2R |
| Supply/Demand only | 526 | 44.5% | 1.18 / 1.16 | +53R | 21.7R |
| Order Blocks only | 945 | 45.6% | 1.19 / 1.27 | +120R | 21.7R |
| Pivot S/R only | 581 | 47.5% | 1.34 / 1.32 | +106R | 18.0R |
| **Pivot S/R + unswept EQH/EQL + 4H swing (V7.3)** | **542** | **49.4%** | **1.47 / 1.41** | **+129R** | 15.1R |

**Why.** The 15m Supply/Demand zones and OBs did not hold as reaction levels,
so treating them as obstacles only removed good trades. The **15m Pivot S/R
zones** (real swing turning points) and **resting liquidity** (equal
highs/lows, the 4H swing) do stop price, so a trade that must pass through
them before TP1 is skipped.

#### Iteration log (each change was kept only if it held in both halves)

| # | Change tested | Result | Decision |
|---|---|---|---|
| 1 | TP1 and TP2 both at real liquidity/structure levels | Win rate 38%, PF 1.06: TP1 lands near 1.9R and price stalls in front of liquidity | Rejected |
| 2 | Front-running targets by 0–0.4 ATR | 38% at every setting | Rejected |
| 3 | TP1 as a 1.51R partial with a structural TP2 | 44%, PF 1.08 | Rejected |
| 4 | The researched setup families (table above) | 32–38% | Rejected |
| 5 | Clean-room obstacles: Pivot S/R only | PF 1.30 → 1.33, trades +80% | Kept, then extended in #6 |
| 6 | Adding EQH/EQL and the 4H swing as obstacles | PF 1.45, 49.4% | **Kept (V7.3)** |
| 7 | Adding PDH/PDL or the 15m swing as obstacles | Lower PF and fewer trades | Rejected |
| 8 | Stop cap in ATR (1.5 / 2 / 2.5 / 3) | 58% at 1.5 ATR but 0.1 trades/day; 3 ATR no gain | Rejected (frequency) |
| 9 | Stop cap $10 / $12 / no cap | $10: PF 1.45 but fewer trades in 2026; no cap: PF 1.18 | $15 kept |
| 10 | 15m bias added to, or instead of, 4H/1H | Added: PF in 1.65 / out 1.41 (decays); instead: worse | Rejected |
| 11 | Close 33% / 50% / 67% / 100% at TP1 | PF 1.46 / 1.45 / 1.42 / 1.36 | 50% kept |
| 12 | Buffer 0.2 / 0.5 ATR, TP2 2 / 3R | Same plateau (PF 1.29–1.33) | Defaults kept |
| 13 | Session / hour filters | Only 06–09 ET is weak in both halves (69 trades, PF 1.13 / 0.89); too thin | Rejected |
| 14 | ML ceiling (all features) | Out-of-sample AUC 0.51–0.53 | Confirms there is no hidden edge |
| 15 | Famous-indicator filters on the trigger bar (20 tested, table above) | Trend filters +2–3 points of win rate; oscillators nothing; ADX worse | **Supertrend kept (V7.4)** |
| 16 | Supertrend settings | ATR 7–20 with factor 3–4 all similar; factor 2 filters almost nothing | Default ATR 10 / factor 3 |
| 17 | Stacking trend filters (Supertrend + Ichimoku cloud, VWAP, Range Filter) | All five: 53.7%, PF 1.80, but 300 trades and net +116R | Rejected (they measure the same trend) |
| 18 | Block entries inside an opposing 15m Pivot zone | PF 1.65 → 1.52 | Rejected |
| 19 | Break-candle filters (LuxAlgo confluence, strong close, body size, close location) | 48.5–52.4% on fewer trades | Rejected |
| 20 | Feature study: 770 V7.4 setups, 30 context features, each setup simulated alone | Fast pullback, tight structure and calm 1H hold in both halves; most others are noise | Candidates |
| 21 | Fast pullback: break at most 11 bars after the broken pivot | 52.4% → 57.7%, PF 2.04, net +147R, DD 6.6R; 9–14 bars all improve | **Kept (V7.5)** |
| 22 | Calm 1H: Choppiness Index(14) < 50, on top of #21 | 60.7%, PF 2.32, DD 4.3R, 0.33/day; 45–55 all similar | **Kept (V7.5 default, switchable)** |
| 23 | Tight structure (impulse < 2 ATR) | 55.9% alone; little extra on top of #21–22 | Rejected (frequency) |
| 24 | Silver confirmation, SMT divergence, dollar index | +2–5 points on a third to a half of the trades; the dollar effect is the opposite of the textbook | Rejected (frequency, regime risk) |
| 25 | Faster 4H/1H trend readings (10/20-bar structure, Supertrend, EMA 50) | 52–58% vs 60.7% | Rejected |
| 26 | Internal swing length 3 / 4 / 7 (more or fewer triggers) | 50–56% | Rejected |
| 27 | Retest-limit entry; 15m-swing, tighter or wider stop | 53.9–56.2% vs 57.7% | Rejected |
| 28 | ML ceiling inside the trend stack (39 features) | Out-of-sample AUC 0.55–0.59; best 20–30% of setups win 57–63% | Confirms a ceiling around 60–65% |
| 29 | TP2 cap 2.0 / 2.5 / 3.0 / 3.5 / 4.0R | Net +117R to +129R, no trend | 2.5R kept |

#### Visual review

Charts were rendered from the same price data (`backtest/render.py`,
`backtest/review/*.png`):

- **Zones.** The 15m demand/supply zones are thin and numerous, and are cut
  through in trends.
- **Winners.** V7.3 winners come after a pullback-end break in the trend,
  with the stop under the pullback (e.g. 8 Jun 2026 05:10 short, TP2; 16:50
  short, TP2 capped before an obstacle).
- **Typical loser.** A late entry after an extended move (8 Jun 09:05 short:
  sold near the low, a demand zone held, sharp reversal).
- **Range days.** On choppy two-way days (e.g. 24–25 Aug 2026) the clean room
  keeps the system out.
- **V7.4 on the live chart (5m, 5 Oct 2026).**
  - The new table rows read "5m Supertrend (10, 3) DOWN 4,150.83" and
    "Trade side allowed now: none (4H/1H mixed)". The 4H bias is still
    bullish and the 1H bearish, so the system stands aside, as designed.
  - The Supertrend line and the obstacle zones/lines appear only within reach
    of a trade.
- **V7.5 review charts** (`backtest/render75.py`; yellow = V7.5 trades, grey =
  V7.4 trades that V7.5 filters out):
  - **11–12 Aug 2026.** The two V7.4 losses V7.5 removes are a long after a
    slow 14-bar pullback inside a range, in a choppy 1H, and a long bought
    straight into a 15m pivot zone at the top of a spike. A pro would skip
    both.
  - **22 Jun 2026.** The removed short sold into 15m support right after a
    strong rally.
  - **10 Aug 2026 (the filters' cost).** Three winning V7.4 longs at the start
    of the August rally are skipped: the 1H was still choppy from the
    preceding range, or the break came 12 bars after the pivot.

#### TradingView deployment and validation (V7.5) — 5 October 2026

- **The Brain was saved as v13.** The chart's Brain instance (`6J83Ka`)
  updated in place:
  - Execution still reads `6J83Ka$0..$9` ("All 10 sources connected").
  - Every input is at its default except your table position.
- **Compile:** no errors (only the four old LuxAlgo `if top` warnings).
- **Live 5m check** (21:32 UTC+7):
  - **New table rows:** "Bars since pivot L / S (max 11): 5 / 9", "1H
    Choppiness (max 50): 59.4 choppy", "Trade side allowed now: none (4H/1H
    mixed)".
  - **Execution labels, read from the chart model:**
    - "✕ LONG LOSS −1R" (entry 4,490.29);
    - "✓ LONG WIN — TP1 (runner closed) +0.26R" (entry 4,445.10, matching the
      port's 4,444.93), with "Runner stop … (trade already a WIN)".
  - **Scoreboard** on the ~5 weeks of 5m history TradingView loads: 2 W / 1 L.
- **15m and 4H could not be checked live.** Chrome was hidden behind other
  apps, so those views were not painted; the review charts cover them.
- **Your layout was restored and saved:** 5m, your manual price range.

#### TradingView Strategy Tester — V7.5 Strategy Test (5 October 2026)

- **Script.** `3 Strategy Tester.pine` ("XAUUSD Smart Trade V7.5 — 3. Strategy
  Tester" on TradingView, chart instance `OXidda`).
  - It is the deployed V7.5 Brain code, unchanged, declared as `strategy()`,
    with an order block appended.
  - **Entry:** market at the trigger close.
  - **Exits:** 50% at TP1, the rest at TP2. Both parts keep the original stop
    (no break-even).
  - **Size:** fixed $ risk per trade (default $100), so profit / risk = R.
  - **Costs:** $0.30 per ounce round trip, as in the Python backtest.
  - The Brain's own table and drawings are off by default in this copy.
- **Why self-contained.** Your Essential plan allows **one indicator-on-indicator
  link per layout**, and the Execution → Brain bridge uses it. A strategy
  reading the Brain's bridge cannot be linked.
- **Two ways of counting wins:**
  - TradingView's "Profitable trades" counts the TP1 part and the runner part
    of each trade as two trades.
  - The table on the chart counts your rule: TP1 or TP2 = WIN, SL before TP1
    = LOSS.
  - Input *Close at TP1 (%)* = 100 makes both count the same way, but it
    removes the runner.
- **Result on the history TradingView loads for 5m** (Aug 10 – Oct 5, 2026;
  4H/1H were mixed for most of September, so there were no trades then):

  | Trade | Result | PnL at $100 risk |
  |---|---|---|
  | 11 Aug long | TP1 then TP2 — WIN | +$74.32 + $124.08 |
  | 19 Aug long | SL before TP1 — LOSS | −$102.16 |
  | 31 Aug long | TP1, then runner stopped on the original SL — WIN | +$74.24 − $51.26 |

  - **Totals:** 3 trades, 2 W / 1 L (66.7%), +1.26R before costs, +$119.21
    (+1.19R) after costs, PF 1.78, max drawdown $198.18.
  - **Match with the backtest:** two of the three trades are the same as in
    the Python backtest (10 Aug 19:20 UTC, 31 Aug 07:20 UTC).
- **Sample size.** Three trades prove nothing. The 2.75-year backtest (234
  trades) is the evidence. Testing the full history on TradingView needs a
  plan with Deep Backtesting (Premium).

#### Fingerprints

Renamed and re-saved on 5 October 2026, 22:12 UTC+7. Only the names, header
descriptions and table titles changed; the trading logic is the same as V7.5
above. On TradingView each chart instance updated in place, and the Trade
Manager was re-linked to the Signal Engine (`6J83Ka$0..$9`, "All 10 sources
connected").

- `1 Brain - Signal Engine.pine`: 1,693 lines — SHA-256 `9d8b4306a96b626a6269dd447d5109f583ca925ba6a729d4e08794c8d825b76c` (TradingView v14)
- `2 Execution - Trade Manager.pine`: 303 lines — SHA-256 `7a0632d318b86295f1ef9972b3e211abafcc474397cd19090b7fed4c4c84fd3d` (TradingView v11)
- `3 Strategy Tester.pine`: 1,797 lines — SHA-256 `11f08b79f0773e371bb848b957d4580d9bd6eaf28e6bd2753cd5587e612dfb07` (TradingView v4)
- `4 Chart Overlay - SMC ICT.pine`: 2,482 lines — SHA-256 `bbe79ea60242cb7973768d9d709dd6736023ab0761a9cf7864a2f34a3f96eb45` (TradingView v5)
- Backtest scripts:
  - `backtest/v75_report.py`: the V7.5 tables;
  - `v75_lab.py`: setups, features, one-position replay;
  - `v75_grid.py`, `v75_grid2.py`, `v75_combo.py`, `v75_combo2.py`,
    `v75_fast.py`, `v75_chop.py`: the frontier;
  - `v75_intermarket.py` and `fetch_hd_sym.py`: silver and dollar index;
  - `v75_bias.py`, `v75_micro.py`, `v75_entry_sl.py`, `v75_ml.py`;
  - `render75.py`: the review charts.

### V7.4 — 5 October 2026 (superseded by V7.5)

V7.4 added the 5m Supertrend(10, 3) agreement to the V7.3 trigger, drew the
decision levels on the chart and removed dead code. V7.5 keeps all of that.

#### Bottom line (V7.4)

Measured on 1 Jan 2024 – 4 Oct 2026 (719 trading days), with the rules above
and a $0.30 cost per trade:

| | V7.1 AOI pipeline (new rules) | V7.2 | V7.3 | **V7.4** |
|---|---|---|---|---|
| Trades (per day) | 169 (0.23) | 320 (0.44) | 542 (0.75) | **403 (0.56)** |
| Days with at least one trade | — | 213 | 320 | **267** |
| Wins / losses | 65 / 104 | 148 / 172 | 268 / 274 | **211 / 192** |
| Win rate | 38.5% | 46.2% | 49.4% | **52.4%** |
| Win rate in-sample / out-of-sample | — | — | 49.8% / 48.9% | **50.8% / 54.7%** |
| Net / expectancy | +22R / +0.13R | +54R / +0.17R | +129R / +0.24R | **+131R / +0.33R** |
| Profit factor (in-sample / out-of-sample) | 1.21 | 1.30 (1.21 / 1.45) | 1.45 (1.47 / 1.41) | **1.65 (1.55 / 1.83)** |
| Max drawdown / longest losing streak | 11.3R / 8 | 8.2R / 6 | 15.1R / 8 | **8.5R / 7** |
| By year, win rate (PF): 2024 / 2025 / 2026 | — | PF 1.08 / 1.41 / 1.60 | 48.1% (1.36) / 47.9% (1.41) / 56.0% (1.78) | **48.1% (1.38) / 51.1% (1.61) / 65.7% (2.80)** |
| Last 2 years | 97 trades, 34% | 224 trades, 47.3% | 385 trades, 49.9%, PF 1.46 | **280 trades, 53.6%, PF 1.71** |
| Rolling 100-trade win rate (min / median / max) | — | 42–49% | 39% / 50% / 57% | **45% / 51% / 58%** |

- **V7.4 outcomes:**
  - 168 TP2;
  - 43 TP1 then runner stopped (still WIN);
  - 192 SL before TP1 (LOSS).
- **2026's 65.7% is only 67 trades.** The full-period and out-of-sample
  figures are the ones to rely on.
- **Net R is about the same as V7.3,** with 139 fewer trades, the drawdown
  almost halved and a higher win rate in both halves.

**The 80% target is still not reached, and it cannot be under these rules.**
The evidence:

- **Arithmetic.**
  - A trade wins only if price travels more than 1.5 × the stop distance in
    the trade's favour before touching the stop.
  - A random entry does that about 40% of the time.
  - 80% would mean an average of about +1R on every trade.
- **Oracle test.** Even with *perfect* knowledge of the next 1h / 4h / 24h
  direction, these entries, stops and targets reach only **71.8% / 70.0% /
  59.6%**.
- **Every researched setup family** wins **32–38%** with structural targets
  (table below).
- **A statistical ceiling test** (gradient boosting and logistic regression
  on 35 context features across 9,751 setups) showed no skill
  out-of-sample: AUC 0.51–0.53, where 0.50 means no skill.
- **Best result so far.** V7.4's best window of 100 consecutive trades is 58%.
  Stacking every helpful filter reaches 53.7% (table below).

**Frequency.**
- V7.4 trades on 37% of trading days, about 0.56 per day.
- It stands aside when:
  - the 4H and 1H disagree;
  - the 5m Supertrend points against the trade;
  - an obstacle blocks TP1.
- Switching the clean room OFF gives 1.08 trades per day, but only 44.9%,
  PF 1.23, drawdown 38R. That is not recommended.

#### V7.4 audit: what was checked and what changed

This round reviewed every part of the indicator for inconsistent logic, weak
or missing logic, and computation that does nothing. Each change was tested
on the 2.75-year data.

| # | Area | Finding | Action |
|---|---|---|---|
| 1 | **Missing logic: short-term trend** | The trigger needed only the 4H and 1H bias, so it also fired while the 5m trend still pointed against the trade. Those V7.3 trades (180) won **43.9%, PF 1.13**, about the no-edge level, against 52.2%, PF 1.63 for the rest. | **Added** a 5m Supertrend(10, 3) agreement: TradingView built-in `ta.supertrend`, read on the confirmed bar, no repaint |
| 2 | **Chart vs logic mismatch** | The Visual Reference draws **5m** zones, but the Brain decides with **15m** Pivot S/R, 15m EQH/EQL and the 4H swing. Judging trades by eye used levels the logic never uses. | **Fixed:** the Brain now draws the levels it decides with. These are the Supertrend line, plus the 15m Pivot S/R zones, unswept EQH/EQL and the 4H swing high/low within reach of a trade ($37.5 = 2.5R × $15). Input "Show decision levels". |
| 3 | Dead computation | The nine-indicator dashboard (MACD, Stoch RSI, Vortex, Momentum, RSI, PSAR, DMI, MFI, Fisher), BULB and the session module ran on every bar, but no decision used them, only debug rows. | **Removed** from the Brain, along with their 20 inputs. The Visual Reference still shows that panel. |
| 4 | Formula error | LuxAlgo's optional internal confluence filter had a misplaced parenthesis: `math.min(close, open - low)` instead of `math.min(close, open) - low`. | **Corrected.** The filter is OFF by default. Turned on, it gives the same 52.4% on 28% fewer trades, so it stays OFF. |
| 5 | Zone construction | The Supply/Demand height cap of 0.05% (about $2) cut zones to a third of the base candle a trader would draw. | **Raised to 0.5%.** These zones no longer gate trades; this only affects the table. |
| 6 | Entry inside an opposing zone | A long that starts *inside* a 15m resistance zone is not blocked, because only zones ahead of the entry count. | **Kept.** Such entries win more (54.1% vs 51.7%): a break inside a zone usually means the zone is failing. Blocking them: PF 1.65 → 1.52. |
| 7 | Break-candle quality | Tested: strong close, body ≥ 0.5 ATR, body ≤ 1 ATR, close in the outer third. | **Not added.** None improved V7.4 (48.5–52.4% on fewer trades). |
| 8 | Debug table | Rows 22–27 showed dashboard states. | **Replaced** with "5m Supertrend" (direction and level) and "Trade side allowed now" (LONG, SHORT, or why none). |
| 9 | Compiler warnings | Four warnings at LuxAlgo's `if top` / `if itop` lines (a price used as a condition). | **Left as is:** harmless, since a pivot price is never 0. |

#### Famous indicators tested

Each rule was added to V7.3's trigger bar using the indicator's standard formula and
published default settings, without repainting (`backtest/famous.py`,
`famous_test.py`). Ranked by profit factor:

| Rule on the trigger bar | Trades/day | Win rate | PF | Net | Max DD | In-sample WR / PF | Out-of-sample WR / PF |
|---|---|---|---|---|---|---|---|
| None (V7.3) | 0.75 | 49.4% | 1.45 | +128.6R | 15.1R | 49.8% / 1.47 | 48.9% / 1.41 |
| Ichimoku: price beyond the cloud | 0.56 | 52.6% | 1.66 | +130.7R | 11.3R | 53.3% / 1.71 | 51.7% / 1.59 |
| **Supertrend(10, 3) agrees — adopted** | **0.56** | **52.4%** | **1.65** | **+131.1R** | **8.5R** | **50.8% / 1.55** | **54.7% / 1.83** |
| Ichimoku: Tenkan vs Kijun agrees | 0.60 | 51.8% | 1.61 | +133.6R | 18.4R | 52.0% / 1.60 | 51.6% / 1.62 |
| Session VWAP side (time-weighted; the data has no volume) | 0.60 | 51.3% | 1.60 | +131.6R | 12.0R | 51.4% / 1.63 | 51.1% / 1.56 |
| EMA 21 > 50 > 200 stack agrees | 0.46 | 50.6% | 1.59 | +100.9R | 11.2R | 52.4% / 1.66 | 48.3% / 1.50 |
| Range Filter(100, 3) agrees | 0.57 | 51.8% | 1.58 | +118.9R | 14.0R | 52.1% / 1.59 | 51.5% / 1.57 |
| Donchian(20) breakout bar | 0.52 | 50.7% | 1.54 | +104.0R | 17.3R | 51.8% / 1.60 | 49.0% / 1.46 |
| RSI(14) on the trade side of 50 | 0.72 | 50.1% | 1.49 | +133.8R | 14.7R | 50.7% / 1.53 | 49.3% / 1.44 |
| WaveTrend not overextended (abs(wt1) < 60) | 0.73 | 50.2% | 1.48 | +131.5R | 14.1R | 51.2% / 1.53 | 48.9% / 1.40 |
| WaveTrend wt1 vs wt2 agrees | 0.74 | 49.8% | 1.47 | +131.3R | 15.7R | 50.6% / 1.53 | 48.6% / 1.38 |
| Squeeze Momentum sign agrees | 0.64 | 49.2% | 1.47 | +115.4R | 18.8R | 50.2% / 1.51 | 47.9% / 1.42 |
| Squeeze released | 0.52 | 50.0% | 1.47 | +92.4R | 10.5R | 50.2% / 1.48 | 49.7% / 1.46 |
| DI+ / DI− agrees | 0.69 | 49.5% | 1.47 | +122.1R | 15.3R | 50.5% / 1.52 | 48.1% / 1.39 |
| Price beyond EMA 200 | 0.57 | 49.5% | 1.47 | +102.7R | 13.0R | 50.2% / 1.51 | 48.6% / 1.42 |
| Bollinger %B not stretched | 0.36 | 49.2% | 1.45 | +61.5R | 8.4R | 49.3% / 1.45 | 49.1% / 1.44 |
| UT Bot(1, 10) agrees | 0.75 | 49.4% | 1.44 | +126.6R | 15.1R | 49.8% / 1.47 | 48.7% / 1.40 |
| RSI not overextended (< 70 / > 30) | 0.69 | 49.4% | 1.42 | +112.5R | 17.2R | 51.2% / 1.54 | 46.9% / 1.28 |
| Hull(55) slope agrees | 0.62 | 48.9% | 1.41 | +97.5R | 17.3R | 48.8% / 1.40 | 48.9% / 1.43 |
| ADX ≥ 25 and DI agrees | 0.30 | 48.1% | 1.40 | +47.1R | 11.2R | 45.5% / 1.23 | 52.4% / 1.74 |
| ADX(14) ≥ 20 | 0.51 | 44.9% | 1.21 | +45.0R | 13.8R | 43.5% / 1.11 | 47.2% / 1.39 |

**Why Supertrend.**
- **The trend-type filters all help by about the same amount.** These are
  Supertrend, the Ichimoku cloud, Range Filter and session VWAP. The edge is
  real: they all remove trades taken against the short-term trend.
- **Supertrend has the lowest drawdown** and held up best out-of-sample.
- **It is a TradingView built-in** with no repaint.
- **It is not a tuned value.** ATR periods 7–20 with factors 3–4 give similar
  results; factor 2 flips too often to filter anything:

| Supertrend setting | Trades | Win rate | PF | Max DD | In-sample WR / PF | Out-of-sample WR / PF |
|---|---|---|---|---|---|---|
| ATR 7, factor 3 | 410 | 51.2% | 1.58 | 13.8R | 50.8% / 1.54 | 51.8% / 1.64 |
| ATR 10, factor 2 | 472 | 48.9% | 1.44 | 18.0R | 49.3% / 1.45 | 48.4% / 1.43 |
| **ATR 10, factor 3 (default)** | **403** | **52.4%** | **1.65** | **8.5R** | **50.8% / 1.55** | **54.7% / 1.83** |
| ATR 10, factor 4 | 369 | 52.6% | 1.67 | 12.6R | 53.1% / 1.70 | 51.9% / 1.63 |
| ATR 14, factor 3 | 406 | 51.7% | 1.62 | 9.5R | 50.6% / 1.53 | 53.4% / 1.76 |
| ATR 20, factor 3 | 415 | 50.6% | 1.55 | 12.6R | 50.2% / 1.51 | 51.2% / 1.61 |

**Stacking trend filters does not pay** (`backtest/famous_combo.py`). They
measure the same thing:

| Combination (on V7.3) | Trades | Win rate | PF | Net | Max DD |
|---|---|---|---|---|---|
| Supertrend + Ichimoku cloud | 361 | 52.6% | 1.68 | +121.9R | 8.5R |
| Supertrend + VWAP | 355 | 52.7% | 1.71 | +125.0R | 9.1R |
| Supertrend + cloud + VWAP | 340 | 52.9% | 1.73 | +121.6R | 9.1R |
| All five (Supertrend, cloud, Tenkan/Kijun, VWAP, Range Filter) | 300 | 53.7% | 1.80 | +116.1R | 10.1R |
| 2 of {Supertrend, cloud, VWAP} | 412 | 52.4% | 1.65 | +132.6R | 11.3R |

#### How V7.4 worked

```
Engine 6 trigger: confirmed 5m internal break (CHoCH or BOS) with BOTH 4H and 1H bias,
                  AND the 5m Supertrend(10, 3) pointing the same way      <- new in V7.4
Engine 7 (unchanged from V7.3):
  entry  = trigger candle close
  SL     = protected extreme of the broken leg ∓ 0.3 × ATR(89); skip if > $15 or < $2
  TP1    = entry ± 1.51R, only if no obstacle lies between entry and TP1
           obstacles = 15m Pivot S/R zones, unswept 15m EQH/EQL, 4H swing high/low
  TP2    = 2.5R, or 0.1 ATR in front of the first obstacle beyond TP1 if nearer;
           must be > TP1 + 0.25R
  otherwise NO TRADE
Execution (unchanged): live at the trigger close; 50% at TP1 (WIN); the runner keeps
           the original SL (no break-even) and exits at TP2 (WIN) or SL (still a WIN after TP1)
Chart:     Supertrend line; obstacle zones/lines within $37.5 of price; table rows
           "5m Supertrend" and "Trade side allowed now"
```

- **New inputs** (group *Engine 6 — Trigger*):
  - *Require 5m Supertrend agreement* (ON);
  - *Supertrend factor* (3);
  - *Supertrend ATR period* (10);
  - *Show decision levels* (ON).
- **The bridge to Execution is unchanged:** the same ten `BRIDGE_*` plots, in
  the same order (plots 0–9). The new Supertrend plot comes after them.
- **R per trade:**
  - loss −1R;
  - TP1 then runner stopped +0.26R;
  - TP1 then TP2 about +1.95R.
- **Stops:** median $7.6 overall, $10.8 in 2026.

#### TradingView deployment and validation (V7.4)

- **Brain saved as v11, then v12.** v12 only limits the drawn levels to trade
  reach.
- **The chart instance updated in place.** TradingView upgraded the Brain
  instance on the chart (`6J83Ka`) instead of leaving it pinned, as it did
  before. Consequences:
  - No re-adding was needed.
  - The Execution inputs still read `6J83Ka$0..$9` ("All 10 sources
    connected").
  - Your table position (bottom-left) carried over to the new input slot.
  - Checked through the chart API: every other input is at its default,
    including the new Supertrend inputs.
- **Compile:** no errors. Four warnings were already there before this round
  (LuxAlgo `if top`).
- **Execution + UI** is unchanged (v10); **Visual Reference** is unchanged
  (v4).
- **Restored your view and saved the layout** (no pending changes): 4h
  interval and your manual price range.
- **Live 5m check.** On the 5m history TradingView loaded, the chart's own
  scoreboard showed **7 W / 4 L** (64%, five TP2, +6.21R). That is a small
  sample. The last trade matches the backtest port: long 4,445.10 on OANDA
  vs 4,444.93 on HistData, risk about $12, TP1 hit.
  - The port lists 11 trades from 20 July to 4 October (9 W / 2 L).
  - The two do not match trade-for-trade over that window. Their price feeds
    (OANDA vs HistData) form slightly different swings, and the chart's
    history starts on a different date.
- **Reload your other TradingView tab.** A second tab with this layout was
  open with the pre-V7.4 state. Reload it before changing anything there, so
  it does not save the old state over V7.4.

#### V7.4 fingerprints

- Brain: 1,657 lines — SHA-256 `7184cf7e21a2b43932a9904208f764a94c9c1e4f4281a464991b37ffb812859b` (TradingView v12)
- Execution + UI (unchanged): 298 lines — SHA-256 `bfabd5f6337f9064412b7e81445026f5711a68c42de5e292b3ca25cca40ed9f8` (TradingView v10)
- Visual Reference (unchanged): 2,474 lines — SHA-256 `c28ab486d9f59dbbb28dda13a61e5cef61484799b2cec3df9719258488fda225`
- Backtest scripts:
  - `backtest/v74_report.py`: the V7.4 tables and the Supertrend settings;
  - `famous.py`, `famous_test.py`, `famous_combo.py`: the indicator tests;
  - `audit_inside.py`, `audit_candle.py`: the V7.4 audits;
  - `v74_extra.py`: clean room OFF and the recent trade list;
  - `v73_report.py`: the V7.3 tables.

### V7.3 — 5 October 2026 (superseded by V7.4)

V7.3 used the V7.2 trigger. Its only change was the clean-room obstacle set:
15m Pivot S/R zones, unswept 15m EQH/EQL and the 4H swing high/low, with no
Supply/Demand or OB zones. V7.4 kept all of it and added the 5m Supertrend
agreement to the trigger.

- **Result:**
  - 542 trades, 0.75/day; 268 W / 274 L;
  - win rate 49.4%, PF 1.45 (1.47 in-sample / 1.41 out-of-sample);
  - net +128.6R, max drawdown 15.1R, longest losing streak 8.
- **The weakness V7.4 fixed:** a third of V7.3's trades went against the 5m
  Supertrend and won only 43.9% (PF 1.13).

#### How V7.3 worked

```
Engine 6 trigger: confirmed 5m internal break (CHoCH or BOS) with BOTH 4H and 1H bias
Engine 7:
  entry  = trigger candle close
  SL     = protected extreme of the broken leg ∓ 0.3 × ATR(89); skip if > $15 or < $2
  TP1    = entry ± 1.51R, only if no obstacle lies between entry and TP1
           obstacles = 15m Pivot S/R zones, unswept 15m EQH/EQL, 4H swing high/low
  TP2    = 2.5R, or 0.1 ATR in front of the first obstacle beyond TP1 if nearer;
           must be > TP1 + 0.25R
  otherwise NO TRADE
Execution: live at the trigger close; 50% at TP1 (WIN); the runner keeps the original
           SL (no break-even) and exits at TP2 (WIN) or SL (still a WIN after TP1)
```

- **R per trade:**
  - loss −1R;
  - TP1 then runner stopped +0.26R;
  - TP1 then TP2 about +1.95R.
- **Stops:** median $7.5 overall, $10.6 in 2026. 2026 is the most volatile
  year, so the $15 cap rejects more setups there.

#### TradingView deployment and validation (V7.3)

- **The chart was running old versions.** During this check I found the chart
  instances pinned to **Brain v8 / Execution v9 (V7.1)**, although newer
  versions had been saved. TradingView does not upgrade a pinned instance when
  the script is saved.
- **Fix:**
  1. Added the latest **Brain v10 and Execution v10 (V7.3)**.
  2. Removed the old instances.
  3. Re-linked Execution's 10 inputs to the new Brain's plots 0–9 (verified
     through the chart API).
  4. Kept your Brain table at bottom-left and the 4h interval you had.
  5. Saved the layout (no pending changes).
- **What I could see.** The new Brain table rendered with the V7.3 rows (E6
  direction MIXED, E7 last result `NO_CLEAN_ROOM`, rules "SL ≤ $15 | TP1
  1.51R | clean room ON").
- **What I could not see.** The 5m history beyond 300 bars, the multi-week
  scoreboard and the per-trade chart walk-through. Chrome kept going behind
  other windows (the tab is not painted while hidden). The harness showed
  7 W / 7 L on the few days it loaded.
- **Please reload your own TradingView tab** so it loads the saved layout with
  the V7.3 instances, and switch to 5m to see signals.

#### V7.3 fingerprints

- Brain: 1,717 lines — SHA-256 `7ee0f48b02edfab6346d62f7debd6d68b3f52a29c9a2cd537846d60590c0cbae` (TradingView v10)
- Execution + UI: 298 lines — SHA-256 `bfabd5f6337f9064412b7e81445026f5711a68c42de5e292b3ca25cca40ed9f8` (TradingView v10)
- Visual Reference (unchanged): 2,474 lines — SHA-256 `c28ab486d9f59dbbb28dda13a61e5cef61484799b2cec3df9719258488fda225`
- Backtest: `backtest/v73_report.py` reproduces the V7.3 tables; `lab*.py`,
  `lab_events.py`, `ml_dataset.py`, `ml_ceiling.py` hold the research.

### V7.2 — 5 October 2026 (superseded by V7.3)

V7.2 introduced the trend-aligned structure trigger, the structural stop of at
most $15, TP1 1.51R with a clean room, and no break-even. Its clean-room
obstacles also included 15m Supply/Demand zones and Order Blocks. Removing
those (V7.3) nearly doubled trades and raised PF from 1.30 to 1.45.

#### Rules this version was built to (your specification)

- Stop loss is **structure-based**, never more than **$15**.
- **TP1 > 1.5R** and **TP2 > TP1**; the targets must leave clean room, or the
  setup is **NO TRADE**.
- **No break-even.**
  - TP1 or TP2 reached = **WIN**; SL before TP1 = **LOSS**.
  - After TP1 the runner keeps the original stop. If that stop is hit later,
    the trade is still a WIN and is not shown as an SL hit.
- Goals: **≥ 80% win rate over 100 trades** and **≥ 1 trade per trading
  day**, without overfitting. Profit, profit factor and drawdown matter more
  than win rate.

#### Bottom line

Tested on **1 Jan 2024 – 4 Oct 2026** (2.75 years; the last two years are
shown separately). Every variant uses the rules above and a $0.30 cost per
trade.

| | V7.1 AOI pipeline, new rules | **V7.2 (default)** | V7.2, clean room switched OFF |
|---|---|---|---|
| Trades (per trading day) | 169 (0.23) | **320 (0.44)** | 970 (1.35) |
| Wins / losses | 65 / 104 | **148 / 172** | 440 / 530 |
| Win rate | 38.5% | **46.2%** | 45.4% |
| Net | +22.2R | **+53.9R** | +119.1R |
| Expectancy per trade | +0.13R | **+0.17R** | +0.12R |
| Profit factor | 1.21 | **1.30** | 1.22 |
| Max drawdown | 11.3R | **8.2R** | 23.0R |
| Max losing streak | 8 | **6** | 11 |
| Last 2 years only | 97 trades, 34.0%, PF 1.13 | **224 trades, 47.3%, PF 1.37, DD 8.2R** | 715 trades, 45.0%, PF 1.21, DD 22.8R |

**The 80% win rate cannot be reached under these rules, and the reason is
mechanical.** With TP1 above 1.5R and no break-even, a trade wins only if price
travels more than 1.5 × the stop distance in your favour before touching the
stop. A random entry does that about 40% of the time, and 80% would mean about
+1R profit on every trade. Measured on 2.75 years:

- Every signal family tested (zones, liquidity sweeps, CHoCH/BOS, sessions,
  HTF alignment) scored **34–48%**.
- The best V7.2 window of 100 consecutive trades reached **49%**, the worst
  42%.

No configuration I could find, and none that would survive out-of-sample,
comes close to 80%. Reaching ~70% is possible only by putting TP1 near 0.5R,
which your TP1 > 1.5R rule forbids.

**Frequency.** Your clean-room rule halves the trades but cuts the drawdown
from 23R to 8R; both settings are profitable. At current volatility the $15 cap
also blocks many setups. With the clean room ON, V7.2 averages 0.44 trades per
day, and there are no-trade weeks when the 4H and 1H disagree (as in September
2026). One trade per day requires switching the clean room OFF
(*Require clean room to TP1* input).

#### What the investigation found

1. **The AOIs do not predict reactions.**
   - Every 15m zone the system detects was measured at its first touch:
     15,694 touches in 2.75 years.
   - Trade model: limit at the near edge, stop just beyond the far edge, target
     1.5R.
   - Win rate: Demand 34–35%, Supply 36%, OB 39–44% (small samples), FVG
     37–41%, Pivot S/R 36–38%. A level with no edge scores about 40%.
   - Splitting by 4H/1H agreement, premium/discount location, zone height or
     zone age changed nothing.
   - The same zone logic on **1H and 4H candles** also held only 35–38%.
2. **Requiring an AOI touch made trades worse.** Trend-aligned structure
   breaks that also touched a fresh zone scored PF 0.89 in-sample, against
   1.18 without the requirement.
3. **The simplest signal was the best.** A 5m internal structure break (CHoCH
   or continuation BOS) in the direction of **both** the 4H and the 1H bias won
   45% at 1.5R and fired 1.56 times per day, better than the whole AOI
   pipeline (38–42%, 0.23 per day). Neither side alone worked: 4H-only won
   34.5% and 1H-only lost money.
4. **Structural targets placed TP1 too far.** Using the first structure level
   beyond 1.5R put TP1 at about 2.0R on average and dropped the win rate to
   35%. Price showed no "magnet" effect toward EQH/PDH/swing levels.
   - A TP2 at the next structure level did slightly worse than 2.5R (PF 1.15
     vs 1.22).
   - Capping TP2 just in front of the next opposing zone did as well as 2.5R
     (PF 1.30) and lowered the drawdown.
5. **Clean room works as a context filter, not as a reaction filter.**
   Opposing zones in the path mostly mark choppy, two-way markets. Skipping
   those setups kept the profit factor (1.30 vs 1.22) and cut the drawdown
   (8.2R vs 23R).
6. **Visual review.** I checked charts rendered from the same price data, with
   every zone outlined green (held) or red (failed) at first touch and every
   trade's entry, SL, TP1 and TP2 drawn:
   - **Zones:** thin 15m demand/supply zones sit everywhere and are sliced
     through in trends. On range days (e.g. 24–25 Aug 2026) price crosses
     zones in both directions.
   - **V7.2 behaviour on those days:** it stands aside because opposing zones
     block TP1, while the clean-room-OFF variant alternates wins and losses.
   - **V7.2 entries** (e.g. 6–7 Oct 2025) follow a structure break in the
     trend, with the stop under the pullback low.
   - **Losers** are mostly late entries after a spike near the top of an
     extended push.

   The TradingView chart could not be used for these screenshots because its
   window was behind your other apps (see validation below).

#### How V7.2 works

```
4H structure bias ─┐
1H structure bias ─┼─► Phase 5 (unchanged, confirmed [1]-offset MTF data)
15m zones ─────────┤      zones are now the obstacle map, not entry anchors
5m structure ──────┘
          │
          ▼
Engine 6 — trigger (Brain): confirmed 5m internal break (CHoCH or BOS)
          in the direction of BOTH the 4H and the 1H bias
          │
          ▼
Engine 7 — construction (Brain)
  entry  = trigger candle close
  SL     = protected swing extreme of the broken leg ∓ 0.3 × ATR(89)
           skip if SL > $15 or < $2
  TP1    = entry ± 1.51R, only if no opposing 15m Supply/Demand, OB or
           Pivot S/R zone lies between entry and TP1 (clean room)
  TP2    = 2.5R, or 0.1 ATR in front of the first opposing zone beyond TP1
           if that comes earlier; must be > TP1 + 0.25R
  otherwise NO TRADE
          │  ten BRIDGE_* plots
          ▼
Execution + UI: live at trigger close → TP1 (WIN, 50% closed, runner keeps SL)
          → TP2 (WIN) or SL (LOSS before TP1 / still WIN after TP1)
```

- **Protected extreme.** The lowest low (long) or highest high (short) from
  the internal swing pivot that was just broken, up to the trigger candle.
  This is where the pullback ended; if price goes beyond it, the setup is
  invalid. If that pivot is more than 200 bars old, the last 13 bars are used.
- **Stop buffer.** 0.3 × ATR(89), about $1.2–1.8 at 2026 volatility. It scales
  with volatility, so normal wicks do not touch the stop. Buffers of 0.1–0.8
  ATR (ATR(89) or ATR(14)) all gave PF 1.17–1.20 without the clean room; 0.3
  is the middle.
- **Why the trade is skipped instead of the stop being tightened.** A stop
  inside the structure would sit where the idea is still valid, so it would be
  hit by normal noise.
- **R accounting.**
  - Loss = −1R.
  - TP1 then runner stopped = 0.5 × 1.51 − 0.5 = **+0.26R**.
  - TP1 then TP2 = 0.5 × 1.51 + 0.5 × TP2R = **about +1.9R**.
  - Closing 100% at TP1 instead gives PF 1.18 (+33R), so the runner adds
    profit.

#### What changed in the code

| Area | Change | Reason |
|---|---|---|
| Brain Engine 6 | The AOI candidate builder, score, lock/retarget, touch, confirmation and consumed registry were **removed** and replaced by the trend-aligned 5m structure trigger | AOI gating showed no edge (above) and made results worse |
| Brain Engine 7 | Structural stop beyond the protected extreme + 0.3 ATR, **$15 maximum** and $2 minimum; TP1 1.51R with the clean-room check; TP2 2.5R or before the next opposing zone; NO TRADE otherwise | Your rules, tested |
| Brain | New inputs: stop buffer, max/min stop $, TP1 R (min 1.51), TP2 max R, TP2 front-run, *Require clean room to TP1* | Visible, adjustable rules |
| Brain | Debug rows 28–39 now show the 4H+1H direction, last trigger, last result (e.g. `SL_TOO_WIDE`, `NO_CLEAN_ROOM`), protected extreme, entry, SL/$ risk, TP1/TP2 with R, and the rules in force | Transparency |
| Bridge | Same ten plots. IMPULSE_A = protected extreme, IMPULSE_B = broken swing level; TP codes = floor(R × 10); reason codes 1, 7–11 | Compatible with Execution |
| Execution | **No break-even**: the runner keeps the original stop. A stop after TP1 = `WIN_TP1` (runner closed), never labelled an SL hit. Validation re-checks SL ≤ $15, TP1 > 1.5R, TP2 beyond TP1 | Your rules |
| Execution | Chart results row: W/L, win rate, TP2 count, net R | Live scoreboard |
| Code size | Brain 2,305 → 1,697 lines | Simpler |

#### Tested and rejected (2.75 years, your rules)

| Idea | Result |
|---|---|
| Keep the AOI pipeline, add the new SL/TP rules | 38.5% win rate, 0.23 trades/day, PF 1.21 |
| TP1 at the first structure level beyond 1.5R | 35% win rate, PF 1.04 |
| TP2 at the next structure level (not capped at 2.5R) | PF 1.15 vs 1.22 |
| 4H-only bias (instead of 4H + 1H) | PF 1.14 at 0.61/day with the clean room, PF 1.13 at 2.05/day without; the 1H-only bias loses money |
| Internal CHoCH only (no continuation BOS) | PF 1.01, and negative over the last two years |
| AOI touch required before the trigger | Worse in-sample (PF 0.89) |
| Retest limit entry at the broken level | PF 1.27 with the clean room vs 1.30 at market (and 1.14 vs 1.22 without it); adds no trades |
| Counting FVGs as obstacles | 2024 turns negative |
| Displacement body filter | No gain under these rules |
| Time-in-trade limit (12–24 h) | Slightly worse |
| Session/hour, day-of-week, volatility, momentum filters | Results flip sign between the two halves (noise) |
| TP1 1.6 / 1.75R, TP2 2.0 / 3.0R, buffer 0.2 / 0.5 ATR, max stop $10 | All on the same plateau (PF 1.28–1.36 with the clean room); none better on both halves |

#### Year by year and robustness (V7.2 default)

| Period | Trades | Win rate | PF | Expectancy | Net | Max DD | Max losing streak |
|---|---|---|---|---|---|---|---|
| 2024 | 124 | 43.5% | 1.08 | +0.05R | +6.3R | 7.4R | 6 |
| 2025 | 154 | 47.4% | 1.41 | +0.23R | +34.7R | 7.8R | 4 |
| 2026 (to 4 Oct) | 42 | 50.0% | 1.60 | +0.31R | +13.0R | 6.4R | 6 |
| In-sample 2024-01 → 2025-06 | 197 | 45.2% | 1.21 | +0.12R | +23.9R | 7.4R | 6 |
| Out-of-sample 2025-07 → 2026-10 | 123 | 48.0% | 1.45 | +0.24R | +30.0R | 8.2R | 6 |

The median stop was $6.6 overall and $10 in 2026. 2026 has few trades because
the $15 cap rejects many structural stops when 5m ATR is $4–6.

#### TradingView validation — 5 October 2026

**Done:**
- Both scripts compiled and were saved as new versions. The editor text was verified byte-identical to the local files (SHA-256
  below). The Brain shows only its inherited numeric-to-boolean warnings.
- Execution's ten bridge inputs were set to Brain plots 0–9 through the chart
  API and confirmed after a reload. The layout was saved.

**Not done:**
- The trade-by-trade comparison (Pine logging harness) and chart screenshots.
  The Chrome window was behind your other applications, so TradingView
  stopped painting and loaded only 300 bars.
- I briefly brought the TradingView tab forward and then put your window and
  active tab back as they were.
- The layout on the server shows a **4h** interval. It was changed after my
  last save, so I left it as I found it.

**To finish:** switch the chart to 5m and keep the window visible. The
Execution table's *Chart results W/L* row then shows the live scoreboard. In
the port, the 11 Aug – 4 Oct window has only 2 trades with the clean room ON
(both TP2) and 35 with it OFF (16 W / 19 L), so the default setting will show
very few trades on the current chart.

#### Operating notes

- After any update to Execution + UI, remap the ten bridge inputs (1 → 10 in
  order) and confirm `All 10 sources connected`.
- No trades while the 4H and 1H disagree; the debug row
  "E6 direction (4H + 1H)" shows MIXED.
- `SL_TOO_WIDE` is common in high volatility. That is the $15 rule working,
  not a fault.
- Size positions so that a $15 stop is an acceptable loss. The typical stop is
  $5–10.

#### Fingerprints at that checkpoint

- Brain: 1,697 lines — SHA-256 `c3f89cea68f95d1f5dbd506c77486e9a71aba004e0390c341d22bd2270072082`
- Execution + UI: 298 lines — SHA-256 `bfabd5f6337f9064412b7e81445026f5711a68c42de5e292b3ca25cca40ed9f8`
- Visual Reference (unchanged): 2,474 lines — SHA-256 `c28ab486d9f59dbbb28dda13a61e5cef61484799b2cec3df9719258488fda225`
- Backtest: `backtest/v72_report.py` reproduces every table above;
  `backtest/render.py` draws the review charts.

### V7.1 — 5 October 2026 (superseded by V7.2)

V7.1 kept the AOI pipeline and used a market entry, an ATR stop (no dollar
cap), TP1 1R / TP2 2.5R and break-even after TP1. That gave a 55% win rate and
PF 1.34, but it broke the V7.2 rules (TP1 > 1.5R, SL ≤ $15, no break-even).
Its long-sample findings (retracement entries are adversely selected; fixed $
stops do not scale) still hold.

#### Summary

V7.1 came from a performance review on 2.75 years of XAUUSD 5-minute data
(1 Jan 2024 – 4 Oct 2026, 195,294 bars, 719 trading days). The data was run
through a bar-by-bar Python port of the scripts, which was cross-checked
against TradingView.

| Full period, $0.30 cost per trade | Original V7 | V7.1 |
|---|---|---|
| Trades | 57 (0.08 per day) | **462 (0.64 per day)** |
| Win rate (TP1 or TP2 reached) | 33.3% | **55.4%** |
| Profit factor | 0.96 | **1.34** |
| Expectancy per trade | −0.03R | **+0.16R** |
| Net result | −1.5R | **+72.9R** |
| Max drawdown | 11.9R | 11.1R |
| Max consecutive losses | 10 | 8 |

The original V7 was a breakeven system with almost no trades. Three
construction rules caused most of that: the retracement limit entry, the
fixed $10 stop, and the 1.5R-room rule. V7.1 replaces them, tightens the
confirmation, and relaxes two Engine-6 limits that only cost trades.

**On the 70–80% win-rate goal.** It is not achievable here without damaging
profitability. Measured on the same signals:

- TP1 at 0.5R gives a 69.7% win rate, but only half the profit of 1R
  (PF 1.21, +0.06R per trade).
- A blind entry at the zone touch, or a random entry, wins about 49%.
- The best tested signal set wins about 55% at 1R.

TP1 = 1R is the default because it gives the best balance of win rate and
profit. TP1 is an input, so a higher-win-rate profile can be chosen
knowingly. See *TP1 choice* below.

#### Files and roles

| File | Role |
|---|---|
| `XAUUSD Smart Trade Brain - Phase 5 + Engine 6 Builder.pine` | Producer: 5m structure, Phase-5 MTF zones, Engine-6 AOI decision, Engine-7 trade construction, ten hidden `BRIDGE_*` plots, Brain debug table |
| `XAUUSD Smart Trade Execution + UI.pine` | Consumer: bridge validation, live-trade lifecycle, win/loss accounting, Entry/SL/TP drawings, alerts, Execution table with chart results |
| `SMC ICT Scalping Master - Visual Reference.pine` | Visual reference only; not part of the decision chain; unchanged |
| `backtest/` | Python port + data tools that produced every number in this file (`backtest/README.md`) |

Both trading scripts are built for **XAUUSD on the 5-minute chart**. They do
not advance state on any other timeframe.

#### How the engines work together

```
4H structure ─┐
1H structure ─┼─► Phase 5 (confirmed, [1]-offset MTF data)
15m zones ────┤      Demand/Supply · SMC OB · FVG · Pivot S/R · EQH/EQL · 15m swing range
5m structure ─┘      5m internal/swing CHoCH & BOS · 9-indicator dashboard · BULB · ATR(89)
                               │
                               ▼
Engine 6 — AOI decision (Brain)
  candidates → filters → score ≥ 50 → lock best AOI → (retarget while untouched)
  → touch → within 36 bars: 5m structure break + displacement candle → READY
                               │
                               ▼
Engine 7 — trade construction (Brain)
  A = extreme since touch · entry = READY close · SL = A ∓ 0.5 ATR (≤ 4 ATR)
  · TP1 = 1R · TP2 = 2.5R                         │  ten BRIDGE_* plots
                               ▼
Execution + UI
  validate 10 channels → LIVE at READY close → TP1: 50% off, stop → entry
  → TP2 / break-even / SL  ·  W/L scoreboard
```

**Phase 5 (unchanged).** Confirmed 4H/1H structure (break direction, swing
high/low), previous D/W/M high/low, and the 15m families: Demand/Supply,
Bull/Bear OB, Bull/Bear FVG, Pivot S/R (nearest three each), three EQH/EQL and
the 15m swing range. Every value carries a one-bar `[1]` offset, so nothing
repaints.

**Engine 6 — AOI decision.** On each confirmed 5m bar:

1. *Candidates.* Demand, Bull OB and Pivot Support are long anchors; Supply,
   Bear OB and Pivot Resistance are short anchors. FVG only adds confluence.
2. *Filters.* A candidate is valid only when:
   - its geometry and metadata are valid and it is fresh;
   - it is on the correct side of price;
   - it was not touched in the current 15m window;
   - it is not in the consumed registry;
   - 4H and 1H are not both against it;
   - its near edge is within 6 × ATR(89).
3. *Score.* It must reach **50** (was 55):

   | Component | Points |
   |---|---|
   | Each source family on the AOI (D/S, OB, FVG, Pivot) | +10 each |
   | 4H agrees / disagrees | +15 / −15 |
   | 1H agrees / disagrees | +10 / −10 |
   | AOI midpoint in the 15m range: ideal extreme / favourable half / wrong half / wrong extreme | +10 / +5 / −5 / −10 |
   | Fresh, metadata, confirmed within 168 h, target liquidity exists | +15, +5, +5, +5 |

   The last row adds about +30 for every valid candidate, so 50 means:
   - a single-family AOI needs either 4H agreement (score 55), or 1H
     agreement plus a favourable-half location (score 45 + 5 = 50); or
   - a two-family AOI needs either the 4H or the 1H to agree.
4. *Lock and retarget.* The best score wins (ties: nearest, then newest). An
   untouched lock is replaced by a strictly better candidate, or an equally
   scored nearer one. The identity freezes at the first touch.
5. *Confirmation* (a later confirmed bar, within **36 bars = 3 h** of the
   touch; was 24). Both of these are required:
   - a 5m **structure break** in the AOI direction: an internal CHoCH, an
     internal continuation BOS, or a swing CHoCH;
   - a **displacement candle**: the confirming candle closes in the trade
     direction with a body of at least **0.3 × ATR(89)**.

   A pivot S/R "reaction" candle alone **no longer confirms**. Trend, the 6/9
   dashboard, BULB and session still only feed the 1–6 strength display.
6. *Lifecycle.*

   | Event | Release |
   |---|---|
   | 15m close beyond the AOI | `AOI_INVALIDATED` |
   | Target liquidity hit before READY | `OPPORTUNITY_GONE` |
   | Untouched 288 bars | `LOCK_EXPIRED` |
   | Touched, no confirmation in 36 bars | `CONFIRMATION_EXPIRED` |
   | READY evaluated by Engine 7 | `READY_CONSUMED` or `READY_REJECTED` (next bar) |

   The 24-bar READY retention is removed. It existed only to protect a pending
   limit order, and V7.1 has no pending stage, so Engine 6 searches again on
   the next bar. Every release except a retarget adds the AOI to the 250-entry
   consumed registry.

**Engine 7 — trade construction.** Runs once per READY.

1. *Reaction.* Walk the bars from touch to READY:
   - A = the extreme against the trade (the lowest low for a long);
   - B = the best extreme after A.

   The reaction must be ≥ 0.75 × ATR(89) (`WEAK_IMPULSE` otherwise).
2. *Entry* = the READY candle close: the trade is taken when confirmation
   prints.
3. *Stop* = A − 0.5 × ATR(89) for a long (A + 0.5 × ATR for a short), so it
   sits just beyond the swept reaction extreme. If that is more than
   **4 × ATR(89)** from the entry, the stop is placed at 4 × ATR instead.
4. *Targets* = entry ± 1R (TP1) and ± 2.5R (TP2), where R is the stop
   distance.
5. *Bridge.*
   - META entry code 1 = READY close.
   - TP codes = R multiple × 10 (10 and 25).
   - Reason codes: 1 valid, 2–6 impulse reasons, 7 `INVALID_RISK`.

**Execution + UI.**

1. *Acceptance.* A package is accepted only on its READY bar
   (`BRIDGE_EVAL_ID == time`), with Engine 6 in state 3, and after all ten
   channels validate:
   - the price ordering is coherent;
   - TP1/TP2 match the R multiples carried in META;
   - the impulse is coherent.
2. The trade is **live immediately** at the READY close. A READY that arrives
   while a trade is live is ignored (`IGNORED_READY_BUSY`).
3. *Management*, on every later confirmed bar:
   - The stop is checked first.
   - **TP1 hit:** the trade is a **WIN**. 50% is closed at +1R, the stop moves
     to entry, and the SL line is redrawn at entry ("Stop moved to entry (BE)").
   - **TP2 hit:** **WIN**, worth 0.5 × 1R + 0.5 × 2.5R = +1.75R.
   - **Back to entry after TP1:** still a **WIN** (`WIN_TP1_BE`, +0.5R). It is
     never labelled or counted as an SL hit.
   - **Stop before TP1:** **LOSS** (`LOSS_SL`, −1R).
   - If one candle touches the stop and a target, the stop is taken first
     (conservative).
4. *Display.* The table shows state, reason, last event, impulse, entry,
   SL/$ risk (and "now BE" after TP1), TP1/TP2 with R, and **Chart results
   W/L** (wins / losses, win rate, TP2 count, net R) over the loaded history.
   The last two closed trades stay drawn, faded.
5. *Alerts:* new trade, TP1 hit (win), closed as win, closed as loss.

#### Decision values (defaults)

| Area | Parameter | Value |
|---|---|---|
| Structure | Swing / internal swing length | 50 / 5 |
| 15m D/S | Min % change / Max % zone height | 0.2 / 0.05 |
| Phase 5 | 15m setup history / candidate cap | 500 / 100 |
| Engine 6 | Minimum score | **50** (was 55) |
| Engine 6 | Max lock distance | 6 × ATR(89) |
| Engine 6 | Max pre-touch lock / post-touch confirmation | 288 / **36** (was 24) bars |
| Engine 6 | Confirmation | internal CHoCH, internal BOS or swing CHoCH (**pivot reaction removed**) |
| Engine 6 | Minimum confirmation body | **0.3 × ATR(89)** (new) |
| Engine 6 | READY retention | **released next bar** (was 24 bars) |
| Engine 7 | Minimum reaction (A→B) | 0.75 × ATR(89) |
| Engine 7 | Entry | **READY close** (was F38.2/F61.8 limit) |
| Engine 7 | Stop | **A ∓ 0.5 × ATR(89), max 4 × ATR(89)** (was fixed $10) |
| Engine 7 | TP1 / TP2 | **1R / 2.5R** (was nearest structure ≥ 1.5R / next structure) |
| Execution | Management | **50% at TP1, stop to entry**, rest to TP2 |
| Execution | Pending stage | **removed** |

In 2026 trades the stop was $16 / $20 / $26 at the 25th / 50th / 75th
percentile. The 4 ATR cap is about $17–23 at 2026 volatility (ATR(89) $4.2–5.7). Size
positions by risk (R), not by a fixed lot.

#### Changes and why

| # | Change | Defect / reason | Evidence (2.75 years) |
|---|---|---|---|
| 1 | Entry at the READY close instead of F38.2/F61.8 limits | **Adverse selection.** A limit fills mainly when the reaction is failing; strong reactions leave without filling. 35 of 109 old packages were cancelled because TP1 traded first | Same READY signals, stop beyond A, TP1 1R. Per trade, in-sample / out-of-sample: READY close −0.05…−0.11R / +0.07…+0.17R; F38.2 −0.16…−0.28R / −0.07…+0.13R; F61.8 −0.30…−0.52R / −0.06…−0.24R |
| 2 | Stop = A ∓ 0.5 ATR, capped at 4 ATR (was fixed $10) | ATR(89) rose from about $1.1 (Jan 2024) to about $5.7 (2026). $10 was 9 ATR in early 2024 and 2 ATR in 2026, so the same rule was a different system each year. In 2024 it rejected nearly every setup (9 trades in 18 months) | Stop buffer 0.25–1.0 ATR: all variants profitable. Cap 2 ATR: PF 1.07/1.03; 3 ATR: 1.18/1.12; 4 ATR: 1.32/1.37 (in/out-of-sample) |
| 3 | TP1 = 1R, TP2 = 2.5R (was nearest structure ≥ 1.5R) | The 1.5R-room rule was the biggest rejection, and the READYs it rejected did *better* (OOS +0.19R) than those it accepted (−0.01R). Re-adding a room filter scored PF 1.6–1.9 in-sample but 0.57–0.86 out-of-sample: overfit | TP2 2.0 / 2.5 / 3.0R all positive in every year; 2.5R is the middle |
| 4 | Pivot-reaction confirmation removed | A single reaction candle at a pivot zone is not a structure shift; it was the weakest confirmation group | With market entry: PF 0.96 → 1.16 in-sample, 1.15 → 1.46 out-of-sample, max DD 16.6R → 7.6R |
| 5 | Displacement body ≥ 0.3 ATR on the confirming candle | Filters drift breaks of tiny internal swings | Body ≥ 0 / 0.15 / 0.3 / 0.5 / 0.75 ATR: expectancy rises steadily in both halves (in-sample +0.075 → +0.138R) while trades fall; 0.3 keeps volume |
| 6 | Confirmation window 24 → 36 bars | Valid confirmations 2–3 h after the touch were discarded | +15–20% trades; PF 1.27 → 1.28 in-sample, 1.62 → 1.54 out-of-sample |
| 7 | Minimum score 55 → 50 | Admits single-family AOIs with 1H agreement in the favourable half | Combined with #6: +44% trades; PF 1.27 → 1.34 in-sample, 1.62 → 1.45 out-of-sample; total +55R → +73R |
| 8 | READY released next bar (retention removed) | The 24-bar hold only protected a pending order, which no longer exists; it blocked new setups for 2 h | Retention 24 vs 1: in-sample PF 1.19 vs 1.25 |
| 9 | Execution: live at READY close; 50% at TP1 + stop to entry; WIN/LOSS accounting; scoreboard | Your rule: TP1 or TP2 = win, SL = loss, and TP1 followed by a return to entry is not an SL hit. Partial + break-even makes every "win" profitable (≥ +0.5R) | Matches the backtest model exactly |
| 10 | Removed the now-unused 5m pivot-reaction engine from the Brain | Dead code after #4 | −137 lines; the pivot inputs remain because the 15m pivot zones still use them |

#### Tested and rejected

| Idea | Result |
|---|---|
| Tracking 2–5 AOIs at once (instead of the single best lock) | More trades (0.8/day) but PF fell to 1.01–1.10. The extra trades come from lower-ranked zones, so the single best-score lock is a real quality filter |
| Requiring TP1 room to the nearest opposing structure (0.5–1.0R) | In-sample PF 1.64–1.89, out-of-sample PF 0.57–0.86. Overfit, and it removes about 65% of trades |
| Entry at the zone touch (no confirmation) | −0.07 to −0.27R per trade in-sample, −0.18 to +0.02R out-of-sample |
| Session / hour filters | Hour buckets flip sign between periods (noise) |
| Requiring 4H **and** 1H agreement | Same per-trade result, 25% fewer trades |
| Rejecting stops wider than 4 / 6 ATR | Fewer trades; in-sample worse (cap preferred) |
| Keeping the stop at break-even off (original stop after TP1) | Similar PF, contradicts the "no SL after TP1" rule |
| Removing `OPPORTUNITY_GONE` | Mixed (in-sample better, out-of-sample worse); kept |
| Lock distance 3 or 10 ATR; lock lifetime 96 bars; no retarget | All worse than the current 6 ATR / 288 bars / retarget |
| Minimum reaction 0 / 1.5 / 2.5 ATR | No meaningful effect; 0.75 kept |

#### Backtest method

- **Data.** HistData.com XAUUSD M1 (sourced from Dukascopy, bid) for Jan 2024
  – Sep 2026, plus Dukascopy for 1–4 Oct 2026. HistData times are UTC-5, or
  UTC-4 while London is on summer time. This was verified to the minute
  against Dukascopy UTC data, and against TradingView OANDA closes (about $0.3
  feed offset).
- **Bars.** Built like TradingView OANDA: 4H and daily bars aligned to the
  17:00 New York session start; weekly and monthly bars from trading dates.
- **Port.** `backtest/` re-implements Phase 5, Engine 6, Engine 7 and
  Execution bar by bar, including the `[1]` MTF offsets, swing and pivot
  definitions, freshness, consumed registry and stop-first fills.
- **Costs and accounting.** $0.30 per trade (spread and slippage), charged in
  R. Wins and losses use the Execution model: 50% at TP1, stop to entry.
- **Overfitting control.**
  - Every design choice was made on the in-sample period (2024-01 → 2025-06)
    and checked on the out-of-sample period (2025-07 → 2026-10).
  - It was also checked per calendar year and against neighbouring parameter
    values.
  - Only changes with a mechanical reason that held in both periods were kept.
  - About 60 variants were examined; the published configuration sits on a
    plateau where every neighbour is also profitable.

#### Results (V7.1 defaults)

| Period | Trades (per day) | Win rate | PF | Expectancy | Net | Max DD |
|---|---|---|---|---|---|---|
| In-sample 2024-01 → 2025-06 | 224 (0.57) | 54.9% | 1.32 | +0.149R | +33.4R | 11.1R |
| Out-of-sample 2025-07 → 2026-10 | 238 (0.72) | 55.9% | 1.37 | +0.166R | +39.5R | 9.5R |
| 2024 | 134 | 56.0% | 1.35 | +0.162R | +21.8R | 7.0R |
| 2025 | 182 | 52.7% | 1.25 | +0.121R | +21.9R | 11.1R |
| 2026 (to 4 Oct) | 146 | 58.2% | 1.47 | +0.200R | +29.2R | 5.1R |
| Longs / shorts | 320 / 142 | 54.7% / 57.0% | 1.36 / 1.29 | +0.17R / +0.13R | | |

**Trade profile:**
- Outcomes: 132 TP2 (+1.75R), 124 TP1 then break-even (+0.5R), 206 stops (−1R).
- Trades took place on 352 of 719 trading days (49%).
- Median holding time: 3.9 h.
- Zero cost: PF 1.42. $0.50 cost: PF 1.29.

#### TP1 choice (win rate vs profit)

The signals are the same in every row; only TP1 changes (TP2 2.5R, 50%
partial, stop to entry).

| TP1 | Trades | Win rate | PF | Expectancy | Net | Max DD |
|---|---|---|---|---|---|---|
| 0.5R | 482 | **69.7%** | 1.21 | +0.064R | +30.9R | 9.1R |
| 0.75R | 470 | 62.6% | 1.34 | +0.130R | +61.2R | 8.8R |
| **1.0R (default)** | 462 | 55.4% | 1.34 | +0.158R | +72.9R | 11.1R |
| 1.5R | 442 | 48.2% | 1.42 | +0.225R | +99.6R | 10.4R |

Lowering TP1 buys win rate with profit. 0.75R keeps the same PF with a 63%
win rate, but earns about 16% less. 1.5R earns the most, but loses more often
than it wins. 1R is the balanced default.

#### TradingView validation — 5 October 2026

- **Deployment.** Both scripts compiled and were saved: Brain version 8,
  Execution version 9. The saved text is byte-identical to the local files
  (SHA-256 below). The Brain shows only its inherited numeric-to-boolean
  warnings.
- **Inputs.** The new defaults are live on the chart instance (score 50,
  confirmation 36, body 0.3, stop buffer 0.5, cap 4, TP 1/2.5).
- **Bridge.** Execution's ten inputs were remapped to Brain plots 0–9 in
  order, and the table shows `All 10 sources connected`. The layout was saved
  with no unsaved changes.
- **Chart scoreboard** over the loaded OANDA history (11 Aug – 5 Oct 2026):
  **18 W / 18 L, 8 TP2, +1.0R** (no costs).
- **Harness check.** A private scratch copy of the new Brain with an
  identical lifecycle logger (`HARNESS Brain baseline`, removed from the chart
  afterwards) gave the same 18/18/8/+1.0R and 39 READY, all valid. So the
  Brain → bridge → Execution chain reproduces the intended logic.
- **Port vs TradingView,** same window: 36 vs 36 trades; 20 W / 16 L vs
  18 W / 18 L. About three quarters of the trades match one-to-one (same time,
  side and outcome; entries within cents); the rest differ because of small
  OANDA vs Dukascopy price differences.
- **Context.** These 8 weeks (mostly September 2026) were a weak stretch for
  the system: +1R to +5R over 36 trades, against a long-run +0.16R per trade.
  That is within normal variance; the backtest shows quarters with flat or
  negative results in every year.

#### Operating notes

- After any update to Execution + UI, remap the ten bridge inputs (1 → 10 in
  order) and confirm `All 10 sources connected`.
- After updating the Brain, check that the chart instance kept the intended
  input values.
- Size every trade by R. Stop distance varies with volatility (about
  $15–20 typical in Oct 2026).
- The chart scoreboard covers only the bars TradingView loaded (~50 days). The
  `backtest/` folder is the reference for long-run statistics.
- Expect losing streaks: the longest was 8 losses in a row, and the maximum
  drawdown was 11.1R over 2.75 years.

#### Fingerprints at that checkpoint

- Brain: 2,305 lines — SHA-256 `6b6fbf694a39e7052c68a1e9f2880f3fc40f1d16fcecf81d3fce946188054233`
- Execution + UI: 307 lines — SHA-256 `448b7dd118a4f0caab753c4ce216140deb0bcbcdb5d89ca7d871d83f9c570fb8`
- Visual Reference (unchanged): 2,474 lines — SHA-256 `c28ab486d9f59dbbb28dda13a61e5cef61484799b2cec3df9719258488fda225`
- Static checks: 10 `BRIDGE_*` plots in the Brain, 10 `input.source` channels in
  Execution, balanced `()`, `[]`, `{}` in both.

### Earlier review — 5 October 2026 (logic review before V7.1; superseded)

The review below ran earlier the same day. Its lock-distance cap, pre-touch
retarget, AOI-midpoint location, internal-BOS confirmation, impulse-sequence
fix and D/S 0.2% change remain in V7.1. Its Engine-7 policy (F38.2/F61.8
entries, fixed $10 stop, 1.5R room) and its pending-order lifecycle were
replaced by V7.1 after the long-sample backtest.

#### Files and roles

| File | Role |
|---|---|
| `XAUUSD Smart Trade Brain - Phase 5 + Engine 6 Builder.pine` | Producer: market structure, Phase-5 MTF zones, Engine-6 AOI decision, Engine-7 package construction, ten hidden `BRIDGE_*` plots, Brain debug table |
| `XAUUSD Smart Trade Execution + UI.pine` | Consumer: bridge validation, pending/live lifecycle, Entry/SL/TP drawings, alerts, Execution table |
| `SMC ICT Scalping Master - Visual Reference.pine` | Visual reference only (chart-timeframe drawings and the nine-row dashboard). Not part of the decision chain; unchanged in this review |

Both trading scripts are built for **XAUUSD on the 5-minute chart**. Both refuse
to advance state on any other timeframe.

#### How the engines work together

```
4H structure ─┐
1H structure ─┼─► Phase 5 (confirmed, [1]-offset MTF data)
15m zones ────┤      Demand/Supply · SMC OB · FVG · Pivot S/R · EQH/EQL · 15m swing range
5m structure ─┘      5m CHoCH/BOS · pivot reaction · 9-indicator dashboard · BULB · ATR(89)
                               │
                               ▼
Engine 6 — AOI decision (Brain)
  candidates → filters → score ≥ 55 → lock → (retarget while untouched) → touch
  → later-bar 5m confirmation → READY_FOR_PHASE7
                               │
                               ▼
Engine 7 — package construction (Brain)
  touch→READY impulse A/B → F38.2 / F61.8 entry → fixed $10 SL → TP1 ≥ 1.5R → TP2
                               │  ten BRIDGE_* plots
                               ▼
Execution + UI
  validate all 10 channels → PENDING (≤ 24 bars) → LIVE → TP1 / TP2 / SL
```

**Phase 5 (data only).** It collects confirmed 4H/1H structure (break
direction, swing high/low) and previous D/W/M highs/lows. The 15m request
(`calc_bars_count = 500`) publishes the nearest three active candidates per
family. Those families are Demand, Supply, Bull/Bear OB, Bull/Bear FVG and
Pivot Support/Resistance, plus three EQH/EQL levels and the 15m swing range.
Every 15m value carries a one-bar `[1]` offset, so nothing repaints. Demand and
Supply zones are deleted on their first touch. OB, FVG and pivot zones carry a
`Fresh` flag that clears on first touch.

**Engine 6 (AOI decision).** On each confirmed 5m bar:

1. *Candidates.* Demand, Bull OB and Pivot Support are long anchors; Supply,
   Bear OB and Pivot Resistance are short anchors (3 of each). FVG is never an
   anchor. It only adds a confluence family when it overlaps the anchor.
2. *Filters.* A candidate is valid only when all of these hold:
   - geometry and metadata are valid, and the zone is still fresh;
   - it sits on the correct side of price;
   - it was not touched inside the current 15m window;
   - it is not in the consumed registry;
   - 4H and 1H are not both against it;
   - **its near edge is within 6 × 5m ATR(89) of the close (new).**
3. *Score* — must reach **55**:

   | Component | Points |
   |---|---|
   | Each source family overlapping the AOI (D/S, OB, FVG, Pivot) | +10 each |
   | 4H agrees / disagrees | +15 / −15 |
   | 1H agrees / disagrees | +10 / −10 |
   | AOI location in the 15m range — ideal extreme / favourable half / wrong half / wrong extreme (**now measured at the AOI midpoint**) | +10 / +5 / −5 / −10 |
   | Fresh, complete metadata, confirmed within 168 h, target liquidity exists | +15, +5, +5, +5 |

   The last row is effectively constant (+30) for every valid candidate,
   because the filters already require freshness and metadata. The variable
   part is sources + context + location. With one source family, the threshold
   therefore needs full 4H+1H agreement, or 4H agreement with an AOI in the
   favourable half plus a second family. A pullback against the 1H trend needs
   confluence.
4. *Lock.* The best score wins; ties go to the nearest, then the most recently
   confirmed. While the lock is **untouched** (state 1), a candidate with a
   strictly higher score, or an equal score and nearer to price, replaces it
   (**new, `RETARGETED`**). The replaced zone is not consumed. After the first
   touch the identity is frozen.
5. *Lifecycle.*

   | Event | Release |
   |---|---|
   | 15m close beyond the AOI | `AOI_INVALIDATED` (state 4 for one bar; cancels a pending package) |
   | Target liquidity hit before READY | `OPPORTUNITY_GONE` |
   | Untouched for 288 bars (24 h) | `LOCK_EXPIRED` |
   | Touched, no confirmation within 24 bars (2 h) | `CONFIRMATION_EXPIRED` |
   | Engine 7 rejected the READY | `READY_REJECTED` (next bar) |
   | Accepted READY older than 24 bars | `READY_RETENTION_EXPIRED` |

   Every terminal release except a retarget adds side + anchor + origin to the
   250-entry consumed registry, so the same dead setup is never re-locked.
6. *Confirmation* (a later confirmed 5m bar after the touch). One of these is
   required, in the AOI direction:
   - internal CHoCH;
   - **internal continuation BOS (new)**;
   - swing CHoCH;
   - pivot S/R reaction candle.

   Trend agreement, the 6-of-9 dashboard majority, BULB extreme and an active
   session only add to the 1–6 strength score. They never gate.

**Engine 7 (package construction, Brain).** Runs once per READY timestamp.

1. *Impulse.* Walk the bars from touch to READY:
   - A = the extreme against the trade (low for a long);
   - B = the best extreme in the trade direction at or after A;
   - **a candle that closed in the trade direction may supply both A and B (new).**

   The impulse must be ≥ 0.75 × 5m ATR(89).
2. *Entries.* F38.2 = B − 0.382·(B−A) and F61.8 = B − 0.618·(B−A) (mirrored for
   shorts). The entry must still be pending at the READY close.
3. *Stop.* Fixed **$10.00** from entry. It must sit **beyond both the impulse
   origin A and the AOI 50% mean threshold (new)**; failure is reported as
   `FIXED_SL_INSIDE_STRUCTURE`.
4. *Targets.* The pool is EQH/EQL, PDH/PDL, PWH/PWL, PMH/PML, the 15m swing,
   the 4H swing, and opposing D/S, OB, FVG and pivot S/R near edges. A target
   must lie beyond both the entry and the READY candle. Liquidity swept inside
   the current 15m window is excluded. TP1 is the **nearest** target and must
   be at least **1.5R** ($15); any nearer opposing structure rejects the
   setup. TP2 is the next farther target.
5. *Choice.* If both entries are valid, the one with the larger TP2 R wins,
   then the larger TP1 R. The result is published on the bridge.

**Execution + UI.**

1. It accepts a package only on the exact READY bar (`BRIDGE_EVAL_ID == time`),
   and only after validating all ten channels:
   - the stop is exactly $10;
   - TP1 is at least 1.5R and TP2 is farther;
   - price and impulse ordering are coherent.
2. A pending order is cancelled when:
   - the bridge disconnects;
   - the parent AOI is invalidated;
   - 24 bars pass, or TP1 trades before the entry fills (`MISSED_ENTRY`).
3. A live trade checks the stop first, then TP2, then TP1, on each later bar.
4. **Fill candle (new).** When the entry candle also touches SL or a target,
   the trade is resolved conservatively on that bar:
   - a touched stop closes it (`STOP_ON_FILL_BAR`);
   - a touched target is not credited until a later bar.

   Previously this created a terminal `AMBIGUOUS_FILL` state that blocked every
   later signal.

#### Decision values (defaults)

| Area | Parameter | Value |
|---|---|---|
| Structure | Swing length / internal swing | 50 / 5 |
| 15m D/S | Min % change / Max % zone height | **0.2** (was 0.05) / 0.05 |
| 15m OB | Filter / scan cap | ATR(200) × 2 / 499 bars |
| 15m pivots | Left / right / ATR len / width | 20 / 15 / 30 / 0.5 ATR |
| EQH/EQL | Confirm bars / threshold | 3 / 0.1 × ATR(200) |
| Phase 5 | 15m setup history / candidate cap | 500 / 100 |
| Engine 6 | Minimum score | 55 |
| Engine 6 | Max lock distance | **6.0 × 5m ATR(89)** (new) |
| Engine 6 | Max pre-touch lock / post-touch confirm / READY retention | 288 / 24 / 24 bars |
| Engine 6 | Dashboard majority (strength only) | 6 of 9 |
| Engine 7 | Min impulse | 0.75 × 5m ATR(89) |
| Engine 7 | Fixed stop / min TP1 | $10.00 / 1.5R |
| Execution | Max pending bars | 24 (keep equal to READY retention) |

#### Changes in this review and why

Each change was made only after source inspection and, where possible,
measurement in TradingView.

| # | Change | Defect / reason | Evidence |
|---|---|---|---|
| 1 | Engine 7 impulse may start and end on one directional candle | `INVALID_IMPULSE_SEQUENCE` whenever the READY reaction candle itself printed the sweep low — the most common reaction shape | 8 of 20 READY rejections in the baseline → 0 |
| 2 | Stop must clear impulse A and the AOI 50% level (was: the whole AOI) | A fixed $10 stop could never clear tall 15m OBs, and the old rule ignored the swept reaction extreme (a stop above A was legal) | First fixed run: stop rejections 11 → 9 while READY rose; a stop inside the swept range is now always rejected |
| 3 | Engine 6 lock distance cap (6 × 5m ATR) | Engine 6 locked an AOI 11 ATR ($50) below price for up to 24 h, blocking every nearer setup | Avg lock distance 3.0–3.4 ATR afterwards |
| 4 | Pre-touch retargeting | Engine 6 was locked ~73–80% of the time; a single untouched lock hid better/nearer setups | Touches 70 → 109, READY 28 → 43, avg bars to touch 39 → 24 |
| 5 | Location scored at the AOI midpoint (was current close) | A discount demand AOI was penalised −10 when price was in premium — the classic pullback buy | Logic fix |
| 6 | Internal BOS accepted as post-touch confirmation | A demand that held without internal structure turning bearish could only confirm via a rare pivot reaction | 3 of 43 READY used it |
| 7 | D/S min change 0.05% → 0.2% | 0.05% ≈ $2 on gold — a quarter of one 15m candle — so micro "zones" were everywhere, acting as weak anchors and blocking TP1. The original author's tooltip suggests 0.4% for forex 15m; 0.2% ≈ 1 × 15m ATR on XAUUSD | Post-touch invalidations 51 → 40; supply blockers 10 → 4 |
| 8 | Execution: ambiguous fill resolved on the fill bar | `AMBIGUOUS_FILL` (state 3) had no exit, so one ambiguous candle froze Execution forever (`IGNORED_READY_BUSY`) | Code-path fix; preview-disabled drawing moved into the fill step |
| 9 | Reason renamed `FIXED_SL_DOES_NOT_CLEAR_AOI` → `FIXED_SL_INSIDE_STRUCTURE` (code 2 unchanged) | Matches the new stop rule; both scripts updated | Decoded live through the bridge |

**Tested and rejected (left unchanged):**

- *Minimum score 55 → 50.* It only kept the engine locked longer (valid
  packages 10 → 9). The bottleneck was lock occupancy, not score.
- *D/S max zone height 0.05 → 0.1.* Bit-for-bit identical results; the cap
  practically never binds.
- *FVG as target-but-not-blocker for the 1.5R room check.* It added two trades
  and both were stopped out. That sample is too small to prove anything, but an
  opposing FVG commonly acts as resistance, so the original rule was kept.

**Deliberately kept as policy:**

- the fixed $10 stop and the 1.5R TP1 floor (the largest remaining rejection,
  `NO_1_5R_ROOM`, is a real nearby opposing zone in every measured case);
- 15m-close invalidation;
- the 4H/1H weights;
- the 288/24/24-bar lifecycle;
- the session context as non-gating.

#### TradingView validation — 5 October 2026

**Environment:**
- OANDA:XAUUSD, 5-minute chart, UTC+7.
- Price about 4,160; 5m ATR(89) about 4.4.

**Method:**
- A scratch-only harness copy of the Brain (saved privately as
  `HARNESS Brain baseline`, never part of the maintained files) appended
  counters for every lock, retarget, touch, READY, release reason and Engine-7
  rejection.
- It also simulated the Execution lifecycle, using the same rules and the
  conservative fill-bar resolution.
- The 15m history was raised to 2,000 bars for the test only, which gave
  56.4 days (9 Aug – 5 Oct 2026, 11,136 five-minute bars).

| Stage (56.4 days) | Original v7 | Final |
|---|---|---|
| AOI locks (long/short) | 107 (99/8) | 141 (135/6) + 88 retargets |
| Touches · avg bars to touch | 63 · 41.8 | 109 · 23.9 |
| READY | 25 | 43 |
| Valid Engine-7 packages | **5** | **12** |
| Engine-7 rejections (F38.2 and F61.8 counted separately) | 8 impulse-sequence, 11 stop-vs-AOI, 8 no-1.5R-room | 0 impulse-sequence, 18 stop-inside-structure, 31 no-1.5R-room |
| Simulated pending → cancelled (missed/expired) | 3 | 2 |
| Simulated fills: stop / stop after TP1 / TP1+TP2 | 2 / 0 / 0 | 6 / 1 / 3 |
| Avg TP1 R / TP2 R | 2.40 / 3.57 | 2.07 / 2.80 |

That is about 0.3 packages per trading day. The final build is materially less
strict than v7 (about 2.4 times the packages), without loosening any risk rule.
It is still selective, because the remaining filters are deliberate policy
(fixed $10 stop, 1.5R room, 15m-close invalidation). Ten simulated fills are
far too few to estimate a win rate or expectancy; the outcome rows are there
for sanity only, not as performance evidence.

**Deployment check on the live chart:**
- Both maintained scripts compiled and were saved. The saved TradingView text
  was byte-identical to the local files (SHA-256 below).
- The Brain immediately showed `LOCKED_WAIT_TOUCH | RETARGETED`. It moved from
  the stale Bull OB at 4111–4115 (about $50 below price) to a Demand AOI at
  4135–4138, and the D/S input showed 0.2.
- Saving Execution reset its ten source inputs to `close`. All ten were
  remapped to the identically named Brain plots and the layout was saved. The
  table then showed `All 10 sources connected`.
- The current evaluation decoded through the bridge as `READY_REJECTED` with
  "F38.2: FIXED_SL_INSIDE_STRUCTURE / F61.8: NO_1_5R_ROOM", which confirms the
  renamed reason code end to end.
- No compile error and no runtime-error badge on either script. The Brain still
  shows only its inherited numeric-to-boolean warnings.
- A live package fill, TP or SL event was not observed during this session.
  The fill-bar resolution is validated by code review and the harness
  simulation, not by a live fill.

**Operating notes:**
- After any update to Execution + UI, remap the ten bridge inputs and confirm
  `All 10 sources connected`.
- After updating the Brain, check the existing chart instance's
  `D/S Min % change` input; it should read 0.2.
- The Brain is close to Pine's 80,000-token compile limit. A diagnostic that
  called the candidate builder 18 extra times failed at 90,784 tokens, so keep
  future additions lean.

#### Fingerprints at that checkpoint

- Brain: 2,603 lines — SHA-256 `b9d09af96769ed19d2a53422ca22aad68d523baafed2e19fd7a53a6449d8c869`
- Execution + UI: 434 lines — SHA-256 `112c63cbff9f2518e43103fdf47fa75ca8b0d243133c65fc59d32d9685fc264d`
- Visual Reference (unchanged): 2,474 lines — SHA-256 `c28ab486d9f59dbbb28dda13a61e5cef61484799b2cec3df9719258488fda225`
- Static checks: 10 `BRIDGE_*` plots in the Brain, 10 `input.source` channels in
  Execution, balanced `()`, `[]`, `{}` in both.

### v7 Replay-Memory Split

### Result

The v7 combined baseline was split into two indicators:

1. `XAUUSD Smart Trade Brain - Phase 5 + Engine 6 Builder.pine`
2. `XAUUSD Smart Trade Execution + UI.pine`

The split follows the reviewed recommendation, but the split by itself was not sufficient. The first split build still produced TradingView's `Memory limits exceeded` runtime error during Bar Replay. Removing the original blanket `max_bars_back=500` declaration reduced broad history allocation and allowed a short replay check to pass, but the later hardened build still reproduced the same runtime error after approximately 120 five-minute replay steps.

The remaining failure was traced to the 15-minute Phase 5 request returning a nested object tree on every requested bar: one `Phase5SetupState`, 24 `Phase5ZoneCandidate` objects, and 6 `Phase5LiquidityCandidate` objects. TradingView retained enough of those requested-context objects during replay to exhaust the script's memory allowance.

The final build transports the same decision-bearing state as a 117-element primitive tuple instead. Pine's tuple limit is respected, the confirmed `[1]` offsets are unchanged, and the expensive request remains deliberately bounded by:

```pine
calc_bars_count=phase5SetupHistoryBars
```

The default `phase5SetupHistoryBars` remains 500. Existing explicit scan limits, candidate registries, detectors, freshness rules, AOI decisions, impulse construction, and lifecycle rules also remain unchanged.

### Removed superseded combined baseline

After the split indicators were saved and verified in TradingView, the unused
combined v7 source was removed from the `v7` working set:

- Removed file: `XAUUSD Smart Trade Core - Phase 5.pine`
- Last SHA-256: `db03a0ddaedf3f2c1c35a247417a7bda67912bb9930d2ba43a37bf79b698cccb`
- Last line count: 2,626

The split Brain and Execution + UI files are now the maintained implementation.
Earlier version folders and this fingerprint remain available for comparison;
the removed local file was moved to the macOS Trash for recoverability.

### Split responsibility

#### Brain / producer

The Brain owns calculation only:

- Lean Core structure, pivot reaction state, dashboard, BULB, and ATR context
- Phase 5 confirmed multi-timeframe collection and normalization
- Engine 6 scoring, AOI selection, locking, touch, confirmation, and handoff
- Engine 7 impulse construction and F38.2/F61.8 candidate evaluation
- The existing Phase 5 + Engine 6 debug table
- Ten hidden bridge outputs

It does not own Engine 7 trade lifecycle drawings, history, or alerts.

#### Execution + UI / consumer

The UI owns presentation and lifecycle only:

- Bridge validation and metadata decoding
- Pending-entry, live-trade, cancellation, SL, TP1, and TP2 lifecycle
- Entry, SL, TP1, and TP2 plots/drawings
- Signal history and status tables
- Alerts

It does not recalculate Phase 5, Engine 6, or Engine 7 construction logic.

### Bridge mapping

Add the Brain to the chart first. Add the Execution + UI indicator second, then connect each UI input to the matching Brain plot:

| Execution + UI input | Brain output |
|---|---|
| Bridge evaluation ID | `BRIDGE_EVAL_ID` |
| Bridge metadata | `BRIDGE_META` |
| Bridge entry | `BRIDGE_ENTRY` |
| Bridge stop loss | `BRIDGE_SL` |
| Bridge TP1 | `BRIDGE_TP1` |
| Bridge TP2 | `BRIDGE_TP2` |
| Bridge Engine 6 state | `BRIDGE_E6_STATE` |
| Bridge impulse A | `BRIDGE_IMPULSE_A` |
| Bridge impulse B | `BRIDGE_IMPULSE_B` |
| Bridge impulse strength | `BRIDGE_IMPULSE_STRENGTH` |

The current UI status must show `All 10 sources connected`. Keep both indicators on the same XAUUSD 5-minute chart.

### Logic-preservation audit

The split does not change the trading policy:

- Phase 5 AOI families remain distinct: Demand/Supply, SMC Order Blocks, FVGs, Pivot S/R, and EQH/EQL liquidity.
- The confirmed 4H, 1H, 15m, and 5m hierarchy is unchanged.
- Engine 6 source masks, weights, score threshold, opposite-context rejection, lock identity, touch rules, invalidation, and post-touch confirmation are unchanged.
- FVG remains supporting confluence and is not promoted to an AOI anchor.
- Engine 7 still evaluates the touch-to-READY impulse, F38.2 and F61.8 entries, the fixed 10.0 XAU stop, minimum 1.5R TP1 room, and a farther TP2.
- Lifecycle ordering remains unchanged so a pending entry can be filled before same-bar TP/SL checks, matching the combined baseline.
- Plot prices travel in dedicated bridge channels. The packed metadata channel transports classifications only, avoiding price precision loss.

Memory-specific source changes are limited to removal of the blanket `max_bars_back=500` declaration and replacement of the nested requested-context UDT transport with primitive series. The omitted transport fields were FVG and EQH/EQL origin/confirmation timestamps that had compatibility aliases but no reads in scoring, AOI selection, target selection, bridge plots, alerts, or debug output. FVG boundaries/freshness and all EQH/EQL levels remain transported and used exactly as before.

### Earlier TradingView validation checkpoint

Environment: OANDA:XAUUSD, 5-minute chart, Bar Replay on 2 October 2026.

- Brain compiled and updated successfully.
- Execution + UI compiled and updated successfully.
- All ten UI sources were connected to their matching Brain outputs.
- The UI reported `Bridge connected` and consumed real bridge values.
- Entry, stop, TP1, TP2, reason, and lifecycle status updated from the producer.
- Replay advanced from approximately 17:50 to 19:20, about eighteen 5-minute bars, without the Pine `Memory limits exceeded` runtime error.
- The prior split build containing blanket `max_bars_back=500` failed immediately in the same replay workflow.

The Brain compiler still reports the pre-existing numeric-to-boolean conversion warnings inherited from the baseline structure checks. They are warnings, not compile errors, and were not rewritten because doing so could alter behavior.

### Validation boundary

The current validation is a 520-bar sequential replay regression across more than one trading day and more than four times the former failure point. It is materially stronger than the earlier 18-bar checkpoint, but it is not a statistical trade-outcome parity study across every symbol, timeframe, account plan, and chart-history depth. The validated configuration is OANDA:XAUUSD on the required 5-minute chart with the default 500-bar setup request.

### Earlier split file fingerprints

- Brain SHA-256: `72aa8c245b0fb4ac7736cd53c88feae6d9fddd61b6cf72908a782494e2033af1`
- Execution + UI SHA-256: `54196eeeb4a4cf941b15d2858676c5ee65c7f0d929759ed5fa62eebf9949403d`

### TradingView upload check — 4 October 2026

The maintained v7 chart set is:

1. `SMC & ICT & Indicators + Scalping Master — Visual Reference`
2. `XAUUSD Smart Trade Brain — Phase 5 + Engine 6 Builder`
3. `XAUUSD Smart Trade Execution + UI`

On OANDA:XAUUSD 5-minute, the Brain and Execution + UI were present with all
ten UI inputs mapped to the matching Brain outputs. The Visual Reference source
was saved as `SMC ICT Scalping Master - Visual Reference v7`, compiled, and
updated on the chart under its declared indicator title. Its compiler output
contained the inherited numeric-to-boolean and calculation-consistency warnings
but no compile error.

### Review-driven bridge hardening — 4 October 2026

An external review was checked claim-by-claim against the current split files
and the frozen combined-source fingerprint. The reported live disconnection was
not reproduced: the inspected TradingView layout had all ten UI inputs mapped.
The following source-level bridge weaknesses were confirmed and repaired:

- The Brain now publishes distinct idle sentinels on the non-META bridge
  channels. Execution validates all ten mapped sources rather than treating the
  META numeric range alone as proof of connection.
- A valid package is accepted only when the evaluation ID is a plausible 5m
  timestamp, Engine 6 is `READY_FOR_PHASE7`, side/entry/target classifications
  are valid, the stop is exactly 10.0 away within tick tolerance, TP1 has at
  least 1.5R room, TP2 is farther, and LONG/SHORT price and impulse ordering is
  coherent.
- A pending package now cancels fail-safe with `BRIDGE_DISCONNECTED` if any
  mapped source becomes invalid. Parent invalidation remains authoritative when
  the bridge is healthy.
- F38.2 and F61.8 rejection reasons are encoded separately in META and decoded
  back into the exact pair instead of collapsing to `NO_VALID_RETRACEMENT`.
- Execution reconstructs `ImpulseSize = abs(B - A)` and
  `ImpulseATR = ImpulseSize / ImpulseStrength` without adding bridge plots.
- Execution consumes a READY evaluation only on the original 5-minute bar
  where `BRIDGE_EVAL_ID == time`. A package left visible by the Brain cannot be
  accepted later after a temporary bridge outage, so the pending clock and
  missed-entry chronology stay aligned with the frozen combined baseline.

The global `max_bars_back=500` declaration was not restored. The review's
200–499-bar dynamic-history concern remained a targeted replay requirement,
not a static source defect. These repairs passed local structural checks: ten
bridge plots, ten bridge inputs, balanced delimiters, and no global
`max_bars_back`.

Post-repair fingerprints:

- Brain SHA-256: `7e63b45060ee2ee55ce941f1aad8da9b9d9905da753147db2ef1edab90ae794b`
- Execution + UI SHA-256: `0666aebf6f0920900abe6c49bf52b523df0f82944203984d619d6e84d40749c1`

### Final runtime repair and replay — 4 October 2026

#### Reproduced failure

- Environment: OANDA:XAUUSD, 5-minute chart, Bar Replay beginning at 1 October 2026 00:00.
- The hardened Brain compiled, and all ten Execution inputs were mapped correctly.
- After approximately 120 five-minute replay steps, TradingView stopped the Brain with `Runtime error — Memory limits exceeded`.
- The Execution consumer stopped updating as a consequence of its producer failing; this was not a separate lifecycle-logic error.

#### Confirmed root cause and repair

- The Phase 5 15-minute `request.security()` result previously returned 31 nested UDT objects for every requested bar.
- The request now returns 117 primitive series, below TradingView's 127-element tuple ceiling.
- Every value read by current decisions is preserved: all Demand/Supply, bullish/bearish OB, and Pivot S/R boundaries, origins, confirmations, and freshness flags; all FVG boundaries and freshness flags; all EQH/EQL levels; and setup location/swing boundaries.
- The omitted FVG and EQH/EQL timestamps were proven dead at the consumer boundary. Their compatibility aliases remain defined as typed `na` values, so no decision path silently receives invented timing data.
- No scoring threshold, AOI family distinction, freshness test, target priority, fixed-stop rule, retracement rule, Engine-6 state transition, or Engine-7 lifecycle rule was changed.

#### TradingView compile and runtime evidence

- Brain: compiled, updated, and saved successfully. Only inherited numeric-to-boolean warnings remain.
- Execution + UI: previously compiled, updated, and saved successfully with the current freshness gate.
- Connection: the live table showed `All 10 sources connected` after the Brain update; TradingView retained all ten exact mappings.
- Stale-package regression: a persisted Brain READY package remained visible, while Execution stayed `NO_TRADE`/`READY_REJECTED`; reconnecting did not start a late pending order.
- Replay: 520 sequential five-minute steps completed from the 1 October 2026 start, crossing the former 120-step failure point by more than four times.
- End state: both Brain and Execution tables remained present and updating, the Brain still reported `5m chart OK`, and no Pine runtime-error badge or memory error appeared.
- Live-value preservation check: before and after the transport repair, the same current chart snapshot retained the Brain handoff `LONG 4114.191–4115.791`, `DEMAND`, score `55.0`, confirmation `REACTION | 2`, and `LONG READY`; Execution continued to decode the same entry/stop/target package.

#### Fingerprints at that checkpoint

- Brain line count: 2,466
- Brain SHA-256: `77b6af67c4722977dd8db9d7c9b6422c5783c80313c61e74610d68bb1340e1b5`
- Execution + UI line count: 407
- Execution + UI SHA-256: `0666aebf6f0920900abe6c49bf52b523df0f82944203984d619d6e84d40749c1`
- Visual Reference line count: 2,474
- Visual Reference SHA-256: `67f94b9e39f5c20a83300f8a7f0e95f9c13b64515aedea3b1e15e0ac6dc7790a`

### Chart-output validation from 16 April 2024 — 4 October 2026

#### Scope and method

- Environment: OANDA:XAUUSD, required 5-minute chart, chart timezone UTC+7.
- Replay date: 16 April 2024. The closely observed bar-by-bar window ran from
  approximately 04:55 through 05:30.
- Loaded indicators: Visual Reference, Brain, and Execution + UI only.
- Validation combined chart observation with inspection of the exact current
  formulas and state transitions. A visual match is reported separately from
  an unexercised path; source inspection alone is not called runtime proof.
- This is an algorithm/output-concordance check, not proof of future
  profitability or statistical predictive reliability.

#### Defects found and repaired during replay

1. The Visual Reference dashboard created a new table object on every bar:

   ```pine
   infoDataTable = table.new(...)
   ```

   During replay this produced an intermittent visible mismatch: on one
   candle the Brain reported `7 / 2`, while the nine-row Visual dashboard
   displayed `4 / 5`, even though both scripts use the same nine formulas and
   the same defaults. The declaration is now:

   ```pine
   var table infoDataTable = table.new(...)
   ```

   This keeps one persistent table and updates its cells on the last bar. No
   MACD, Stochastic RSI, Vortex, Momentum, RSI, PSAR, DMI, MFI, or Fisher
   calculation was changed.

2. The local Execution + UI file contained one standalone `2` between the
   debug helper and its final `if barstate.islast` block. It was absent from
   the successfully compiled TradingView copy and would have broken a fresh
   paste. The stray character was removed; no lifecycle logic changed.

#### TradingView compile and runtime result

- The repaired Visual Reference compiled, updated on the chart, and saved.
- Compiler output contained the inherited numeric-to-boolean and
  calculation-consistency warnings, but no compiler error.
- After recompilation the Visual dashboard displayed four bullish and five
  bearish rows, exactly matching the Brain's `4 / 5` count on that replay bar.
- Execution continued to display `All 10 sources connected` after the Visual
  update. Its state stayed `NO_TRADE / NO_TRADE`, with both retracement
  candidates rejected as `ENTRY_ALREADY_PASSED`.
- The required 5-minute chart showed no indicator runtime-error badge.
- Switching the loaded layout to a daily chart produced runtime-error badges
  in the Brain/Execution pair. That timeframe is outside this system's stated
  operating contract; keep the split system on 5 minutes.

#### Observed output-to-chart concordance

| Component | Replay evidence | Result |
|---|---|---|
| Chart contract | Brain showed `5m chart OK`; OANDA:XAUUSD and all three indicators were present. | Pass |
| Ten-channel bridge | Execution showed `All 10 sources connected` throughout the observed 5m window. | Pass |
| Nine-indicator dashboard | Exact `8 / 1` agreement was observed at approximately 05:20. After the table repair, exact `4 / 5` agreement was observed at approximately 05:30. | Pass after repair |
| 4H/1H context | Brain showed bullish 4H macro/last break and bullish 1H primary bias while the visible chart was in a strong bullish expansion. The confirmed values remained stable between 5m candles. | Consistent, not an independent HTF bar-by-bar proof |
| Previous D/W/M | After the daily boundary, Brain showed D `2387.645 / 2324.255`, W `2431.590 / 2302.975`, and M `2236.330 / 2039.110`. The daily pair rolled only after the provider day changed. Weekly/monthly values were not independently cursor-checked because the Visual HTF lines were disabled. | Partial |
| Demand/Supply | Active 15m Demand `2381.833–2383.025` and Supply `2395.065–2395.780` matched the corresponding nearby zone locations. These remain distinct from OB and pivot S/R. | Pass for visible active zones |
| SMC Order Blocks | Bullish OB `2327.765–2335.570` remained separately reported; no bearish OB was active in the table. It was not relabeled as Demand. | Pass for classification; freshness history not fully replayed |
| Fair Value Gaps | The reported bullish FVG updated on a confirmed 15m boundary from `2378.255–2379.740` to `2383.870–2385.880`; bearish FVG remained around `2400.120–2410.580`. Updates did not occur on every 5m candle. | Pass for confirmed-timeframe behavior |
| Pivot S/R | Pivot Support `2361.752–2365.463` and Resistance `2391.337–2393.401` were independently listed and visually aligned with their volatility-sized chart zones. | Pass |
| EQH/EQL liquidity | The table reported no active EQH and EQL `2187.590`, with `0 / 3` pools. The EQL was outside the visible zoom, so its exact price could not be visually cross-checked in this window. | Partial |
| 5m BOS/CHoCH | Historical BOS/CHoCH labels aligned with closed-price structural breaks. The current debug pulse rows were false on the sampled candles, as expected when no new break occurred on that candle. | Consistent |
| BULB | Context changed from `Overbought` to `Neutral` as price left the RSI extreme. It is behaving as reversal/extreme context, not as an automatic trade trigger. | Pass for intended role |
| ATR envelope | The 47-SMA and ATR(89) envelopes tracked the visible volatility band, while the Brain ATR(89) changed gradually around `3.18`. It was not treated as an OB or Demand/Supply zone. | Pass for intended role |
| Rejected Engine-7 evaluation | With both fib entries already behind current price, Execution correctly stayed `NO_TRADE`, reported both exact rejection reasons, and showed no stale Entry/SL/TP values. | Pass |

#### Important Engine-6 reliability limitation exposed by this date

At the 16 April 2024 replay point, Engine 6 was already frozen in
`LOCKED_WAIT_TOUCH` on a LONG AOI at `2039.110–2040.620`, with target
`4H_SWING_HIGH 2065.530`, while current price was around 2380–2390. The lock
was therefore hundreds of dollars below price and its target had already been
surpassed, yet the lock remained active and prevented a fresh AOI selection.

This is not a calculation mismatch: it follows the current state machine. A
lock is released only by a confirmed close through its invalidation boundary,
or after its later touch/confirmation lifecycle. There is no maximum lock age,
maximum distance, or "target already passed before touch" reset in Engine 6.

Consequences for this validation:

- The frozen identity itself was stable, so lock immutability passed.
- The lock was not operationally current for the visible April market.
- No AOI touch, post-touch confirmation, READY package, pending fill, live
  trade, SL, TP1, TP2, or ambiguous-fill transition occurred in this replay
  slice.
- Engine 7 package construction and the full Execution lifecycle therefore
  remain **not exercised by the requested start date**. They must not be called
  runtime-validated from this replay alone.

Adding an age/distance/missed-target release would change trading policy and
could change which setups occur. It was intentionally not added during this
logic-preservation validation.

#### Reliability conclusion

The visible descriptive layers—structure, distinct zone families, FVG timing,
pivot S/R, dashboard states after the table repair, BULB context, ATR context,
and the hardened bridge/rejection display—fit the observed chart behavior in
the sampled 16 April window. The indicator should still be treated as a
confluence system, not as proof that any single Buy/Sell row predicts the next
move.

The split system is not yet fully certified end-to-end for this historical
date because the stale Engine-6 lock blocked every downstream trade-state path.
The next dedicated replay should begin before a known AOI lock, then capture a
later touch, later-bar structural confirmation, READY handoff, both fib
candidates, fixed 10.0 stop, TP1 at 1.5R or more, farther TP2, entry fill, and
close/cancel behavior.

#### Fingerprints at that checkpoint

- Brain line count: 2,466
- Brain SHA-256: `77b6af67c4722977dd8db9d7c9b6422c5783c80313c61e74610d68bb1340e1b5`
- Execution + UI line count: 431
- Execution + UI SHA-256: `170d9b543efaedd2d7e892f7e3fd5331bfd5083825fbb890b64dbf63f50d01f4`
- Visual Reference line count: 2,474
- Visual Reference SHA-256: `c28ab486d9f59dbbb28dda13a61e5cef61484799b2cec3df9719258488fda225`

### Rejected-READY display-state repair — 4 October 2026

#### Review finding verified against the current source

The external review's stale-package finding was confirmed in the current
Execution + UI source. When Execution was idle, both a normal Brain rejection
and the fail-safe invalid-package rejection updated `Reason`, `Last status`,
and `Last event`, but left the preceding accepted package's side, impulse,
Entry, SL, TP1, TP2, target kinds, R values, and fill metadata in memory. The
trade state remained `NO_TRADE`, so this did not create an active trade or an
Engine-8 handoff, but the debug table could misleadingly combine the new
rejection with old trade prices.

#### Scope of the repair

- The two idle rejection outcomes now share one reset block before their
  distinct reason/event strings are assigned.
- The reset clears the current package's setup ID, side, entry kind, impulse
  A/B/size/ATR/strength, Entry/SL/TP1/TP2, target kinds, R values, package/fill
  indices and timestamp, fill OHLC, TP1-hit flag, and ambiguous-fill flag.
- `phase7LastProcessedEvalId` is intentionally retained so an evaluation cannot
  be consumed twice.
- `IGNORED_READY_BUSY` still exits before the reset. A pending, live, or
  ambiguous trade therefore remains frozen when another READY arrives.
- History 1 and History 2 arrays are not read, cleared, reassigned, hidden, or
  deleted by the new rejection reset. Completed-trade drawings are preserved.
- No Brain, Phase-5 registry, Engine-6 scoring/state, bridge protocol, entry,
  stop, target, fill, or trade-close calculation was changed.

The review's 200–499-bar dynamic-history note remains a test boundary rather
than a confirmed source defect. This repair does not change the 499-bar policy,
does not restore global `max_bars_back=500`, and does not add temporary debug
state to the maintained Brain.

#### Static and TradingView validation

- Static checks: ten Brain bridge plots, ten Execution source inputs, and zero
  unmatched parentheses, brackets, or braces.
- TradingView compiler: the patched Execution + UI compiled and saved without
  an error.
- Environment: OANDA:XAUUSD, required 5-minute chart.
- Updating the consumer caused TradingView to reset external-source selections
  to `close`; all ten inputs were manually remapped to the identically named
  Brain plots and the layout was saved.
- Live rejected-READY regression: Execution displayed `NO_TRADE / NO_TRADE`,
  `INVALID_IMPULSE_SEQUENCE`, and `READY_REJECTED` while the connection cell
  displayed `All 10 sources connected`.
- In that exact rejected evaluation, `Impulse A / B` and `Impulse / ATR` showed
  dashes, side/entry showed `NONE NONE —`, SL showed a dash, and TP1/TP2 showed
  `NONE —`. No preceding package price remained in the current-status table.
- The chart showed no indicator-error badge after the final compile and remap.

Post-rejected-READY checkpoint fingerprints (before the later dashboard-table
persistence repair):

- Brain line count: 2,466
- Brain SHA-256: `77b6af67c4722977dd8db9d7c9b6422c5783c80313c61e74610d68bb1340e1b5`
- Execution + UI line count: 431
- Execution + UI SHA-256: `170d9b543efaedd2d7e892f7e3fd5331bfd5083825fbb890b64dbf63f50d01f4`
- Visual Reference line count: 2,474
- Visual Reference SHA-256: `67f94b9e39f5c20a83300f8a7f0e95f9c13b64515aedea3b1e15e0ac6dc7790a`

### Historical-buffer and Engine-6 lifecycle hardening — 4–5 October 2026

This section supersedes earlier statements in this document that the global
`max_bars_back` declaration remained removed and that Engine 6 intentionally
had no stale-lock release policy. A later 16 April 2024 replay exposed both a
concrete historical-buffer fault and lifecycle deadlocks that required a
bounded, logic-preserving repair before Engine 8 work.

#### Reproduced runtime failure

TradingView stopped the Brain at the Phase-5 Order Block scan with:

```text
Error on bar 5064: The requested historical offset (162) is beyond the
historical buffer's limit (161).
at phase5_setup_packet():801
at #main():1200
```

The scan was already intentionally capped at offset 499, but Pine had inferred
only 161 history slots on that execution path. The Brain now declares
`max_bars_back=500`, matching the existing maximum dynamic offset without
changing which candles the Order Block scan may inspect. The earlier primitive
117-series Phase-5 transport remains in place, so the old nested-UDT memory
failure is not reintroduced.

#### Review findings confirmed and repaired

The external review was treated as a lead and checked against the exact current
sources. All eight reported issues were confirmed:

1. `LOCKED_WAIT_TOUCH` had no finite lifetime.
2. `TOUCHED_WAIT_CONFIRM` had no confirmation timeout.
3. An Engine-7 rejection could leave Engine 6 permanently READY.
4. A valid READY parent could remain active indefinitely after use.
5. A simple reset could immediately select the same expired AOI again.
6. Engine-6 liquidity eligibility was relative to the AOI only, so already
   passed market liquidity could remain a target and earn score.
7. Engine-7 structural targets were checked relative to entry only, so a target
   already reached before package creation could theoretically be selected.
8. Execution used chart OHLC but had no independent 5-minute guard.

The maintained repair is:

- Untouched locks expire after configurable `phase6MaxLockBars` (default 288
  confirmed 5-minute bars, or 24 hours), or earlier when their original target
  is already reached.
- Touched setups expire after configurable `phase6MaxConfirmBars` (default 24
  confirmed 5-minute bars, or 2 hours) if no later structural/reaction
  confirmation appears.
- Rejected READY states release on the next confirmed bar. Accepted READY
  parents remain available for invalidation protection for configurable
  `phase6ReadyRetentionBars` (default 24), matching Execution's default pending
  lifetime, and then release.
- Every terminal release records the exact side + anchor family + origin time
  in a bounded 250-item Engine-6 consumed registry. Phase 5 continues tracking
  the underlying zone; only repeated orchestration of the exact dead setup is
  blocked.
- Invalidation still emits state 4 for one confirmed bar so a connected
  Execution instance can cancel its pending package before Engine 6 returns to
  search.
- Engine-6 target liquidity must remain beyond both the AOI reference and the
  current candle extreme. Engine-7 target candidates must remain beyond entry
  and beyond the READY candle high/low; point-liquidity swept inside the active
  15-minute setup window is excluded.
- Execution now advances pending/live/evaluation state only when
  `timeframe.period == "5"` and displays `Switch chart to 5m` otherwise.

#### Preserved policy and split contract

The repair does **not** change Phase-5 detector formulas, the separation of
Demand/Supply, SMC Order Blocks, FVG and Pivot S/R, the Engine-6 score weights
or minimum score, 4H/1H direction rules, the fixed 10.0 XAU stop, F38.2/F61.8
math, the 1.5R TP1 rule, the farther-TP2 requirement, fill/SL/TP ordering, or
the ten-channel bridge protocol. Static checks confirm exactly ten hidden
`BRIDGE_*` plots in the Brain and exactly ten `input.source` channels in
Execution.

#### TradingView compile and replay evidence

- Environment: OANDA:XAUUSD, required 5-minute chart, UTC+7 chart timezone.
- The exact maintained Brain source compiled and was added to the chart at
  approximately 23:20 on 4 October 2026. The exact maintained Execution source
  compiled and was added at approximately 23:21. Only the Brain's inherited
  numeric-to-boolean warnings remained; neither script had a compile error.
- The loaded lifecycle inputs visibly showed the new defaults `288 / 24 / 24`.
- A wrong-timeframe check on 15 minutes produced `Use locked 5m chart` in the
  Brain and `Switch chart to 5m` in Execution. Returning to 5 minutes removed
  the timeframe warning.
- Bar Replay began on 16 April 2024 and advanced approximately 300 sequential
  five-minute bars into 17 April. No historical-offset, memory-limit or other
  Pine runtime-error badge appeared.
- Before the timeout boundary the Brain held LONG Demand AOI
  `2365.017–2366.200` in `LOCKED_WAIT_TOUCH`. After crossing 288 bars, that AOI
  was no longer active; Engine 6 had released it and later selected a different
  LONG Demand AOI `2366.942–2368.870`. This is runtime evidence that the stale
  lock expired and the exact old AOI was not immediately re-locked.

#### Validation boundary

Re-adding the compiled Execution source reset its ten external-source selectors
to `close`. They were deliberately left unmapped after attempts to manipulate
the dropdowns proved unreliable in this UI session. Therefore this checkpoint
validates exact-source compilation, the Brain's historical replay and stale-lock
release, and both scripts' local 5-minute guards. It does **not** claim a fresh
end-to-end Brain-to-Execution package, fill, SL, TP1, TP2 or cancellation replay
for this build. Map all ten sources according to the bridge table above and
confirm `All 10 sources connected` before using Execution. Runtime correctness
also does not establish profitability or optimal timeout values.

#### Fingerprints at that checkpoint

- Brain line count: 2,560
- Brain SHA-256: `1d54b6834ac987f357da3a1fb07a50031942f78095e0dea879091b7a784bc88c`
- Execution + UI line count: 432
- Execution + UI SHA-256: `9f8e2f54dcb2b55ba3da0477ddf6ff653a728a51d1eb3b75609eff0733961452`
