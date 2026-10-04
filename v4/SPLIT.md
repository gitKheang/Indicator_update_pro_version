# v4 Visual / Lean-Core Split

## Result

The v4 codebase now contains two independent TradingView indicators. The original combined v4 file was deleted after the split at the user's request. The byte-identical v3 source remains available as a recovery/parity copy.

| File | Role |
|---|---|
| `SMC ICT Scalping Master - Visual Reference.pine` | Script A. Original visual/manual-analysis engines through ATR Envelopes, with the complete Phase 5 block removed. |
| `XAUUSD Smart Trade Core - Phase 5.pine` | Script B. Calculation-only dependencies plus the unchanged Phase 5 state architecture and debug table. This is the future Engine 6/7/8 foundation. |

The two split scripts do not communicate with each other. Each calculates from the chart's price data.

## Preserved separation of systems

The split does not merge or rename the indicator's independent concepts:

- SMC Internal and Swing Structure remain separate.
- Swing Order Blocks remain separate from Demand/Supply zones.
- Pivot Support/Resistance remains separate from both of those systems.
- FVGs remain imbalance zones.
- EQH/EQL remain liquidity levels, not zones.
- The nine-indicator dashboard, BULB, and ATR remain secondary execution context.

Script A retains the original drawings, labels, boxes, alerts, dashboard, BULB labels, candle-pattern tools, and ATR envelopes. It stops immediately before Phase 5.

Script B contains no legacy `box.new`, `label.new`, `line.new`, plot, candle-pattern import, or visual-alert machinery. The Phase 5 debug table is intentionally retained for parity testing.

## Lean-core dependency mapping

Script B rebuilds only the calculations required by the Phase 5 contract:

| Phase 5 consumer | Lean dependency retained |
|---|---|
| 4H / 1H structure | Original `swings()` source, close-cross structural state, and one-break-per-swing locks |
| 15m Demand/Supply | Original percentage helpers, thresholds, base/displacement geometry, lifecycle, and metadata |
| 15m Swing OB | Original swing source and ATR/cumulative-mean filter selection |
| 15m FVG | Original three-candle condition and automatic threshold |
| 15m Pivot S/R | HA/body/high-low source, ATR width, alignment, polarity flips, freshness, and nearest-three selection |
| 15m EQH/EQL | Pivot confirmation, ATR threshold, unswept lifecycle, and nearest-three selection |
| 5m structure | Internal/Swing trend and Internal/Swing CHoCH calculations without drawings |
| 5m reactions | Numeric equivalent of the box-backed Pivot S/R overlap and polarity engine |
| 5m dashboard | All nine original formulas and directional comparisons |
| 5m BULB / ATR | RSI(13) 65/30 state and ATR(89) |
| Session | Existing timezone-aware Phase 5 session module |

## Invariants deliberately unchanged

- Phase 5 timeframes remain locked to 4H, 1H, 15m, and 5m.
- `phase5SetupHistoryBars` still defaults to `500`.
- `phase5ActiveCandidateCap` still defaults to `100`.
- The nearest-three interface remains unchanged for every AOI family.
- `Origin`, `Confirmed`, and `Fresh` semantics remain unchanged.
- The full public aliases from `macro4HBias` through `sessionState` remain unchanged.
- No AOI scoring, setup locking, entry, stop, target, order, Engine 6, Engine 7, or Engine 8 logic was added.
- No history expansion or candidate-cap optimization was mixed into the migration.

## Local verification completed

- Before deletion, the combined v4 master was verified byte-for-byte against the retained v3 source with SHA-256 `0b48efb4089a50c36d5585347e8030af46a657448add687dab87e37b0a27520e`.
- Script A contains no Phase 5 identifiers or public Phase 5 aliases.
- Script B contains no legacy drawing/plot/import/alert calls outside its retained Phase 5 table code.
- Script B retains the complete Phase 5 block from the master; only line-ending normalization and the surrounding lean dependency layer differ.
- The required safety defaults and `calc_bars_count=phase5SetupHistoryBars` connection remain present.

### Verified split repair — persistent Pivot S/R polarity tracker

The retained v3 parity source declares the original Pivot S/R `_color()` tracker as `var int _track = nPiv`. The first lean split accidentally declared its replacement as ordinary `int _track = nPiv`, which reinitialized the returned tracker on every bar.

This was a real parity defect because `trackHigh` and `trackLows` feed `moveAbove`, `moveBelow`, `resBreak`, `supBreak`, `bullCheck`, and `bearCheck`; Phase 5 then publishes the two reaction values through `exec5mBullReaction` and `exec5mBearReaction`.

The lean declaration is now restored to:

```pine
lean_color_zones(_tops, _bottoms, _states) =>
    var int _track = nPiv
```

No other Pivot S/R, reaction, ATR, Phase 5, input-default, or candidate logic was changed in this repair. The two written calls for Pivot High and Pivot Low retain independent function-call histories under Pine's execution model.

Official Pine references:

- [Variable declarations](https://www.tradingview.com/pine-script-docs/language/variable-declarations/) — default declarations reinitialize on each scope execution; `var` persists across bars.
- [User-defined functions](https://www.tradingview.com/pine-script-docs/v5/language/user-defined-functions/) — each written function-call instance maintains independent history.

These checks prove the intended source split and dependency coverage. They do not prove TradingView compilation, runtime memory stability, or candle-by-candle parity.

## Required TradingView validation

Use `OANDA:XAUUSD` on a 5-minute chart and keep all corresponding input values equal.

1. If full-versus-lean parity evidence is needed, paste and save the retained v3 full source as the temporary parity reference.
2. Paste and save `XAUUSD Smart Trade Core - Phase 5.pine` as a separate indicator.
3. Put both Phase 5 debug tables in different corners.
4. On the same closed candle, compare 4H bias/high/low/break, 1H bias/location, all 15m candidate ranges and pool counts, EQH/EQL, 5m Internal/Swing trends and CHoCH, reactions, all nine dashboard directions/counts, BULB, ATR, and session.
5. Compare every populated candidate's `Top`, `Bottom`, `Origin`, `Confirmed`, and `Fresh` value where accessible.
6. Run Bar Replay across at least one bullish structure break, one bearish structure break, an AOI retest, and a session transition.
7. Reload the chart on the same historical candle and confirm both tables remain equal.
8. After parity succeeds, remove the temporary full reference from the chart and use Script A plus Script B together.

If any field differs, treat it as a migration defect. Do not tune thresholds, increase history, or begin Engine 6 until the mismatch is resolved.

## Later optimization boundary

After TradingView parity and runtime stability are confirmed, test setup history gradually (`500`, `1000`, `2000`, then `5000`). Keep the active candidate cap at `100` unless measured evidence shows the nearest-three output loses a useful active candidate. Increasing history can change the automatic FVG threshold, so it is a behavioral experiment rather than a free memory adjustment.
