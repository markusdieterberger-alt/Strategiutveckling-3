# C4 alpha1.1 — FVG semantic finding

Mobile alpha1 result:
- RAW L/S 59/55
- BODY displacement 97
- EDGE displacement 95
- SAME-type FVG after displacement: 0
- ANY-ahead FVG after displacement: 67
- execution FVG under SAME_TYPE default: 0

Interpretation:
The phrase “FVG in trade direction” cannot reasonably mean formation polarity matching trade direction in this target/magnet context.

A long target is an untouched FVG located ABOVE price; such a gap can naturally have bearish formation polarity. A short target is an untouched FVG BELOW price; such a gap can naturally have bullish formation polarity.

Therefore alpha1.1 changes execution semantics to:
- long: nearest untouched 1H/4H FVG above current price
- short: nearest untouched 1H/4H FVG below current price

Formation polarity remains stored and SAME_TYPE remains diagnostic only.

No threshold was changed. No performance result was used to tune the rule. This is a semantic/source correction driven by the gate funnel and the strategy's magnet definition.

Open item:
The alpha1 manual HTF engine produced 67 ANY-ahead opportunities versus ~74 in the earlier v1.2 diagnostic. That residual difference is kept open for later HTF/lifecycle parity QA; it does not justify reverting to SAME_TYPE.
