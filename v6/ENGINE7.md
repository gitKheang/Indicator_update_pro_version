# Engine 7 — Exact Trade Construction and Signal UI

## Status

Engine 7 is implemented in `XAUUSD Smart Trade Core - Phase 5.pine` inside `v6`.

It is an additive trade-construction layer. It consumes the confirmed Engine 6 handoff and does not create a second AOI detector, change Engine 6 scoring, or merge the meanings of SMC Order Blocks, Demand/Supply zones, Pivot S/R zones, FVGs, and liquidity levels.

## Processing contract

Engine 7 processes each confirmed Engine 6 `READY_FOR_PHASE7` timestamp once, including the first timestamp after script initialization. A newer READY event is ignored while another Engine 7 package is pending, live, or awaiting Engine 8 ambiguity resolution. That event is recorded as `IGNORED_READY_BUSY` without overwriting the active package's construction reason or `phase7SetupId`.

The touch-to-READY impulse is frozen as follows:

- Long: `A = lowest low`, followed chronologically by `B = highest high after A`, from the Engine 6 touch bar through the READY bar.
- Short: `A = highest high`, followed chronologically by `B = lowest low after A`, over the same window.
- Impulse size: `abs(B - A)`.
- Quality: `impulse size / confirmed exec5mATR`.
- Default minimum quality: `0.75 ATR`, configurable with `Minimum impulse / ATR`.

If a later price extreme replaces A, the earlier B is discarded and must be rebuilt after the new A. This prevents a backward-in-time high/low pair from being treated as a directional impulse.

The history lookup is limited to 499 bars to respect the script's `max_bars_back=500` contract. A longer touch-to-READY span is rejected explicitly as `IMPULSE_HISTORY_TOO_LONG`; Engine 7 does not silently truncate the impulse. Missing/zero-length history and a window with no valid A-before-B sequence are rejected as `INVALID_IMPULSE_HISTORY` and `INVALID_IMPULSE_SEQUENCE`.

## Entry construction

Both retracement entries are evaluated independently:

- Long F38.2: `B - 0.382 × impulse`.
- Long F61.8: `B - 0.618 × impulse`.
- Short F38.2: `B + 0.382 × impulse`.
- Short F61.8: `B + 0.618 × impulse`.

At the READY close, a long retracement must still be below price (`close > entry`) and a short retracement must still be above price (`close < entry`). Otherwise that candidate is rejected as `ENTRY_ALREADY_PASSED`; Engine 7 does not create a retroactive pending order.

The fixed XAUUSD stop distance is exactly `10.0` price units:

- Long: `SL = entry - 10.0`, valid only when the SL is at or below the locked AOI bottom.
- Short: `SL = entry + 10.0`, valid only when the SL is at or above the locked AOI top.

This means the fixed stop must clear the structural invalidation boundary; it is not widened dynamically and is not converted through broker pip conventions.

If the fixed stop fails this boundary rule, the diagnostic reason is `FIXED_SL_DOES_NOT_CLEAR_AOI`. The name describes the failed condition directly: being beyond the AOI is required, while remaining inside it is invalid.

## Structural target selection

Engine 7 reuses the confirmed structures already published by Phase 5. It does not introduce a new target detector.

For a long candidate, the target pool contains:

- Liquidity: 15m EQH pools, previous day/week/month highs, confirmed 15m swing high, and confirmed 4H high.
- Opposing structures: 15m Supply, bearish SMC Order Blocks, bearish FVGs, and Pivot Resistance zones.

For a short candidate, the inverse pool contains:

- Liquidity: 15m EQL pools, previous day/week/month lows, confirmed 15m swing low, and confirmed 4H low.
- Opposing structures: 15m Demand, bullish SMC Order Blocks, bullish FVGs, and Pivot Support zones.

Zone targets use the first boundary price would meet. The nearest distinct eligible structure becomes TP1. The next farther distinct structure becomes TP2.

