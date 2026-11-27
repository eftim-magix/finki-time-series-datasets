# MEPSO monthly data quality and forecasting columns

Use an **applied EUR settlement-price series** as a priority target for financial forecasting: the merged CSV now contains it as derived columns (`imbalance_regime`, `imbalance_price_surplus_eur_per_mwh`, `imbalance_price_deficit_eur_per_mwh`, plus `preliminary_`/`final_` variants; rule and definitions in README_mepso.txt). They reproduce the plant settlement workbooks' `MEPSO Price` in 99.3% of the January–October 2026 hours that have a derived price. Use the final activated aFRR and mFRR up/down columns when operational forecasting and coverage are the priority. Keep MKD prices as references. High fill rates alone do not make a column a useful target: exchange rates, timestamps and revision metadata have different roles.

This report describes `MEPSO_balancing_prices_hourly.csv` and its existing column definitions. Recommendations combine completeness counts with the domain sources below; they are not claims about achieved forecast accuracy. No forecasting models or experiments were run.

## Dataset coverage

<!-- BEGIN SNAPSHOT -->

As of **2026-11-27**: **59,904 rows**, **82 local calendar months**, **59,904 expected UTC hours**, and **0 absent timestamp rows**. There are **2,928 hours without source measurements**, **3,169 hours without any EUR price component in either version**, and **1,970 hours with preliminary EUR prices and no final EUR price**.

Dataset SHA-256: `bc95f898560617438345c57c803a2b768c0cbe975ee58c5bb65af94635b7eb87`.

<!-- END SNAPSHOT -->

Counts use **local calendar months in Europe/Skopje**, with their actual UTC hours. A month can have 743 or 745 hours because of daylight saving. The CSV keeps a continuous UTC grid; an existing timestamp row can still contain no measurements. The scope ends at the last source month, October 2026, so unpublished November 2026 is outside this snapshot.

There are four different meanings of missingness:

1. **Missing timestamp row:** an expected UTC interval is absent from the CSV itself.
2. **No measurements:** neither version supplies any price or activated-energy/ACE value; a daily exchange rate alone does not count as a balancing measurement.
3. **No EUR price:** all four EUR components are blank for the specified version, or for both versions when labelled “either.” A supplied numeric zero counts as present.
4. **Missing individual parameter:** that exact column is blank. This includes unavailable files, historical tables that were not published, and blank cells inside published tables. It does not establish that the physical quantity was zero.

“Either version” means availability in at least one version. It is a **coverage union**, not a recommendation to fill intentional final blanks with preliminary component values. The hourly CSV and its prices have not been changed by this report.

## Important gaps and changes

- **March–June 2023:** no source measurements for 2,927 actual hours. March includes a spring transition. Keep these gaps explicit rather than training on invented zeros.
- **October 30, 2022 at 01:00 UTC:** the second local 02:00 interval is missing from both source versions. The other autumn hour is a separate observation.
- **October 22–31, 2026:** 241 hours have no EUR price components, while balancing-energy or other parameters can still be available. The preliminary price coverage is therefore shorter than the source file's nominal month.
- **March 2020 preliminary:** the archive's original file contains June data and is excluded. **September 2026 final:** the archive points to a September 2025 file, which is not a final September 2026 observation.
- **Historical format changes:** early net-energy columns, later directional/total columns, and missing early ACE tables describe different reporting layouts. A blank early directional/total/ACE column need not mean a lost hourly record.
- **Price components:** a blank WAP or VAA cell is different from an hour in which every EUR component is absent. Earlier zero-filled rows and later sparse component reporting should not be treated as one uniform economic regime. Keep the raw blanks and zeros separate.
- **Reserve totals:** reported `*_total_mwh` values cannot be treated as one consistent definition across the archive. Some periods align with signed `up + down`, others with gross `up + abs(down)`, and some values agree with neither. The directional down series contains negative values. Do not combine totals across regimes as if their definitions were fixed; inspect [the monthly arithmetic checks](../summary/mepso_reserve_total_checks.csv). These are direct value checks, not forecasting experiments.

