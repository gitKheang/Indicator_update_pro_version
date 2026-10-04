# Engine 6 — AOI Decision and Orchestration

## Status

Engine 6 is implemented in `XAUUSD Smart Trade Core - Phase 5.pine`.

It contains exactly eight decision/orchestration features and adds no new raw market detector. The existing Phase-5 contract remains the source of 4H/1H structure, 15m AOI families, liquidity references, and confirmed 5m execution evidence.

Engine 6 stops before exact entry, stop loss, targets, position sizing, or orders. Those remain responsibilities of Engines 7 and 8.

## Implemented features

1. **Direction Context Engine**
   - Classifies confirmed 4H plus 1H structure as `BULLISH`, `BEARISH`, or `MIXED`.
   - Agreement adds score; disagreement subtracts score.
   - It does not require 4H, 1H, 15m, and 5m to all agree.
   - Complete 4H plus 1H opposition is an optional hard rejection and is enabled by default.

2. **AOI Candidate Builder**
   - Builds LONG anchors from fresh confirmed Demand, Bullish SMC Order Block, and Pivot Support candidates.
   - Builds SHORT anchors from fresh confirmed Supply, Bearish SMC Order Block, and Pivot Resistance candidates.
   - Uses all three published candidates from each anchor family: 9 LONG and 9 SHORT anchor slots.
   - FVG remains supporting confluence and cannot become an anchor by itself.
   - A LONG anchor must be below current price; a SHORT anchor must be above current price.
   - A candidate is rejected if any 5m candle has already overlapped it after the close of the latest confirmed 15m snapshot. This prevents a delayed Phase-5 `Fresh` flag from allowing a pre-touched AOI to become a new lock.

3. **Confluence Mapper**
   - Detects price overlap with same-side Demand/Supply, SMC OB, FVG, and Pivot S/R.
   - A supporting zone counts only when Phase 5 marks it fresh and no 5m candle has touched that supporting zone since the latest confirmed 15m snapshot closed.
   - Counts independent families once, even when several candidates from one family overlap.
   - Publishes both a source bit mask and readable source names.
   - Source mask: `1 = Demand/Supply`, `2 = SMC OB`, `4 = FVG`, `8 = Pivot S/R`.

4. **AOI Quality Scorer**
   - Scores source-family diversity, 4H context, 1H context, 15m location, freshness, complete origin/confirmation metadata, recent confirmation, and target-side liquidity.
   - All weights and the minimum score are inputs so they can be calibrated later instead of being treated as proven constants.
   - Default minimum score: `55`.
   - Tie order: higher score, then nearer anchor, then newer confirmation time.

5. **Liquidity Context Engine**
   - Reuses existing EQH/EQL, previous D/W/M highs and lows, confirmed 15m swing levels, and confirmed 4H swing levels.
   - Stores the nearest target-side liquidity price and type.
   - Finds the nearest active opposing 15m zone between the AOI and target liquidity as an obstacle.
   - LONG obstacles come from Supply, Bearish SMC OB, Bearish FVG, and Pivot Resistance; SHORT uses the inverse families.
   - After an AOI is locked, target liquidity and the nearest obstacle are refreshed from the latest confirmed Phase-5 data around the frozen AOI.
   - It does not calculate TP1, TP2, R-multiples, or target legality.

6. **AOI Selector and Lock Engine**
   - Selects the best candidate that reaches the minimum score.
   - Copies side, boundaries, score, anchor type, source mask/count/names, origin, confirmation time, liquidity context, and lock time into persistent variables.
   - The copied AOI does not move when Phase-5 nearest candidates or scores later change.
   - Lock-time liquidity and obstacle values remain stored for audit, but they are not used as the live Engine-7 market-context handoff.
   - A confirmed 15m close below a LONG AOI bottom or above a SHORT AOI top invalidates the lock; a 5m wick or close alone does not.

7. **Post-Touch 5m Confirmation Engine**
   - Touch condition: `low <= lockedTop and high >= lockedBottom`.
   - The lock bar cannot also count as the touch bar; touch begins on the next confirmed 5m bar or later.
   - Confirmation can only occur on a confirmed 5m bar after the touch bar.
   - Requires at least one same-side Internal CHoCH, Swing CHoCH, or Pivot S/R reaction.
   - Internal trend, swing trend, dashboard majority, BULB, and session only increase confirmation strength.
   - The dashboard default is a 6-of-9 majority; 9-of-9 is not required.