Point-liquidity objectives receive one additional timing check. Because Phase 5 publishes the prior confirmed 15-minute snapshot, Engine 7 scans the current 15-minute window from that snapshot's close through the READY/current bar. A long-side point is excluded if a current-window high has already reached it; a short-side point is excluded if a current-window low has already reached it. This applies only to EQH/EQL, previous day/week/month highs or lows, confirmed 15-minute swing highs or lows, and confirmed 4-hour highs or lows. Supply/Demand, Order Block, FVG, and Pivot S/R zones are not removed by this test because a previously tested zone can still be a valid reaction target and is not equivalent to consumed point liquidity.

A candidate is valid only when all conditions pass:

1. Its retracement remains pending on the correct side of the READY close.
2. The fixed $10 stop clears the locked AOI boundary.
3. A first real structural target exists.
4. TP1 offers at least `1.5R` from the exact candidate entry.
5. A distinct farther TP2 exists.

If both F38.2 and F61.8 are valid, Engine 7 chooses the candidate with the larger TP2 R multiple; TP1 R is the tie-breaker.

## Frozen lifecycle

State codes are:

- `NO_TRADE`
- `PENDING_ORDER`
- `LIVE_TRADE`
- `AMBIGUOUS_FILL`

Closed and cancelled outcomes return the active state to `NO_TRADE`, while their terminal result remains available in `phase7LastStatus`. Only filled trades enter the frozen historical trade UI; cancelled pending packages remain audit-visible through status/reason/event outputs but are not archived as trades.

Pending values never chase price. The confirmed-bar decision priority is:

1. Parent Engine 6 AOI invalidation cancels the pending child package.
2. If the parent remains valid, an exact entry touch fills the package.
3. If entry was not touched, the configurable pending duration can expire (default 24 five-minute bars).
4. If entry was not touched, TP1 reached first cancels the package as `MISSED_ENTRY`.

This keeps confirmed parent validity authoritative while the order is pending. After a non-ambiguous fill on an earlier bar, Engine 7 follows its frozen trade package independently.

An entry fills only when the confirmed candle range contains the exact entry: `low <= entry and high >= entry`.

If the fill candle also contains SL, TP1, or TP2, Engine 7 marks `phase7FillBarAmbiguous = true`, enters the dedicated `AMBIGUOUS_FILL` state, publishes `AMBIGUOUS_FILL_BAR`, and raises `phase7NewAmbiguousFill`. It records the fill candle's OHLC and does not invent the intrabar sequence. Engine 7 freezes all later TP/SL outcome processing for that package; only Engine 8 may resolve whether the trade survived the fill candle. The unresolved package intentionally continues to occupy the single active slot so a newer READY cannot overwrite it.

Normal exit testing starts on the bar after the fill candle. If a later OHLC candle contains both SL and a target, Engine 7 applies a conservative stop-first rule. `STOP_AFTER_TP1` is used only when TP1 was confirmed on an earlier bar; TP1 touched for the first time on the same stop bar is not credited before the stop. A standalone TP1 touch updates `phase7TP1Hit` and the TP1 label immediately while the package remains live for TP2 or SL.

## Signal UI

The signal UI follows the supplied right-label level style:

- Entry: blue.
- SL: red.
- TP1: orange.
- TP2: teal.
- Pending preview: faint dashed lines and `◇ Pending` labels.
- Filled trade: solid two-pixel lines beginning at the exact fill candle.
- Ambiguous fill: warning entry label and orange debug-state cell while the package remains frozen for Engine 8 resolution.
- TP1 hit: the orange label changes to `TP1 ✓ HIT` immediately, without waiting for final closure.
- Labels remain on the right and move with the current bar using the configurable offset.
- Filled trades freeze and fade after closure instead of continuing to move.
- Cancelled, expired, or missed pending packages have their preview removed and do not consume a filled-trade history slot.

The UI stores the two most recent completed filled trades and displays at most two packages at once:

- With a current pending/live/unresolved package: current plus the most recent completed filled trade.
- With no current package: the two most recent completed filled trades.

When a pending preview is enabled, the second historical trade is hidden rather than deleted. Cancelling, expiring, or missing that pending entry removes the preview and restores the second historical trade. The older history is permanently deleted only when the new package actually fills. With the pending preview disabled, both historical trades remain visible while the order waits, and the second history is deleted at fill.

