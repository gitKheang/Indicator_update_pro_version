# Phase 5 — Multi-Timeframe State Architecture

## Purpose

Phase 5 turns the indicator's independent engines into a shared, confirmed multi-timeframe data interface:

- **4H:** larger market environment
- **1H:** primary intraday directional bias
- **15m:** candidate trade locations
- **5m:** current execution evidence
- **Session:** current intraday environment

Phase 5 only collects, normalizes, and publishes information. It does **not** score setups, lock AOIs, create BUY/SELL signals, calculate a 100-pip stop, calculate TP1/TP2, or place strategy orders. Those decisions remain reserved for Phase 6.

## The eight completed pieces

### 1. MTF Timeframe Controller

Added four locked Phase 5 timeframes:

- Macro TF: `240` (4H)
- Bias TF: `60` (1H)
- Setup TF: `15` (15m)
- Execution TF: `5` (5m)

The public Phase 5 contract is intentionally fixed to `4H > 1H > 15m > 5m`. Each timeframe input has only its required value available, and the controller validates both the hierarchy and the current 5m chart. This prevents the earlier problem where the inputs could be changed while the public names and debug labels still claimed 4H/1H/15m/5m.

### 2. Safe / Confirmed MTF Data Layer

Added confirmed OHLC transport for 4H, 1H, and 15m. Higher-timeframe requests use the previous completed source-timeframe bar together with `barmerge.lookahead_on`. This makes the Phase 5 feed use known closed-bar information instead of an unfinished higher-timeframe candle.

Added separate, data-only liquidity references from fully completed calendar periods:

- `prevDayHigh` / `prevDayLow`
- `prevWeekHigh` / `prevWeekLow`
- `prevMonthHigh` / `prevMonthLow`

These use `[high[1], low[1]]` with `lookahead_on`, so Phase 6 can evaluate higher-timeframe liquidity and target room without reading an unfinished Daily, Weekly, or Monthly candle. The older optional visual D/W/M drawings were not rewritten or replaced.

### 3. 4H Macro Context Module

Reuses the original `swings(length)` state machine, structural break locks, and close-cross break rules and publishes:

- `macro4HBias`
- `macro4HHigh`
- `macro4HLow`
- `macro4HBreak`
- `macro4HRange`

The latest break direction is persistent. It remains bullish or bearish until a confirmed opposite structural break occurs. This replaces the earlier Phase 5 pivot substitute, so the macro packet now derives its structural points from the same custom swing source as the original SMC engine.

### 4. 1H Primary Bias Module

Publishes:

- `bias1H`
- `bias1HBreak`
- `bias1HLocation`

Location uses the script's narrow Premium/Equilibrium/Discount percentages, but applies them to the last confirmed swing high/low range. Values outside those narrow zones are explicitly described as above or below equilibrium rather than incorrectly calling the complete upper/lower half Premium or Discount.

This is intentionally stable confirmed context for the Master Brain. It is not claimed to be identical to the original visual Premium/Discount boxes, whose range uses live `trail_up` and `trail_dn` extremes and can move before another swing is confirmed.

### 5. 15m Setup / AOI Module

Added data-only adapters. They do not duplicate visual boxes or combine engines into one score.

Published fields:

- Three Demand candidates: `setup15mDemand1*` through `setup15mDemand3*`
- Three Supply candidates: `setup15mSupply1*` through `setup15mSupply3*`
- Three bullish Swing OB candidates: `setup15mBullOB1*` through `setup15mBullOB3*`
- Three bearish Swing OB candidates: `setup15mBearOB1*` through `setup15mBearOB3*`
- Three bullish FVG candidates: `setup15mBullFVG1*` through `setup15mBullFVG3*`
- Three bearish FVG candidates: `setup15mBearFVG1*` through `setup15mBearFVG3*`
- Three Pivot Support candidates: `setup15mPivotSupport1*` through `setup15mPivotSupport3*`
- Three Pivot Resistance candidates: `setup15mPivotResistance1*` through `setup15mPivotResistance3*`
- Each numbered candidate publishes `Top`, `Bottom`, `Origin`, `Confirmed`, and `Fresh` fields. The older `Born` name remains as a compatibility alias of `Origin`.
- `setup15mSwingHigh` / `setup15mSwingLow`
- `setup15mDemand`
- `setup15mSupply`
- `setup15mBullOB`
- `setup15mBearOB`
- `setup15mBullFVG`
- `setup15mBearFVG`
- `setup15mPivotSupport`
- `setup15mPivotResistance`
- Three unswept EQH candidates: `setup15mEQH1*` through `setup15mEQH3*`
- Three unswept EQL candidates: `setup15mEQL1*` through `setup15mEQL3*`
- Each liquidity candidate publishes its price, `Origin`, and `Confirmed` time. The unnumbered `setup15mEQH` / `setup15mEQL` aliases point to candidate 1.
- `setup15mLocation`