8. **Phase-6 Handoff Engine**
   - Emits stable state, side, locked AOI, score, source metadata, timestamps, liquidity context, confirmation type/strength, and readiness.
   - Final handoff text is `LONG READY`, `SHORT READY`, or `NO SETUP`.

## State machine

```text
SEARCHING
    -> LOCKED_WAIT_TOUCH
    -> TOUCHED_WAIT_CONFIRM (later 5m bar)
    -> READY_FOR_PHASE7 (later confirmed 5m bar)

LOCKED_WAIT_TOUCH / TOUCHED_WAIT_CONFIRM / READY_FOR_PHASE7
    -> INVALIDATED
    -> SEARCHING
```

State changes are allowed only on confirmed bars when the chart is the locked 5m execution timeframe and the 4H > 1H > 15m > 5m hierarchy is valid.

Invalidation is evaluated from the safe last-closed 15m feed (`phase5SetupClose`), not the chart's 5m close. Lock-to-touch and touch-to-confirmation each require a later 5m bar, preserving chronological ordering in historical execution.

Before selection, the candidate builder also scans the current three-bar 5m window beginning at the close of `phase5SetupTime`. If any of those bars already overlapped the candidate, it is ineligible for a new lock even when the delayed confirmed 15m snapshot still reports `Fresh = true`. Therefore, the first accepted AOI touch must occur on a later 5m bar after locking.

`INVALIDATED` is visible on the invalidation bar. The next confirmed bar clears the copied lock and resumes searching. If a new eligible candidate exists, it can be locked on that next bar.

## Engine-7 handoff contract

The main public values are:

```text
phase6State
phase6Side
phase6AOITop
phase6AOIBottom
phase6Score
phase6Anchor
phase6SourceMask
phase6SourceCount
phase6Sources
phase6AOIOrigin
phase6AOIConfirmed
phase6LockTime
phase6Touched
phase6TouchTimestamp
phase6NearestLiquidity
phase6NearestLiquidityType
phase6NearestObstacle
phase6NearestObstacleType
phase6Confirmation
phase6ConfirmationScore
phase6ReadyTimestamp
phase6ReadyForRisk
phase6HandoffState
```

`phase6NearestObstacle` is the nearest active opposing Phase-5 zone in front of the AOI and before the selected target-side liquidity. It is context only; Engine 7 must still decide whether enough legal room exists after an exact entry is known.

The lock contract intentionally separates immutable setup identity from dynamic environment:

```text
Frozen while locked:
side, AOI top/bottom, anchor, score, source families, origin/confirmation, lock time

Refreshed from confirmed Phase 5 while state is 1–3:
nearest target-side liquidity/type, nearest opposing obstacle/type
```

The refresh never selects a new AOI and cannot change readiness. It reruns the existing liquidity and obstacle interpretation using the locked AOI boundary as its reference. On the one-bar `INVALIDATED` audit state, the original lock-time context remains available; the handoff is not ready for Engine 7 on that bar.

## Debug table

Rows 28–39 were added to the existing table:

```text
E6 direction context
E6 eligible / best score
E6 state
E6 side / AOI
E6 anchor
E6 source families
E6 locked score
E6 target liquidity
E6 nearest obstacle
E6 touched
E6 confirmation
E6 handoff
```

The `eligible` field counts only current candidates whose score reaches the configured minimum; it does not count every structurally valid candidate. The `best score` field can display `—` when that eligible count is zero, while `locked score` can still show the frozen value selected earlier. That is expected and demonstrates that the lock is independent of later candidate changes.

## Validation evidence

The original build was validated in TradingView on October 3, 2026 at approximately 22:46 Asia/Phnom_Penh. The three-fix build was compiled and runtime-checked again at approximately 23:09. The current-context repair was compiled and runtime-checked at approximately 23:35. The pre-lock chronology repair was compiled and recalculated at approximately 23:53. The supporting-confluence freshness repair was compiled and runtime-recalculated on October 4, 2026 at approximately 00:09, using the exact 2,129-line disk source recorded by the latest SHA-256 below.

