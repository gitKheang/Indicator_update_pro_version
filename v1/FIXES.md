# v1 wiring fixes

This repair addresses seven confirmed wiring and UI defects in `Indicator SMC & ICT & Indicators + Scalping Master for TradingView .pine`. It does not tune trading parameters or merge the indicator's independent systems.

## Fixed

1. **Pivot S/R ATR Length now works**
   - Added a Pivot-specific `ta.atr(atrLen)` calculation.
   - Pivot zone width now uses that value instead of the SMC module's global ATR(200).
   - The global ATR remains unchanged for Order Blocks and candle-pattern filters.

2. **Demand/Supply alert switches now work**
   - `Demand` and `Supply` alert toggles now gate both Hit and Near `alert()` calls.
   - Disabled alerts no longer update Near-alert repeat tracking.

3. **Supply-zone deactivation uses the correct visibility switch**
   - Demand boxes use `showDemandZone`.
   - Supply boxes use `showSupplyZone`.

4. **Pivot S/R alert conditions respect Detection settings**
   - Breakout, breakdown, resistance/support break, false-break, and support/resistance reaction alert conditions now use the same gated signals as their chart markers.

5. **Daily/Weekly/Monthly line styles are independent**
   - The high/low drawing function now receives the correct style for each timeframe.

6. **Removed the unused `directions` checkbox**
   - It was a dead input with no effect on calculations, display, or alerts.
   - The working dashboard controls and per-indicator order settings are unchanged.

7. **Corrected the Demand tooltip type**
   - A Demand-zone tooltip that identified itself as Supply now passes the Demand type.

## Intentionally unchanged

- SMC Internal/Swing Structure and BOS/CHoCH logic
- Internal and Swing Order Blocks
- EQH/EQL and Fair Value Gaps
- Premium/Equilibrium/Discount zones
- Demand/Supply detection rules and default thresholds
- Pivot locations, source, left/right lengths, and zone-width default
- Candle-pattern rules
- Nine-indicator dashboard calculations and ordering
- BULB and ATR-envelope parameters

## Validation status

- Confirmed each reported defect existed in the exact `v1` source before editing.
- Completed static post-edit checks for repaired variable wiring and balanced delimiters.
- Pasted the exact repaired local source into TradingView Pine Editor.
- TradingView Pine v5 reported `Compiled.` and `Added to chart.`.
- The indicator rendered on the open OANDA:XAUUSD 15-minute replay chart without a visible runtime error.
- Reload/replay-equivalence and strategy-performance testing were not performed; this repair validates wiring and platform loading, not profitability.