Important separation is preserved:

- Demand/Supply candidates come from the displacement/base-candle engine.
- Bull/Bear OB candidates come from the Swing Order Block structure-break interval search.
- FVG candidates come from the three-candle imbalance engine.
- Pivot support/resistance uses the configured pivot source and volatility-sized band.
- EQH/EQL remain liquidity levels, not zones.

Each adapter tracks active candidates and publishes the nearest three as complete top/bottom ranges. Candidate 1 is nearest to the current confirmed 15m close, candidate 2 is second-nearest, and candidate 3 is third-nearest. A non-`na` candidate is active. Candidate type is preserved by the separate variable family, while the metadata lets Phase 6 compare age, confirmation latency, and freshness without Phase 5 applying a score.

The timestamps have deliberately different meanings. `Origin` remains the opening time of the source candle/pivot, while `Confirmed` is the closing time of the bar that made the candidate knowable:

- Demand/Supply `Origin` is the base/S1 candle time; `Confirmed` is the displacement bar that creates the zone.
- Swing OB `Origin` is the selected order-block candle; `Confirmed` is the closing BOS bar.
- FVG `Origin` is the middle displacement candle; `Confirmed` is the third candle that makes the gap knowable.
- Pivot S/R `Origin` is the actual pivot candle; `Confirmed` is the later bar after the configured right-side confirmation period.
- EQH/EQL `Origin` is the earlier matching pivot; `Confirmed` is the later pivot-confirmation bar that establishes the pool.

Because a following 15m bar opens at the same timestamp that the confirming bar closes, post-confirmation touch and sweep checks use `time >= Confirmed`. This allows that immediately following bar to be the first legitimate retest or sweep without treating the confirming bar itself as a later event.

`Fresh` is true until a later bar revisits the still-active zone. Demand/Supply zones are removed when the proximal S1 level is hit, so every active Demand/Supply candidate is necessarily fresh. OB, FVG, and Pivot candidates can remain active after a first overlap and therefore publish `Fresh = false` until invalidated. EQH/EQL use unswept membership instead of a zone-freshness flag and are removed after a later sweep through the level.

The older unnumbered range and single-price aliases remain compatible and point to candidate 1. Demand and bullish/support aliases use the proximal top, Supply and bearish/resistance aliases use the proximal bottom, and FVG aliases use the midpoint. The interface does not call one engine's output by another engine's name.

The prior hidden, engine-specific retention limits of 100 Demand/Supply zones, 50 OBs, and 100 FVGs were removed. All Phase 5 AOI adapters use the visible **Active candidate safety cap** input. Its runtime-safe default is now `100`, with a configurable range of `25` to `500`. The cap is deliberate runtime protection rather than an undisclosed semantic filter. It does not change the public nearest-three interface, although candidates older than the retained pool cannot be published. Pivot state retains at least three candidates per pivot array even when the visual `Number of Pivots` remains `1`; this affects only the data adapter and does not alter the original drawings.

The large candidate packet is transported through one `Phase5SetupState` object containing fixed-size nested zone and liquidity candidate objects. It does not return higher-timeframe arrays or collections, which avoids the global tuple-element limit. Because TradingView must still retain requested UDT results across chart history, the 15m request now uses the visible **15m setup history bars** input as `calc_bars_count`, default `500` with a range of `500` to `5000`. The active-candidate safety cap independently bounds each retained registry. An empty typed state protects the earliest chart bars where `request.security()` has not yet produced a source-timeframe object.

The Swing OB adapter now uses the original `swings(length)` source and one-break-per-swing lock. The Pivot S/R adapter now preserves the configured pivot source, ATR sizing, `alignZones` overlap behavior, and bullish/bearish polarity flips after a close through the zone.

### 6. 5m Execution Context Module

Reuses existing current-chart calculations instead of creating a second 5m engine:

- `exec5mInternalTrend`
- `exec5mSwingTrend`
- `exec5mTrend` (compatibility alias of Internal Trend)
- `exec5mInternalBullCHoCH` / `exec5mInternalBearCHoCH`
- `exec5mSwingBullCHoCH` / `exec5mSwingBearCHoCH`
- `exec5mBullCHoCH`
- `exec5mBearCHoCH`
- `exec5mBullReaction`
- `exec5mBearReaction`
- `exec5mMomentum`
- `exec5mBULB`
- `exec5mATR`

Internal and Swing CHoCH are now published separately so Phase 6 can distinguish microstructure from the stronger swing-structure event. The older combined `exec5mBullCHoCH` and `exec5mBearCHoCH` aliases remain for compatibility and are true when either corresponding internal or swing event is true.

The stable `exec5m*` interface is closed-bar confirmed. Internal and Swing trend states remain separate because a microstructure trend must not overwrite or impersonate the stronger swing trend. Separate `exec5m*Live` aliases expose forming-bar context without allowing it to masquerade as confirmed evidence, including separate live Internal/Swing trends and CHoCH aliases.

All nine dashboard readings are now exposed independently:

- `exec5mMACD`
- `exec5mStoch`
- `exec5mVortex`
- `exec5mMomentumIndicator`
- `exec5mRSI`
- `exec5mPSAR`
- `exec5mDMI`
- `exec5mMFI`
- `exec5mFisher`
- `exec5mBullCount` / `exec5mBearCount`

`exec5mMomentum` remains the strict 9/9 consensus output for compatibility. It is bullish only when all nine dashboard engines agree bullish, bearish only when all nine agree bearish, and neutral otherwise. Phase 6 can now consume the individual states or counts instead of losing all partial agreement. BULB remains overbought/oversold context only. ATR uses the existing ATR(89) envelope calculation.

### 7. Session State Module

Publishes `sessionState` as one of:

- `ASIA`
- `LONDON`
- `NEW_YORK`
- `LONDON_NY_OVERLAP`
- `OFF_SESSION`

Default hours use the market's local timezone names so daylight-saving changes are handled by TradingView:

- Asia: 09:00–18:00, `Asia/Tokyo`
- London: 08:00–17:00, `Europe/London`
- New York: 08:00–17:00, `America/New_York`

Session state is informational and is not a trade gate.

### 8. MTF State Interface and Debug Table

Added a stable central interface using the variable names listed above. A table at the top-right displays all major Phase 5 outputs separately for inspection before Phase 6 is built. It shows confirmed previous D/W/M liquidity, complete nearest 15m zone ranges, the number of published candidates in every AOI pool, the confirmed 15m swing range, separate Internal/Swing CHoCH states, dashboard bull/bear counts, and a compact view of all nine dashboard directions.

The debug table can be disabled with **Show MTF Debug Table** or moved to another corner.

## What was preserved

- Existing SMC structure drawings and alerts
- Internal and Swing Order Block drawings
- Existing Demand/Supply drawings and alerts
- Existing FVG drawings
- Existing Pivot S/R engine and optional detectors
- Existing EQH/EQL drawings
- Existing nine-indicator dashboard
- Existing BULB labels
- Existing ATR envelopes
- All v2 default visibility choices

No original engine was converted into a trade-entry engine, and no Phase 6 judgment logic was added.

## Review findings verified and fixed

The two supplied reviews were checked against the actual v3 source. These issues were real and were corrected:

1. The 4H/1H packets used generic pivots instead of the original SMC `swings()` source.
2. The 15m Swing OB adapter used a different pivot source and lacked the original break lock.
3. The 15m Pivot S/R adapter omitted zone alignment and bullish/bearish polarity flips.
4. The dashboard adapter discarded every non-9/9 combination instead of exposing nine independent readings.
5. The public 5m execution fields could expose unfinished-bar states as though they were confirmed.
6. Timeframes were configurable while fixed public names and table labels still claimed 4H/1H/15m/5m.
7. Several setup adapters reduced zones to one price and lost their top/bottom geometry.

The fixes stay inside Phase 5's data-collection role. They do not introduce scoring, entries, stops, targets, AOI locking, or strategy orders.

## Follow-up inspection findings

The later inspection identified one real omission and one real semantic distinction:

1. **Fixed:** Phase 5 had no safe previous Daily/Weekly liquidity interface. Confirmed previous Day, Week, and Month high/low variables were added without modifying the original optional drawings.
2. **Documented by design:** Phase 5 location uses a confirmed swing range, while the original visual Premium/Discount engine uses live trailing extremes. The confirmed method was retained for stable Master-Brain input, and the code, table labels, and documentation now state that distinction explicitly.