- Symbol: `OANDA:XAUUSD`
- Chart timeframe: `5 minutes`
- Pine version: `v5`
- TradingView compiler: successful
- TradingView result: script added to chart
- Historical chart calculation: completed without an Engine-6 runtime error
- Rendered table: all twelve Engine-6 rows visible
- Active indicator title: `XAUUSD Smart Trade Core — Phase 5 + Engine 6`

Supporting-confluence repaired build current runtime snapshot:

```text
Direction context: MIXED
Eligible candidates / best score: 0 / —
State: READY_FOR_PHASE7
Side / AOI: LONG 4114.191–4115.791
Anchor: DEMAND
Independent sources: 1 | Demand
Locked score: 55.0
Target-side liquidity: 15M_SWING_HIGH 4187.810
Nearest obstacle: PIVOT_RESISTANCE 4142.961
Touched: true
Confirmation: REACTION | 2
Handoff: LONG READY
```

The existing historical AOI identity, score, source count, state, touch, confirmation, and handoff remained unchanged after the supporting-confluence repair because that lock had already progressed to `READY_FOR_PHASE7` with only its Demand anchor family. The environmental context remained on the current confirmed Phase-5 map. This verifies successful compilation, full recalculation, and non-regression of the locked-state handoff, but it does not by itself exercise the new supporting-zone exclusion path.

Three-fix build runtime snapshot before the current-context repair:

```text
Direction context: MIXED
Eligible candidates / best score: 0 / —
State: READY_FOR_PHASE7
Side / AOI: LONG 4114.191–4115.791
Anchor: DEMAND
Independent sources: 1 | Demand
Locked score: 55.0
Target-side liquidity: PDH 4275.325
Nearest obstacle: SUPPLY 4132.750
Touched: true
Confirmation: REACTION | 2
Handoff: LONG READY
```

This is transient historical/runtime state, not a permanent expected value. It confirms that the repaired source compiles, recalculates on the locked 5m chart, reports the corrected score-eligible count, and can reach READY only with touch plus a structural/reaction confirmation. It is not a substitute for observing every state transition step-by-step in controlled Bar Replay.

Original-build runtime snapshot before the repair:

```text
Direction context: MIXED
Valid candidates shown by the original debug build: 6
State: LOCKED_WAIT_TOUCH
Side / AOI: LONG 4118.300–4118.357
Anchor: DEMAND
Independent sources: 1 | Demand
Locked score: 55.0
Target-side liquidity: 15M_SWING_HIGH 4187.810
Nearest obstacle: PIVOT_RESISTANCE 4142.960
Touched: false
Confirmation: NONE | 0
Handoff: NO SETUP
```

This snapshot is transient market state, not a permanent expected value. The original `6` was the valid-candidate array size, not the true minimum-score-qualified count; that debug-reporting defect is corrected in the repaired build. The snapshot's important validation result is that Engine 6 locked a copy of an eligible AOI and did not emit READY before touch and post-touch confirmation.

The compiler reported six warnings at original Phase-5 lines 106, 109, 112, 115, 240, and 243. They are pre-existing implicit numeric-to-boolean conditions and are identical in the v4 Phase-5 source. No Engine-6 compiler error or warning was reported.

## Static checks

- 9 LONG anchor calls present.
- 9 SHORT anchor calls present.
- 0 FVG anchor calls present.
- No `strategy()`, `strategy.entry()`, `strategy.order()`, or `strategy.exit()` logic present.
- Original validated-build SHA-256 before the focused repair: `4d8fbf5bac918cb1aadf85685a31456432abc8b81cfdc82e1eed51277421b170`.
- Three-fix validated-build SHA-256: `74e260c0c70a5609d00416d39ea063a98009f911a7cac86cf436733d5efb1e57`.
- Current-context repaired and validated SHA-256: `4d67ac937943d4f6798cea4ad94188a270ed906f0d78d797e53196f46aaa25f5`.
- Pre-lock chronology repaired, compiled, and runtime-recalculated SHA-256: `962281462f23fd03b776f38558512a390ae25a73ed23bbf5b9b5814ce05e5ac2`.
- Supporting-confluence freshness repaired, compiled, and runtime-recalculated SHA-256: `83198948380c9bd7640e49baed1e3c5c3b12f632110a175f8b86611e802cc941`.