Only one Engine 7 trade package can be pending, live, or unresolved at a time.

## Engine 8 handoff

The stable construction/lifecycle outputs available to Engine 8 are:

- Identity and direction: `phase7SetupId`, `phase7Side`, `phase7EntryKind`.
- Frozen impulse: `phase7ImpulseA`, `phase7ImpulseB`, `phase7ImpulseSize`, `phase7ImpulseATR`, `phase7ImpulseStrength`.
- Frozen trade package: `phase7Entry`, `phase7SL`, `phase7TP1`, `phase7TP2`.
- Target identity and R: `phase7TP1Kind`, `phase7TP2Kind`, `phase7TP1R`, `phase7TP2R`.
- Lifecycle: `phase7State`, `phase7TradeValid`, `phase7ReadyForEngine8`, `phase7FillTimestamp`, `phase7TP1Hit`.
- Ambiguous-fill handoff: `phase7FillBarAmbiguous`, `phase7NewAmbiguousFill`, `phase7FillOpen`, `phase7FillHigh`, `phase7FillLow`, `phase7FillClose`.
- Audit/status: `phase7Reason`, `phase7LastStatus`, `phase7LastEvent`.
- Event pulses: `phase7NewPackage`, `phase7NewFill`, `phase7NewAmbiguousFill`, `phase7NewClose`.

Four alert conditions correspond to valid package creation, unambiguous exact entry fill, ambiguous fill-candle detection, and trade closure/cancellation. An ambiguous fill raises only the dedicated ambiguity alert; it does not also claim that the trade is live.

## Debug table

Rows 40–48 show Engine 7 state, last status, construction/lifecycle reason, most recent event, ambiguous-fill state, chronological impulse A/B, impulse-to-ATR strength, selected side/entry, fixed SL, TP1/R, and TP2/R.

## Validation record

The pre-review build was validated on 2026-10-04 in TradingView using OANDA:XAUUSD on the required 5-minute chart:

- Pine v5 compilation completed successfully at 01:45:20 Asia/Phnom_Penh.
- The final 2,504-source-line build was added to the chart (the Pine editor caret reported line 2,505 after the terminal newline).
- The chart legend exposed the Engine 7 defaults `0.75`, `24`, and label offset `3`.
- No Engine 7 compiler error or visible runtime error was present after full historical chart calculation.
- Static checks confirmed no tab characters or trailing whitespace and balanced delimiter counts.

That record applies to the earlier 2,504-line build, before the review corrections documented above.

The corrected 2,581-line build was freshly validated on 2026-10-04 in TradingView using OANDA:XAUUSD on the required 5-minute chart:

- Pine v5 compilation and chart update completed successfully at 02:15:32 Asia/Phnom_Penh.
- The Pine editor reported line 2,582 after the terminal newline, matching the 2,581-line local source.
- Corrected local source SHA-256: `565a5ee4f8b4c79866cb0d9d5e52b10e32e976adee2f6ecb4f891e5af17a2df8`.
- TradingView reported only the six pre-existing Lean Core bool-conversion warnings at lines 106, 109, 112, 115, 240, and 243. No Engine 7 compiler error was present.
- The chart completed its historical calculation with no visible runtime error and displayed the expanded Engine 7 debug rows through TP2.
- Direct runtime evidence showed Engine 6 at `READY_FOR_PHASE7` / `LONG READY` and Engine 7 at `NO_TRADE` with `INVALID_IMPULSE_SEQUENCE` / `READY_REJECTED`. This proves the corrected first-READY intake executed instead of remaining at the initial `NO_SETUP` state, and that the chronological impulse guard actively rejected the observed non-directional sequence.
- Static checks confirmed no tab characters or trailing whitespace.

Controlled Bar Replay coverage of every pending/fill/TP/SL branch remains pending and is still required before Engine 8 execution modeling. Compilation and this live historical state do not, by themselves, prove every lifecycle branch.

