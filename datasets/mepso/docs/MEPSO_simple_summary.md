# MEPSO dataset practical summary

## What to forecast

For a straightforward operational task, start with final aFRR or mFRR upward and downward activated energy. These columns have broad coverage and describe balancing actions relevant to flexibility planning. Keep downward values in their published sign.

For a financial task, use the imbalance settlement price that the CSV now derives from the components: `imbalance_price_surplus_eur_per_mwh` and `imbalance_price_deficit_eur_per_mwh` (final, else preliminary; `imbalance_price_version` says which, and the per-release columns are kept).

## Can the prices be combined

Yes, and the CSV now does it. MEPSO's rules (Articles 83–84) use one imbalance price per hour, chosen from the activated balancing energy:

- **WAPpos**, the weighted average price of the activated upward energy, when more upward than downward energy was activated (system short);
- **WAPneg**, the weighted average price of the activated downward energy, when more downward energy was activated (system long);
- **VAA**, when nothing was activated. Only VAA is a dual price: VAA+ (HUPX − 50 %) for a surplus, VAA− (HUPX + 50 %) for a deficit.

So the CSV gives a surplus price and a deficit price, equal in every WAP hour. Making upward prices positive and downward prices negative would still be wrong: direction and price sign are different things, and every component can be negative. Details, coverage and validation: README_mepso.txt.

## What remains missing

Combining columns cannot invent prices for entirely missing periods. March–June 2023 is absent, one repeated autumn hour is missing in October 2022, and late October 2026 lacks prices. May and September 2026 have preliminary sources only; October also has no final workbook, and its preliminary prices stop after October 21.

## Useful inputs

Calendar features are known ahead of time. Past prices, ACE and balancing activations are possible inputs only if their values were available when the forecast would have been issued. Same-hour realized data would leak the answer. This monthly archive does not establish live publication times.

## What to keep as references

Keep MKD prices for currency checks rather than as independent targets. Keep revision labels, filenames and missing-data flags for tracing and filtering. Reserve totals can duplicate directional information within a consistent period, but their signed versus gross conventions vary; prefer the directional columns initially. ACE is a separate operational quantity, not a duplicate of activated energy.

## Further reading

The detailed README includes monthly quality tables and column recommendations. Domain references: [MEPSO balancing rules, Articles 83–86](https://www.mepso.com.mk/docs/pbee/en/Electricity%20balance%20market%20rules%20-%20consolidated%20text.pdf) and [ENTSO-E electricity balancing](https://www.entsoe.eu/network_codes/eb/).

These recommendations use coverage and domain reasoning. No forecasting experiments were performed.

## Applied scalar price update

The CSV now also has final_price_applied_eur_per_mwh and preliminary_price_applied_eur_per_mwh. Both reproduce every January 2026 settlement reference price. Clear source-based choices are filled; different fallback prices without a matching reference remain blank. Their selection status, component and source columns explain each result. Existing surplus/deficit prices remain available for portfolio-specific fallback handling. The January reference is evidence about observed settlement labels, not information available to a future forecast.