## Focused review repair

The exact original validated build was checked against the external review before any edit. Three reported defects were confirmed and corrected:

1. AOI invalidation now uses the safe confirmed 15m close (`phase5SetupClose`) instead of the chart's 5m `close`.
2. A persistent lock-bar index prevents historical price movement on the bar that created the lock from being counted retroactively as a touch.
3. The debug-table eligible count now increments only for candidates meeting `phase6MinimumScore`.

Candidate-specific premium/discount scoring and changing event timestamps from bar-open `time` to `time_close` were not included because the review identified them as optional semantic/design choices rather than confirmed defects.

### Current-context repair

A subsequent exact-build review identified one additional confirmed behavior: liquidity and obstacle values were copied at lock time and could become stale while the AOI remained locked. The visible mismatch between the current Phase-5 PDH and Engine-6's older locked PDH demonstrated the problem.

The repair keeps the AOI and all selection metadata immutable, retains the original lock-time context variables for audit, and refreshes only these public Engine-7 context outputs during `LOCKED_WAIT_TOUCH`, `TOUCHED_WAIT_CONFIRM`, and `READY_FOR_PHASE7`:

```text
phase6NearestLiquidity
phase6NearestLiquidityType
phase6NearestObstacle
phase6NearestObstacleType
```

No new detector, candidate family, score component, readiness rule, or Engine-7 risk logic was added. Event timestamps continue using the 5m bar-open `time`; changing them to `time_close` remains an optional metadata decision rather than part of this repair.

### Pre-lock touch chronology repair

The subsequent exact-source review confirmed one remaining timing gap. Phase 5 publishes the prior confirmed 15m candidate state, so its `Fresh` flag can remain true temporarily after price has already touched that zone during the current still-forming 15m interval.

`phase6_touched_since_setup_snapshot()` now derives the snapshot close from `phase5SetupTime + 15 minutes` and checks the current three 5m bars for zone overlap. `phase6_build_candidate()` rejects the anchor when such an overlap exists. The check applies only before a new lock; it does not alter a locked AOI, 15m invalidation, refreshed liquidity/obstacle context, scoring, or the post-lock touch and confirmation state machine.

The cutoff intentionally uses the confirmed snapshot candle's close rather than merely `time > phase5SetupTime`, because `phase5SetupTime` is that 15m candle's opening timestamp. This keeps the scan inside the current unconfirmed setup window and avoids treating price action from the confirmed snapshot candle itself as a new pre-lock touch.

### Supporting-confluence freshness repair

The next exact-source review confirmed that the anchor used effective freshness while supporting Demand/Supply, SMC OB, FVG, and Pivot S/R zones still relied only on the delayed Phase-5 `Fresh` flag. A supporting zone touched during the current unconfirmed 15m window could therefore add a source-family bit and quality points even though it was already used.

`phase6_current_fresh_overlap()` now requires all three conditions for each supporting zone: Phase-5 `Fresh`, no 5m touch since the confirmed snapshot closed, and price overlap with the anchor. `phase6_any_current_fresh_overlap()` applies that rule to all three published candidates in each family. The family is still counted at most once, FVG remains confluence-only, and all score weights and lock rules remain unchanged.

## Validation boundary

The supporting-confluence repaired source compiled successfully in TradingView, completed full historical recalculation on `OANDA:XAUUSD` 5m without a new runtime error, and rendered all twelve Engine-6 rows with the existing locked-state handoff unchanged. The compiler produced only the same six pre-existing Phase-5 warnings. Static inspection verifies that all eight side/family confluence branches use the new effective-freshness helper, the obsolete helper has no remaining call, and no protected Engine-6 behavior was changed.

A controlled Bar Replay that visibly catches an untouched anchor overlapping a supporting zone that was already touched during the current unconfirmed 15m window was not completed. The earlier pre-lock anchor rejection path and every state transition (`lock`, later-bar `touch`, later-bar CHoCH/reaction, `READY_FOR_PHASE7`, context changes during each locked state, confirmed-15m invalidation, and reset) also remain replay-test boundaries before Engine 7 consumes the handoff in production.