## Post-review verification of the 2,616-line snapshot

The two supplied external reviews describe the earlier 2,581-line snapshot with SHA-256 `565a5ee4f8b4c79866cb0d9d5e52b10e32e976adee2f6ecb4f891e5af17a2df8`. The source reviewed afterward was 2,616 lines with SHA-256 `390b8c6a4d7d3a10514239d36f41a27e03bd434be5e44ac0aaaea4e1078130a0` after removal of one non-functional trailing space.

All three reported Engine-7 concerns were already resolved in that snapshot:

- **Parent invalidation versus fill:** `phase7CancelPending` is true whenever `phase7ParentInvalid` is true, and cancellation is evaluated before the entry-fill branch. A pending child therefore cannot become live on the same confirmed bar that Engine 6 invalidates its parent AOI.
- **Ambiguous fill continuation:** a fill candle containing Entry plus SL, TP1, or TP2 moves the package to dedicated state code `3` (`AMBIGUOUS_FILL`). Normal exit simulation requires state code `2`, so later bars cannot manufacture a TP/SL result for an unresolved fill. The package remains occupied for Engine 8.
- **Delayed point-liquidity targets:** `phase7_add_liquidity_target()` calls `phase7_liquidity_still_unswept()` before adding EQH/EQL, previous day/week/month levels, or confirmed 15m/4H swing levels. On the required 5-minute chart, offsets `0..2` cover the active three-bar 15-minute window after the last confirmed setup snapshot. Opposing D/S, OB, FVG, and Pivot S/R zones remain separate structural targets and are intentionally not filtered as consumed point liquidity.

No Pine logic was changed during that post-review because changing already-correct branches would create unnecessary regression risk. Local checks confirmed the three protections are wired into their consumers and found no formatting or delimiter defect. The open TradingView chart showed the Engines 6-7 indicator on OANDA:XAUUSD 5m with no visible runtime error, but the editor was not holding the exact local source; therefore this is not recorded as a fresh exact-source compile.

## Final Engine-7 consistency repair

The later external review identified four additional presentation/diagnostic inconsistencies in the 2,616-line snapshot. The current 2,610-line source, SHA-256 `597c6847755b9540946f0c1931d970a4bbac67eb0f1abc718e0491fd72a5feef`, applies only these scoped corrections:

- The no-preview fill branch now reapplies the warning Entry label when the fill candle is ambiguous.
- A cancelled pending package deletes its preview without rotating or deleting either filled-trade history slot.
- The normal fill alert is gated by `not phase7FillBarAmbiguous`, leaving ambiguous fills to the dedicated alert.
- The failed fixed-stop boundary reason is now `FIXED_SL_DOES_NOT_CLEAR_AOI`.

These changes do not alter Phase 5, Engine 6, impulse construction, F38.2/F61.8 prices, the fixed `$10` stop calculation, target selection, or lifecycle state transitions. Local static checks passed, but this exact SHA has not been compiled or replayed in TradingView. A fresh exact-source compile and controlled Bar Replay matrix are still required before calling every lifecycle and UI path runtime-validated.

## History2 pending-lifecycle repair

The subsequent source review confirmed that package creation still permanently deleted the second completed-trade history before the pending order had filled. The repair now:

- temporarily hides History2 only while an enabled pending preview is visible;
- restores History2 when the pending package is cancelled, expired, or missed;
- keeps both histories visible during a pending order when preview is disabled; and
- permanently deletes History2 only after an exact entry fill, including an unresolved ambiguous fill.

The repaired Pine source is 2,626 lines with SHA-256 `db03a0ddaedf3f2c1c35a247417a7bda67912bb9930d2ba43a37bf79b698cccb`. Local checks found balanced delimiters, no tab characters, no trailing whitespace, and the expected hide/restore/delete call placement.

No entry, stop, target, impulse, parent-invalidation, or ambiguity rule was changed. This exact source still requires TradingView compilation and controlled replay of preview-on cancellation, preview-off waiting/fill, normal fill, and ambiguous fill before the UI lifecycle is considered runtime-validated.
