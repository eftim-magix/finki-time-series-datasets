#!/usr/bin/env python3
"""Count dataset completeness and refresh the generated sections of the quality README.

No models, correlations, imputation, or forecasting experiments are performed.
"""
import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

DATASET = Path(__file__).resolve().parents[1]   # datasets/mepso
TZ = ZoneInfo('Europe/Skopje')
UTC = dt.timezone.utc
PARAMETERS = ['afrr_up_mwh', 'afrr_down_mwh', 'mfrr_up_mwh', 'mfrr_down_mwh',
              'afrr_total_mwh', 'mfrr_total_mwh', 'afrr_net_mwh', 'mfrr_net_mwh',
              'ace_mwh_per_h', 'exchange_rate_mkd_per_eur']
PRICES = [f'price_{component}_eur_per_mwh' for component in ['wappos', 'wapneg', 'vaa_plus', 'vaa_minus']]


def next_month(date):
    return date.replace(year=date.year+1, month=1) if date.month == 12 else date.replace(month=date.month+1)


def value(row, column):
    text = row.get(column, '')
    if text == '':
        return None
    number = float(text)
    if not math.isfinite(number):
        raise ValueError(f'Non-finite value in {column}: {text}')
    return number


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def replace_section(text, name, content):
    start, end = f'<!-- BEGIN {name} -->', f'<!-- END {name} -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f'Readme needs exactly one pair of {name} markers')
    before, rest = text.split(start)
    _, after = rest.split(end)
    return before + start + '\n\n' + content.strip() + '\n\n' + end + after


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DATASET/'processed'/'MEPSO_balancing_prices_hourly.csv')
    parser.add_argument('--output-dir', type=Path, default=DATASET/'summary')
    parser.add_argument('--readme', type=Path, default=DATASET/'docs'/'README_data_quality.md', help='Markdown file whose generated sections are refreshed')
    parser.add_argument('--as-of', default=dt.datetime.now(TZ).date().isoformat())
    args = parser.parse_args()
    with args.input.open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames
        rows = list(reader)
    if not rows:
        raise ValueError('Empty dataset')
    metrics = sorted(c.removeprefix('final_') for c in columns
                     if c.startswith('final_') and (c.endswith('_mwh') or c.endswith('_per_h') or c.endswith('_mkd_per_eur')))
    for metric in metrics:
        if f'preliminary_{metric}' not in columns:
            raise ValueError(f'No preliminary counterpart for {metric}')
    versions = ['preliminary', 'final']
    by_timestamp = {}
    by_month = collections.defaultdict(list)
    intervals = []
    for row in rows:
        timestamp = dt.datetime.fromisoformat(row['timestamp_utc'].replace('Z', '+00:00'))
        if timestamp.utcoffset() != dt.timedelta(0) or timestamp.minute or timestamp.second:
            raise ValueError('Expected UTC hours at interval starts')
        if timestamp in by_timestamp:
            raise ValueError(f'Duplicate UTC timestamp: {timestamp}')
        local = timestamp.astimezone(TZ)
        if local.date().isoformat() != row['local_date']:
            raise ValueError('Local date and UTC timestamp disagree')
        row['_timestamp'] = timestamp
        # Presence and zero counts use numeric cells, including legitimate 0 values.
        row['_values'] = {f'{v}_{m}': value(row, f'{v}_{m}') for v in versions for m in metrics}
        by_timestamp[timestamp] = row
        by_month[local.strftime('%Y-%m')].append(row)
    first = min(by_timestamp).astimezone(TZ).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last = next_month(max(by_timestamp).astimezone(TZ).replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    expected = collections.Counter()
    cursor = first.astimezone(UTC)
    while cursor < last.astimezone(UTC):
        expected[cursor.astimezone(TZ).strftime('%Y-%m')] += 1
        cursor += dt.timedelta(hours=1)
    month_rows = []
    detail = []
    totals_checks = []
    all_prelim_times = []
    core = [m for m in metrics if m != 'exchange_rate_mkd_per_eur']

    def present(row, metric, version=None):
        return any(row['_values'][f'{v}_{metric}'] is not None for v in ([version] if version else versions))

    def price_present(row, version=None):
        return any(present(row, metric, version) for metric in PRICES)

    def has_core(row):
        return any(present(row, metric) for metric in core)

    for month, hours in sorted(expected.items()):
        part = by_month[month]
        count = dict(month=month, expected_hours=hours, csv_rows=len(part), missing_grid_rows=hours-len(part),
                     hours_without_measurements=hours-sum(has_core(r) for r in part),
                     hours_without_eur_prices_either_version=hours-sum(price_present(r) for r in part),
                     hours_without_final_eur_prices=hours-sum(price_present(r, 'final') for r in part),
                     preliminary_only_eur_hours=sum(price_present(r, 'preliminary') and not price_present(r, 'final') for r in part))
        for metric in PARAMETERS:
            count['missing_'+metric+'_either_version'] = hours-sum(present(r, metric) for r in part)
        month_rows.append(count)
        all_prelim_times.extend(r['_timestamp'] for r in part if price_present(r, 'preliminary') and not price_present(r, 'final'))
        for version in versions:
            for metric in metrics:
                column = f'{version}_{metric}'
                values = [r['_values'][column] for r in part if r['_values'][column] is not None]
                detail.append(dict(month=month, column=column, expected_hours=hours, filled_hours=len(values),
                                   missing_hours=hours-len(values), zero_hours=sum(x==0 for x in values),
                                   nonzero_hours=sum(x!=0 for x in values), coverage_percent=round(100*len(values)/hours, 4)))
            for kind in ['afrr', 'mfrr']:
                triplets = [tuple(r['_values'][f'{version}_{kind}_{metric}_mwh'] for metric in ['up','down','total']) for r in part]
                complete = [(u,d,t) for u,d,t in triplets if None not in (u,d,t)]
                signed = sum(math.isclose(t,u+d,rel_tol=1e-9,abs_tol=1e-6) for u,d,t in complete)
                gross = sum(math.isclose(t,u+abs(d),rel_tol=1e-9,abs_tol=1e-6) for u,d,t in complete)
                totals_checks.append(dict(month=month, version=version, reserve=kind, complete_triplets=len(complete),
                                          signed_sum_matches=signed, gross_sum_matches=gross,
                                          neither_sum_matches=sum(not math.isclose(t,u+d,rel_tol=1e-9,abs_tol=1e-6) and not math.isclose(t,u+abs(d),rel_tol=1e-9,abs_tol=1e-6) for u,d,t in complete)))
    whole_hours = sum(expected.values())
    coverage = []
    for metric in metrics:
        item = dict(metric=metric, expected_hours=whole_hours)
        for version in versions:
            vals = [r['_values'][f'{version}_{metric}'] for r in rows if present(r, metric, version)]
            item[version+'_filled_hours'] = len(vals)
            item[version+'_coverage_percent'] = round(100*len(vals)/whole_hours,4)
            item[version+'_zero_hours'] = sum(v==0 for v in vals)
        item['either_version_filled_hours'] = sum(present(r, metric) for r in rows)
        coverage.append(item)
    # Enumerate the exact UTC ranges of preliminary-only EUR observations.
    for timestamp in sorted(all_prelim_times):
        if intervals and timestamp == intervals[-1][1]:
            intervals[-1][1] += dt.timedelta(hours=1)
        else:
            intervals.append([timestamp,timestamp+dt.timedelta(hours=1)])
    out = args.output_dir.resolve()
    out.mkdir(parents=True,exist_ok=True)
    write_csv(out/'mepso_monthly_quality.csv',month_rows)
    write_csv(out/'mepso_monthly_column_quality.csv',detail)
    write_csv(out/'mepso_column_coverage.csv',coverage)
    write_csv(out/'mepso_reserve_total_checks.csv',totals_checks)
    digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
    summary = dict(as_of=args.as_of, input_csv=args.input.name, csv_sha256=digest,
                   rows=len(rows), expected_hours=whole_hours, months=len(expected),
                   missing_grid_rows=sum(r['missing_grid_rows'] for r in month_rows),
                   hours_without_measurements=sum(r['hours_without_measurements'] for r in month_rows),
                   hours_without_eur_prices_either_version=sum(r['hours_without_eur_prices_either_version'] for r in month_rows),
                   hours_without_final_eur_prices=sum(r['hours_without_final_eur_prices'] for r in month_rows),
                   preliminary_only_eur_hours=sum(r['preliminary_only_eur_hours'] for r in month_rows),
                   preliminary_only_eur_intervals=[dict(start_utc=a.isoformat(),end_exclusive_utc=b.isoformat(),hours=int((b-a).total_seconds()/3600)) for a,b in intervals],
                   coverage=coverage)
    (out/'mepso_quality_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    readme = args.readme.resolve()
    text = readme.read_text()
    intro = (f'As of **{args.as_of}**: **{len(rows):,} rows**, **{len(expected)} local calendar months**, '
             f'**{whole_hours:,} expected UTC hours**, and **{summary["missing_grid_rows"]:,} absent timestamp rows**. '
             f'There are **{summary["hours_without_measurements"]:,} hours without source measurements**, '
             f'**{summary["hours_without_eur_prices_either_version"]:,} hours without any EUR price component in either version**, '
             f'and **{summary["preliminary_only_eur_hours"]:,} hours with preliminary EUR prices and no final EUR price**.\n\n'
             f'Dataset SHA-256: `{digest}`.')
    text = replace_section(text,'SNAPSHOT',intro)
    table = ['| Metric suffix | Final filled | Final coverage | Preliminary filled | Either version filled | Final zeros |',
             '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in coverage:
        table.append(f'| `{r["metric"]}` | {r["final_filled_hours"]:,} | {r["final_coverage_percent"]:.2f}% | {r["preliminary_filled_hours"]:,} | {r["either_version_filled_hours"]:,} | {r["final_zero_hours"]:,} |')
    text = replace_section(text,'COVERAGE','\n'.join(table))
    table = ['| Month | Expected hours | No measurements | EUR missing F/E | P only EUR | aFRR missing U/D | mFRR missing U/D | ACE missing | FX missing |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in month_rows:
        table.append(f'| {r["month"]} | {r["expected_hours"]} | {r["hours_without_measurements"]} | {r["hours_without_final_eur_prices"]}/{r["hours_without_eur_prices_either_version"]} | {r["preliminary_only_eur_hours"]} | {r["missing_afrr_up_mwh_either_version"]}/{r["missing_afrr_down_mwh_either_version"]} | {r["missing_mfrr_up_mwh_either_version"]}/{r["missing_mfrr_down_mwh_either_version"]} | {r["missing_ace_mwh_per_h_either_version"]} | {r["missing_exchange_rate_mkd_per_eur_either_version"]} |')
    text = replace_section(text,'MONTHLY','\n'.join(table))
    table = ['| Start UTC inclusive | End UTC exclusive | Hours |', '| --- | --- | ---: |']
    for a,b in intervals:
        table.append(f'| {a.isoformat()} | {b.isoformat()} | {int((b-a).total_seconds()/3600)} |')
    text = replace_section(text,'PRELIMINARY','\n'.join(table))
    readme.write_text(text)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['coverage']},indent=2))


if __name__=='__main__':
    main()
