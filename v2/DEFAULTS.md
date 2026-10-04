# v2 default configuration

This version changes presentation defaults only. Signal calculations, thresholds, colors, alerts, and engine logic remain unchanged from v1.

## Changed from v1

- Swing Order Blocks: **ON**
- Fair Value Gaps: **ON**

## Enabled by default

- Internal Structure
- Swing Structure
- Strong/Weak High and Low
- Internal Order Blocks
- Swing Order Blocks
- EQH/EQL
- Fair Value Gaps
- Demand zones
- Supply zones
- Pivot Highs
- Pivot Lows
- Align Zones
- Wait For Confirmed Bar
- Direction Dashboard
- BULB
- ATR Bands

ATR Bands do not have a visibility input in this script. Their three plots are always active, so they are effectively enabled by default.

## Disabled by default

- Color Candles
- Internal Structure Confluence Filter
- Swing Point labels
- Previous Daily High/Low
- Previous Weekly High/Low
- Previous Monthly High/Low
- Premium/Discount/Equilibrium drawing
- Breakout and Breakdown markers
- Resistance and Support break markers
- False-break markers
- Support and Resistance reaction markers
- TSI Curl markers
- All candle-pattern detectors
- Candle-pattern labels
- Candle-pattern boxes

## Intentionally unchanged

- Market Structure, BOS, and CHoCH calculations
- Internal and Swing Order Block calculations
- EQH/EQL calculations
- FVG detection and invalidation
- Demand/Supply detection, lifecycle, and alerts
- Pivot S/R calculations and alerts
- Direction Dashboard calculations
- BULB calculations
- ATR Band parameters and calculations
- All numeric defaults and visual colors

## Validation

- Audited all 42 requested visibility and detection defaults in the exact v2 source.
- Static delimiter check passed.
- The only source differences from v1 are the two requested default changes.
- TradingView accepted the updated Pine v5 source and rendered it on OANDA:XAUUSD 15 minutes without a compile error.
- TradingView still reports pre-existing type/consistency warnings; these were outside this default-only change.
- Reload equivalence and strategy-performance testing were not performed.