## Coverage by column

Add `final_` or `preliminary_` to each suffix below to get an actual CSV column name. Percentages use all expected hours, including missing months. “Final zeros” counts literal numeric zero cells; it does not infer inactivity or validate a price. The full per-version, per-month counts are in [mepso_monthly_column_quality.csv](../summary/mepso_monthly_column_quality.csv).

<!-- BEGIN COVERAGE -->

| Metric suffix | Final filled | Final coverage | Preliminary filled | Either version filled | Final zeros |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ace_mwh_per_h` | 53,154 | 88.73% | 40,797 | 54,690 | 2 |
| `afrr_down_mwh` | 54,023 | 90.18% | 46,391 | 55,991 | 32,675 |
| `afrr_net_mwh` | 2,183 | 3.64% | 1,440 | 2,183 | 422 |
| `afrr_total_mwh` | 52,584 | 87.78% | 46,776 | 54,793 | 13,331 |
| `afrr_up_mwh` | 54,023 | 90.18% | 46,391 | 55,991 | 30,879 |
| `exchange_rate_mkd_per_eur` | 54,765 | 91.42% | 47,085 | 56,733 | 0 |
| `imbalance_price_deficit_eur_per_mwh` | 54,765 | 91.42% | 47,831 | 56,735 | 5 |
| `imbalance_price_surplus_eur_per_mwh` | 54,765 | 91.42% | 47,831 | 56,735 | 5 |
| `mfrr_down_mwh` | 54,023 | 90.18% | 46,391 | 55,991 | 35,685 |
| `mfrr_net_mwh` | 2,183 | 3.64% | 1,440 | 2,183 | 859 |
| `mfrr_total_mwh` | 52,584 | 87.78% | 46,776 | 54,793 | 19,544 |
| `mfrr_up_mwh` | 54,023 | 90.18% | 46,391 | 55,991 | 37,977 |
| `price_applied_eur_per_mwh` | 48,990 | 81.78% | 42,657 | 50,872 | 4 |
| `price_vaa_minus_eur_per_mwh` | 30,154 | 50.34% | 27,542 | 30,329 | 24,376 |
| `price_vaa_minus_mkd_per_mwh` | 30,156 | 50.34% | 26,798 | 30,329 | 24,376 |
| `price_vaa_plus_eur_per_mwh` | 30,154 | 50.34% | 27,542 | 30,329 | 24,376 |
| `price_vaa_plus_mkd_per_mwh` | 30,156 | 50.34% | 26,798 | 30,329 | 24,376 |
| `price_wapneg_eur_per_mwh` | 41,516 | 69.30% | 37,084 | 42,663 | 16,333 |
| `price_wapneg_mkd_per_mwh` | 41,516 | 69.30% | 36,340 | 42,663 | 16,333 |
| `price_wappos_eur_per_mwh` | 38,533 | 64.32% | 34,325 | 39,275 | 14,732 |
| `price_wappos_mkd_per_mwh` | 38,533 | 64.32% | 33,581 | 39,275 | 14,732 |

<!-- END COVERAGE -->

## Monthly quality summary

Every number below is a count of actual hours. `EUR missing F/E` means **no final EUR price / no EUR price in either version**. `P only EUR` means at least one preliminary EUR component is present and every final EUR component is blank. `U/D` gives separate up/down missing counts. Parameter and FX missing counts use availability in either version; they are not strict-final completeness counts. FX is the published MKD-per-EUR exchange rate. See the per-column file for final-only and preliminary-only parameter gaps, including totals and early net series.

<!-- BEGIN MONTHLY -->

| Month | Expected hours | No measurements | EUR missing F/E | P only EUR | aFRR missing U/D | mFRR missing U/D | ACE missing | FX missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2020-01 | 744 | 0 | 0/0 | 0 | 744/744 | 744/744 | 744 | 0 |
| 2020-02 | 696 | 0 | 0/0 | 0 | 0/0 | 0/0 | 696 | 0 |
| 2020-03 | 743 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-04 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-05 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-06 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-07 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-08 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-09 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-10 | 745 | 0 | 0/0 | 0 | 0/0 | 0/0 | 1 | 1 |
| 2020-11 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2020-12 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-01 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-02 | 672 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-03 | 743 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-04 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-05 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-06 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-07 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-08 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-09 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-10 | 745 | 0 | 0/0 | 0 | 0/0 | 0/0 | 1 | 1 |
| 2021-11 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2021-12 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-01 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-02 | 672 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-03 | 743 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-04 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-05 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-06 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-07 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-08 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-09 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-10 | 745 | 1 | 1/1 | 0 | 1/1 | 1/1 | 1 | 1 |
| 2022-11 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2022-12 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2023-01 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2023-02 | 672 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2023-03 | 743 | 743 | 743/743 | 0 | 743/743 | 743/743 | 743 | 743 |
| 2023-04 | 720 | 720 | 720/720 | 0 | 720/720 | 720/720 | 720 | 720 |
| 2023-05 | 744 | 744 | 744/744 | 0 | 744/744 | 744/744 | 744 | 744 |
| 2023-06 | 720 | 720 | 720/720 | 0 | 720/720 | 720/720 | 720 | 720 |
| 2023-07 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2023-08 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2023-09 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2023-10 | 745 | 0 | 0/0 | 0 | 0/0 | 0/0 | 25 | 0 |
| 2023-11 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2023-12 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 24 | 0 |
| 2024-01 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-02 | 696 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-03 | 743 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-04 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-05 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-06 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-07 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-08 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-09 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-10 | 745 | 0 | 0/0 | 0 | 0/0 | 0/0 | 121 | 0 |
| 2024-11 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2024-12 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-01 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-02 | 672 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-03 | 743 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-04 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-05 | 744 | 0 | 2/0 | 2 | 0/0 | 0/0 | 0 | 0 |
| 2025-06 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-07 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-08 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-09 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-10 | 745 | 0 | 0/0 | 0 | 0/0 | 0/0 | 1 | 0 |
| 2025-11 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2025-12 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-01 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-02 | 672 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-03 | 743 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-04 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-05 | 744 | 0 | 744/0 | 744 | 0/0 | 0/0 | 0 | 0 |
| 2026-06 | 720 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-07 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-08 | 744 | 0 | 0/0 | 0 | 0/0 | 0/0 | 0 | 0 |
| 2026-09 | 720 | 0 | 720/0 | 720 | 0/0 | 0/0 | 312 | 0 |
| 2026-10 | 745 | 0 | 745/241 | 504 | 241/241 | 241/241 | 361 | 241 |

<!-- END MONTHLY -->

## Periods with preliminary EUR prices only

The major periods are May 2026, September 2026 and October 1–21, 2026. The exact ranges below include isolated currency-specific gaps where final MKD data can exist but final EUR data do not. They are defined from EUR cells, so they need not equal the hourly CSV's general `status=preliminary_only`, which also recognizes MKD prices. Boundaries are UTC; the end is exclusive.

At the **workbook level**, May 2026, September 2026 and October 2026 have preliminary sources and no valid final monthly workbook in this collection. October's preliminary file covers the nominal month, but EUR prices are populated only through October 21; some other preliminary parameters continue beyond that date. Thus “only preliminary source data” covers the full October source month, while “preliminary EUR price available” covers only its first 504 hours.

<!-- BEGIN PRELIMINARY -->

| Start UTC inclusive | End UTC exclusive | Hours |
| --- | --- | ---: |
| 2025-05-18T03:00:00+00:00 | 2025-05-18T05:00:00+00:00 | 2 |
| 2026-04-30T22:00:00+00:00 | 2026-05-31T22:00:00+00:00 | 744 |
| 2026-08-31T22:00:00+00:00 | 2026-10-21T22:00:00+00:00 | 1224 |

<!-- END PRELIMINARY -->

For final-label training, these hours lack a final EUR target. Preliminary values can be retained as provisional labels in a separate labelled view; do not silently call them final or treat the preliminary and final versions of an hour as two independent observations.

## Domain interpretation

MEPSO describes aFRR as automatically activated frequency restoration and mFRR as manually activated restoration. Its settlement methodology distinguishes WAPpos, WAPneg and the value of avoided activation, with the relevant component depending on activated energy. VAA fallback values can depend on the HUPX day-ahead price. The archive's component columns are not a ready-made universal scalar settlement price. [MEPSO consolidated rules, Articles 2 and 83–84, April 2025](https://www.mepso.com.mk/docs/pbee/Precistena%20verzija%20na%20Pravila%20za%20balansiranje_30%2004%202025.pdf).

Balancing service providers offer flexibility, while balance responsible parties manage and settle portfolio deviations. Forecasting activation volumes can therefore support flexibility planning; forecasting applicable imbalance prices can support financial exposure and nomination decisions. Those applications motivate the recommendations here. [ENTSO-E electricity balancing overview](https://www.entsoe.eu/network_codes/eb/).

ACE measures a control area's interchange deviation with frequency effects taken into account. It is not automatically the same quantity as the system's imbalance before reserve activation. Treat the published hourly `ace_mwh_per_h` as its own operational series, not as a substitute for activated energy or a reconstructed portfolio imbalance. [ENTSO-E aFRR study, glossary](https://eepublicdownloads.entsoe.eu/clean-documents/mc-documents/balancing_ancillary/160229_Report_aFRR_study_merit_order_and_harmonising_FAT_%28vs_1.2%29.pdf), [Nordic TSO explanation of ACE and ACE open loop](https://nordic-balancing.pages.fifty.eu/information/TSO-TSO/BusinessRequirementSpecification/aceol/index.html). The conceptual distinction is useful here; Nordic market rules are not being applied to MEPSO.

The April 2025 consolidation is a domain reference, not evidence that every rule or reporting convention was unchanged throughout 2020–2026. Reconstructing an authoritative settlement price would require matching the rule effective in each historical period.

## Combining positive and negative price components

Combining complementary price components can reduce apparent sparsity, but it cannot recover genuinely missing hours. At least one of the two final EUR WAP components is present in 52,330 of 59,904 hours (87.36%). Including the VAA components raises the availability ceiling to 54,765 hours (91.42%). These are presence counts, not counts of validated combined settlement prices: both WAP fields can be populated, including zero placeholders, and VAA introduces a separate fallback regime.

Do not automatically negate WAPneg. Positive and negative refer to the direction of balancing energy, not the mathematical sign of its market price. Either directional price can itself be positive or negative. MEPSO selects the applicable component using activated-energy conditions; the sign of a portfolio cash flow also depends on the portfolio imbalance. See [MEPSO rules, Articles 83–86](https://www.mepso.com.mk/docs/pbee/en/Electricity%20balance%20market%20rules%20-%20consolidated%20text.pdf).

A deliberately defined signed-direction indicator could encode upward activation as positive and downward activation as negative, but it would be a synthetic indicator rather than the published settlement price. Encoding direction this way can also destroy information when prices are already negative. Prefer a separate direction column alongside the original price.

**Implemented (2026-11-26).** The importer now derives the imbalance settlement price per release, following Articles 83–84: net activated energy (|aFRR up| + |mFRR up| − |aFRR down| − |mFRR down|) > 0 selects WAPpos, < 0 selects WAPneg, = 0 selects VAA. VAA is a dual price: VAA+ for a positive (surplus) imbalance, VAA− for a negative (deficit) one, so the derived columns give a surplus price and a deficit price that are equal in every WAP hour. In all 2020–2026 hours with activation data the selected WAP is the only non-zero WAP, except 2 final and 6 preliminary hours (flagged `_imbalance_unselected_component_nonzero`). January 2020 (final and preliminary) and February 2020 (preliminary) have no activation tables; there the single non-zero component decides (flagged `_imbalance_regime_from_prices`). Signs are preserved; components are never summed or averaged.

The derived price covers 56,735 hours (94.71%): 54,765 from final, 1,970 from preliminary data. It cannot recover March–June 2023, the missing repeated hour in October 2022, or the October 2026 hours without prices.

## Applied scalar EUR columns now available

The CSV now includes `final_price_applied_eur_per_mwh` and `preliminary_price_applied_eur_per_mwh` as additional financial forecasting targets. The existing regime-specific surplus/deficit fields remain unchanged. Unlike a generic surplus/deficit pair, a scalar requires a choice for unequal VAA fallback prices. The included January settlement reference supplies that choice only for its 744 observed hours; elsewhere unresolved choices stay blank.

Both scalar columns match all 744 January 2026 settlement observations after the documented currency/unit conversion. Reference matching is performed separately against each release and copies its MEPSO component value. A revision mismatch is flagged rather than overridden. Source-only selections and reference-based selections have distinct statuses; this implementation is a conservative derived target, not a claim of independently verified settlement correctness for every historical hour.

Use the corresponding `*_applied_price_status`, `*_applied_price_component`, `*_applied_price_source_filename` and `*_applied_price_reference` fields to filter labels and trace their selection. Raw price-component availability and existing surplus/deficit coverage can be higher than scalar coverage. No ambiguous VAA values are silently averaged, signed, or filled. The full selection policy and reference-builder command are documented in README_mepso.txt.

## Recommended forecasting targets

These priorities balance **observed coverage, an interpretable quantity, and a plausible business decision**. They do not rank empirical forecastability.

| Priority | Columns or proposed derived fields | Why they are useful | Coverage and preparation |
| --- | --- | --- | --- |
| Applied scalar financial target | `final_price_applied_eur_per_mwh`, separately `preliminary_price_applied_eur_per_mwh` | A single observed/selected EUR price corresponding to the settlement workbook where explicit reference evidence is available. | 48,990 final and 42,657 preliminary hours filled in the current snapshot; both reproduce all 744 January reference hours. Other unequal fallback cases remain blank. Use the selection status to distinguish reference matches from source-only reconstruction; do not assume a universal portfolio-independent VAA price. |
| Priority financial target | `imbalance_price_surplus_eur_per_mwh`, `imbalance_price_deficit_eur_per_mwh` with `imbalance_regime` (final, else preliminary; `final_`/`preliminary_` variants also present) | The applicable imbalance settlement price is directly relevant to imbalance exposure and is the plant workbook's `MEPSO Price`, before currency/unit conversion. It is more directly aligned with that business objective than predicting each component independently. | 56,735 hours, 94.71% (54,765 final, 1,970 preliminary; `imbalance_price_version` says which). Surplus and deficit prices differ only in the 5,876 VAA hours. |
| First operational targets | `final_afrr_up_mwh`, `final_afrr_down_mwh` | Activated automatic balancing energy is relevant to flexible generation, storage and balancing-service planning. | Each has 54,023 filled hours, 90.18% of the grid. Keep up/down separate, preserve the down sign, and distinguish numeric zero from a missing observation. |
| Additional operational targets | `final_mfrr_up_mwh`, `final_mfrr_down_mwh` | Directional manual balancing-energy activation is another concrete operational quantity. | Each has 54,023 filled hours, 90.18%. Many reported values are zero; filled does not mean that many activation events. |
| Secondary operational target | `final_ace_mwh_per_h` | A signed control-error forecast can describe system stress and complement activation forecasts. | 53,154 filled hours, 88.73%. Preserve its meaning as published; it is not a direct monetary exposure target. |
| Financial targets with narrower scope | `final_price_wapneg_eur_per_mwh`, `final_price_wappos_eur_per_mwh` | Prices carry economic value for imbalance exposure and flexibility scheduling. | Final WAPneg has 41,516 filled hours, 69.30%; WAPpos has 38,533, 64.32%. Define whether the target is a component conditional on its regime or the applicable settlement price before preparing labels. Do not impute inactive components to zero just to obtain a dense target. |
| Conditional fallback targets only | `final_price_vaa_plus_eur_per_mwh`, `final_price_vaa_minus_eur_per_mwh` | Fallback pricing matters in the corresponding settlement regime. | Each has 30,154 filled hours, 50.34%, including many zeros. Their rule dependence and conditional role make them weaker default standalone targets. |

For a financial forecasting task, use the derived imbalance price columns. For an operational task focused on coverage, choose an aFRR direction or the four directional reserve series as separate outputs. Do not sum WAPpos, WAPneg and VAA, choose the first nonzero value, or assume that the plus/minus VAA fields are interchangeable.

### January 2026 validation of the applied price target

The settlement workbook of one PV plant for January 2026 (not distributed), sheet `Settlement`, labels column J as `MEPSO Price` in MKD/kWh. All **744 hourly values** match existing MEPSO EUR/MWh components using the workbook's fixed rate in B10:

`MEPSO Price (MKD/kWh) = selected component (EUR/MWh) * 61.695 / 1000`

The matches are 323 WAPpos hours, 418 WAPneg hours, two VAA-plus hours and one VAA-minus hour, with no unmatched hours. Both preliminary and final EUR component values match; this comparison cannot identify which release the plant workbook used. The match tolerance was relative 1e-9 or absolute 1e-8 MKD/kWh. See [the hourly comparison](../summary/january_2026_MEPSO_price_matches.csv) and [the findings](../summary/january_2026_price_comparison.txt).

For example, J11 equals `129.50597955 * 61.695 / 1000 = 7.98987140833725` MKD/kWh. Its matching component is `final_price_wappos_eur_per_mwh`, also matched by the preliminary version. The directly published MKD reference uses a daily rate of 61.495 for that date, so it does not reproduce J11 exactly. Prefer the underlying EUR value as the target, keeping the workbook conversion rate as separate provenance rather than embedding a changing accounting convention in the EUR label.

The selection rule has since been confirmed with the balancing rules (Articles 83–84) and with the ten January–October 2026 plant workbooks: the derived price reproduces `MEPSO Price` in 7,007 of the 7,055 hours that have a derived price; the remaining 48 hours differ between revisions. In the 250 VAA hours the workbook uses the deficit price 167 times and the surplus price 83 times. The plant's own imbalance sign does not explain this choice: the sign of the balance responsible party's whole balancing group (the trader's portfolio) decides, and that is not published. The plant workbooks are not distributed; see [the link to PV production](../README.md#link-to-pv-production-balancing-groups) for what this means for a balancing group.

Column J is a unit-price target, not the plant's total balancing cost. Column O calculates `-N * (J - K)`, which also requires the plant imbalance and the other price. Do not rename the applied price as monetary balancing cost or imply that price forecasting alone predicts that cash flow.

At least one final EUR component is present in **54,765 hours, 91.42%** of this grid; at least one EUR component in either version is present in **56,735 hours, 94.71%**. The derived imbalance price columns reach exactly these bounds (54,765 final, 1,970 preliminary-only hours), which is why the financial objective is worthwhile even though each individual component has a lower fill rate.

Use final data as the default historical outcome. Restrict each target to its own valid labels; do not require every unrelated parameter to be populated. Preliminary fallback is a deliberate label-quality choice and should carry a revision flag. Retain gaps and avoid forming training windows across a missing period as if adjacent observed rows were consecutive hours.

## Covariates and their availability

| Candidate | How it can be used | Information available at forecast time |
| --- | --- | --- |
| Calendar features derived from `timestamp_utc` using Europe/Skopje | Local hour, weekday, season, holiday and daylight-saving indicators are natural candidates for recurring demand and operating patterns. | Known in advance. The future timestamp is available without knowing future realized prices or activations. A holiday calendar would be an additional source. |
| History of the selected target | Prior observed activation or price values can provide time-series context. | Use only observations already released at the forecast's issue time. A lag of one hour does not by itself prove availability. |
| Lagged `*_ace_mwh_per_h` and other directional activation series | Candidate operational context when forecasting a different balancing quantity or a price. | Realized values for the forecasted interval are not future-known inputs. Availability of lagged values must be established independently of this monthly archive. |
| Lagged EUR price components | Candidate context for financial regimes or recent balancing costs. | Apply the same publication-time restriction; do not supply the same-hour realized components when predicting their applicable price. |
| `*_exchange_rate_mkd_per_eur` | Accounting or MKD conversion reference. | Low priority for predicting EUR balancing outcomes. Use only a rate known at issuance if future conversion is part of the task. High coverage alone is not a reason to forecast it. |
| Additional data not in this CSV | HUPX day-ahead prices, load/renewable forecasts, weather forecasts and announced outages are domain-motivated candidates. | Align each source's release time and market interval with the horizon. Use forecasts or announcements available then, not the realized future load, weather, generation or outage record. HUPX is particularly relevant to the cited MEPSO fallback methodology; usefulness of the other candidates remains a hypothesis. |

**Publication time matters more than column prefix.** These source files are monthly archives without a complete history of when each hourly value became public. Final same-hour prices, ACE and activated energy are outcomes. Preliminary same-hour values are also not automatically known before that hour. An operational evaluation needs dated releases or an explicitly justified reporting delay; the archive alone does not establish that lagged final values were available live. These are preparation constraints, not results of a forecasting experiment.

## Redundant columns and columns to keep for reference

| Columns or relationship | Recommended role |
| --- | --- |
| MKD price columns alongside their matching EUR components | Retain for audit and conversion checks. They express the same underlying price in another currency, so do not count them as independent economic targets. Using same-hour MKD to predict its EUR counterpart would mostly be currency conversion, not an informative price forecast. |
| Preliminary and final versions of the same parameter | Keep both in storage; select one revision policy for modelling. They are versions of the same hour's outcome, not independent measurements of different phenomena. Preliminary data can support a separate revision task if release timing is known. |
| `*_afrr_total_mwh`, `*_mfrr_total_mwh` with their up/down columns | Potentially redundant within a verified, consistent reporting regime. Keep the directional series for the default target set. Totals can encode signed net energy or gross activation in different periods and include inconsistencies, so they are not universally exact duplicates. Never use a same-hour total that contains the target as a forecast input. |
| `*_afrr_net_mwh`, `*_mfrr_net_mwh` | Early-format context and possible historical reconciliation fields. Their short coverage makes them poor default targets. Do not automatically splice them into later total or directional series. |
| `local_timestamp`, `local_date`, `local_hour`, `local_fold` and the UTC index | Useful calendar/provenance representations derivable from UTC plus the timezone. Choose purposeful calendar features rather than treating each representation as a separate economic variable. |
| `status`, `preliminary_status`, `final_status`, `quality_flags`, source filename columns | Use for filtering, tracing revisions and assessing missingness. They are not forecasting targets. Retrospective final-availability labels and filenames can reveal information unavailable at issuance; do not feed them into a model by default. |

ACE is **not** classed as redundant with net activated energy. Nor are WAPpos and WAPneg interchangeable: their similar units do not make their economic roles identical.

## Refreshing the quality counts

After updating the dataset, run from the dataset folder (`datasets/mepso`):

```bash
python3 scripts/process_mepso.py
python3 scripts/summarize_mepso_quality.py
```

The second command uses only Python's standard library and the existing CSV. It refreshes the marked count tables in this README and writes to `summary/`:

- `mepso_monthly_quality.csv`: one row per month, including all core parameter groups.
- `mepso_monthly_column_quality.csv`: separate filled, missing, zero and nonzero counts for every versioned numeric column in every month.
- `mepso_column_coverage.csv`: coverage by metric and version over the entire grid.
- `mepso_reserve_total_checks.csv`: direct signed/gross arithmetic checks wherever all three values are supplied, with a tolerance of 0.000001 MWh or a relative tolerance of 0.000000001.
- `mepso_quality_summary.json`: dataset checksum, headline counts and exact preliminary-only EUR intervals.

It does not modify the hourly CSV or fit a model. The written interpretation and recommendations describe this snapshot and need review when source formats or coverage change; only the marked count sections refresh automatically. Importer usage and timestamp handling remain documented in [README_mepso.txt](README_mepso.txt).