The suggested Internal OB addition was not made. The original Phase 5 plan described it as useful where appropriate, not mandatory; Swing OB remains the primary 15m AOI source and the existing 5m internal structure remains available for execution context.

## Candidate-pool review findings

The newest two supplied reviews were checked against the updated v3 source. Their three core findings were confirmed and fixed:

1. **Nearest-only AOI loss:** Real. Phase 5 previously published only one nearest candidate per AOI type, preventing Phase 6 from comparing multiple valid locations. It now publishes the nearest three per type, including bounds and origin time, while keeping candidate 1 aliases backward-compatible.
2. **Silent active-zone truncation:** Real. The adapter-specific hard caps (`100`, `50`, and `100`) could silently discard older active zones. They were replaced with one explicit configurable safety cap, default `500`, applied consistently to Demand/Supply, Swing OB, and FVG candidate state.
3. **Merged CHoCH strength:** Real. Internal and Swing CHoCH were collapsed into one boolean pair. Separate confirmed and live Internal/Swing outputs were added; the combined outputs remain only as compatibility aliases.

The related range-exposure observation was also correct: the setup packet calculated its confirmed 15m swing high/low but did not publish stable public names. They are now exposed as `setup15mSwingHigh` and `setup15mSwingLow`.

No AOI scoring, ranking beyond price proximity, signal creation, stop/target logic, trade locking, or order placement was added. Those remain Phase 6 responsibilities.

## Metadata and liquidity-pool review findings

The latest supplied review was checked against the current source. All three reported gaps were real and were corrected:

1. **Ambiguous AOI age/freshness:** Real. A single `Born` timestamp could not distinguish the origin candle from the bar where a delayed engine confirmed the object, and active non-Demand/Supply zones had no first-touch state. Every numbered AOI now exposes `Origin`, `Confirmed`, and `Fresh`; `Born` remains only as an origin-time compatibility alias.
2. **Single overwritten EQH/EQL:** Real. One latest value discarded other valid unswept liquidity pools. Phase 5 now maintains active unswept EQH/EQL registries and publishes the nearest three above/below confirmed 15m price, each with origin and confirmation time.
3. **One persistent 5m trend:** Real. The old interface exposed only `itrend`, even though the original SMC engine maintains independent internal and swing trends. Confirmed and live `exec5mInternalTrend` and `exec5mSwingTrend` outputs are now separate; `exec5mTrend` remains a compatibility alias only.

During exact-source validation, TradingView also exposed a first-bar initialization defect: the higher-timeframe UDT can be `na` before its first completed source value, so direct field access raised `RE10041`. A typed empty setup state now supplies neutral/`na` fields only during that initialization window. It does not create candidates or change populated-bar results.

## Final Phase 5 correction review

The final supplied review was checked against the exact v3 source. All four findings were present and were corrected without adding Phase 6 behavior:

1. **Empty-state location:** The typed fallback used location code `0`, which decodes as Equilibrium. It now uses `9`, so unavailable 15m initialization data is reported as Unavailable.
2. **Pivot alignment metadata:** Alignment previously replaced only the newest target Pivot zone's geometry. It now synchronizes the aligned metadata at the same time: `Origin` is the earliest contributing origin, `Confirmed` is the latest contributing confirmation, and `Fresh` remains true only when both contributing zones are fresh. Pivot polarity-flip behavior is unchanged.
3. **Confirmation timestamps:** Demand/Supply, Swing OB, FVG, Pivot S/R, and EQH/EQL candidates now store `time_close` as `Confirmed`. Their origin timestamps are unchanged. All corresponding later-touch and sweep guards now use `time >= Confirmed`.
4. **History reconstruction:** The earlier unrestricted-history version removed `calc_bars_count`, but the large requested `Phase5SetupState` subsequently exceeded TradingView's runtime memory limit. The bounded history input has therefore been restored as part of the memory-safety repair described below.

## Runtime memory repair

The reported `Memory limits exceeded` runtime failure was consistent with the exact v3 source. Phase 5 returned a large nested `Phase5SetupState` object from `request.security()` over all available 15m history while maintaining multiple persistent candidate registries. TradingView documents requested custom objects and excessive requested history as common causes of this error.

The repair is deliberately limited to two resource bounds:

1. Restored **15m setup history bars**, default `500` and configurable from `500` to `5000`, and passed it to the setup `request.security()` call as `calc_bars_count`.
2. Reduced **Active candidate safety cap** from `500` to `100`, with a configurable range of `25` to `500`.

No candidate detection, zone geometry, confirmation timestamp, freshness/invalidation rule, proximity ordering, public nearest-three field, drawing engine, alert, or Phase 5/Phase 6 responsibility was changed. The tradeoff is explicit: Phase 5 cannot reconstruct a candidate created before the selected 15m history window, and a registry containing more candidates than its selected cap discards the oldest retained candidate. Increase either setting only after confirming TradingView runtime stability.

## Demand/Supply boundary-contract repair

The live Phase 5 table exposed a reversed Demand range: because the formatter intentionally displays `Bottom–Top`, the value `4132.593–4127.808` showed that the stored `Top` was below the stored `Bottom`. Inspection confirmed that the Phase 5 Demand adapter independently adjusted its two boundaries and then stored them without normalizing their final order. This could make the Demand proximal-edge alias and subsequent touch logic use the wrong side of the zone.

Demand and Supply candidates are now normalized immediately after their existing mintick rounding and before insertion into the Phase 5 registries:

- `Top = math.max(adjusted Top, adjusted Bottom)`
- `Bottom = math.min(adjusted Top, adjusted Bottom)`

This establishes the invariant `Top >= Bottom` for every Phase 5 Demand/Supply candidate. Demand continues to expose `Top` as its proximal edge, while Supply continues to expose `Bottom` as its proximal edge. The repair does not change zone detection, displacement thresholds, base-candle selection, size-adjustment formulas, origin/confirmation timestamps, freshness, candidate ordering, the 500-bar setup-history default, or FVG logic.

## Validation

- The v3 baseline immediately before the final correction review compiled in TradingView Pine Script v5 on 2026-10-03.
- That baseline was accepted and saved with no compile error; only the script's pre-existing warnings from earlier source lines remained.
- The updated script rendered on `OANDA:XAUUSD`.
- Runtime was checked on the intended 5-minute chart.
- The candidate-pool row rendered `2/3 0/1 0/3 1/3` for Demand/Supply, bullish/bearish OB, bullish/bearish FVG, and Pivot Support/Resistance respectively on the inspected chart state.
- The separate EQH/EQL pool-count row rendered `0 / 0` on that state; empty pools were handled normally rather than producing stale levels.
- The confirmed 15m swing high/low row populated; the 5m Internal/Swing trend row rendered `Bullish / Bearish`; and Internal CHoCH and Swing CHoCH rendered as separate rows.
- The Phase 5 table populated 4H, 1H, 15m, confirmed 5m, dashboard, and session fields.
- Confirmed previous Daily, Weekly, and Monthly high/low values populated in the live table.
- Complete Demand/Supply, Swing OB, FVG, and Pivot S/R ranges rendered in the table.
- All nine dashboard states and the `5 / 4` bull/bear count rendered consistently with the existing dashboard visible on the same chart.
- The locked controller reported `5m chart OK` on the intended chart.
- The initial `RE10041` undefined-object failure was reproduced, traced to bar-zero UDT initialization, repaired, and absent after recompiling the exact corrected source.

The final correction patch received a targeted local source audit: all ten candidate confirmation assignments use `time_close`, all ten corresponding post-confirmation guards use `time >= Confirmed`, all four Pivot alignment calls pass geometry and metadata arrays, and the empty-state location is `9`.

The runtime-memory repair was also audited locally: the setup-history input is present with default `500`, the 15m setup request uses it through `calc_bars_count`, the active-candidate cap defaults to `100`, and the public candidate field names and Phase 5 decision logic remain intact. A fresh TradingView compile/runtime pass remains required because this local edit cannot prove Pine compilation or runtime memory behavior.

The Demand/Supply boundary repair received a targeted local audit: both candidate families normalize their final rounded boundaries before registry insertion, the debug formatter remains `Bottom–Top`, the Demand and Supply proximal aliases remain unchanged, and neither the setup-history limit nor FVG code was modified. After recompiling in TradingView, every populated Demand/Supply range in the debug table should increase from left to right.

The earlier live pass validates the pre-correction baseline's compilation and chart rendering; the final patch currently has local structural evidence only. Neither pass proves historical replay stability, signal accuracy, profitability, or completed Phase 6 logic.
