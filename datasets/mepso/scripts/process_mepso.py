#!/usr/bin/env python3
"""Incrementally import MEPSO workbooks (raw/) into one hourly CSV (processed/).

See ../README.md and ../docs/README_mepso.txt for the column semantics."""
import argparse
import calendar
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from zoneinfo import ZoneInfo
import zlib

import openpyxl

PARSER_VERSION = '1.0.0'
APPLIED_PRICE_VERSION = '1.0.0'
DATASET = Path(__file__).resolve().parents[1]   # datasets/mepso
TZ = ZoneInfo('Europe/Skopje')
UTC = dt.timezone.utc
HOUR = dt.timedelta(hours=1)
PRICE_LABELS = {'wappos': 'wappos', 'wapneg': 'wapneg', 'vaa+': 'vaa_plus', 'vaa-': 'vaa_minus', 'cimb': 'cimb'}
NAME = re.compile(r'MEPSO_balancing_prices_(\d{4}-\d{2})_(preliminary|final)(.*)\.xlsx$', re.I)
COMPONENTS = ('wappos', 'wapneg', 'vaa_plus', 'vaa_minus')
UP, DOWN = ('afrr_up_mwh', 'mfrr_up_mwh'), ('afrr_down_mwh', 'mfrr_down_mwh')
IMBALANCE_FIELDS = ('imbalance_regime', 'imbalance_price_surplus_eur_per_mwh', 'imbalance_price_deficit_eur_per_mwh')
IMBALANCE_COLUMNS = [f'{v}_{f}' for v in ('preliminary', 'final') for f in IMBALANCE_FIELDS] + list(IMBALANCE_FIELDS) + ['imbalance_price_version']


def parse_date(value):
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        m = re.search(r'(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](20\d{2})(?!\d)', value)
        if m:
            try:
                return dt.date(int(m[3]), int(m[2]), int(m[1]))
            except ValueError:
                pass
    return None


def hour_label(value):
    if not isinstance(value, str):
        return None
    value = value.strip().lower().replace('н', 'h').replace('в', 'b')
    m = re.fullmatch(r'h?(\d{1,2})(b?)h?', value)
    if m and 1 <= int(m[1]) <= 24:
        return int(m[1]), int(bool(m[2]))
    return None


def utc_hour(day, hour, fold=0):
    """H1 is 00:00 local. Reject nonexistent hours and spurious H3B columns."""
    naive = dt.datetime.combine(day, dt.time(hour - 1))
    local = naive.replace(tzinfo=TZ, fold=fold)
    utc = local.astimezone(UTC)
    back = utc.astimezone(TZ)
    if back.replace(tzinfo=None) != naive or back.fold != fold:
        return None
    return utc.strftime('%Y-%m-%dT%H:00:00Z')


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def classify(header, sheet):
    h = header.lower()
    context = (header + ' ' + sheet).lower()
    if ('порамнување' in context or 'poramnuvanje' in context or 'imbalance price' in context):
        currency = 'mkd' if 'mkd' in h or 'мкд' in h else 'eur'
        return 'price', currency
    energy_context = h if 'afrr' in h or 'mfrr' in h or 'секундарна' in h or 'терциерна' in h else context
    kind = 'afrr' if 'afrr' in energy_context or 'секундарна' in h else 'mfrr' if 'mfrr' in energy_context or 'терциерна' in h else None
    if kind:
        direction = 'up' if 'нагоре' in h or re.search(r'\bup\b', h) else 'down' if 'надолу' in h or re.search(r'\bdown\b', h) else 'net' if 'секундарна' in h or 'терциерна' in h or 'енергија во' in h else 'total'
        return f'{kind}_{direction}_mwh', None
    if 'control error' in context or sheet.strip().lower() == 'ace':
        return 'ace_mwh_per_h', None
    return None, None


def parse_workbook(path):
    match = NAME.fullmatch(path.name)
    if not match:
        raise ValueError(f'Unrecognized workbook filename: {path}')
    period, version, suffix = match.groups()
    # Retain the bad archive source on disk, but never let it replace June's true source.
    if '__source-' in suffix:
        return dict(period=period, version=version, excluded='Known archive period mismatch; original March preliminary file actually contains June.', rows={}, metrics=[], issues=[])
    supplement = bool(re.search(r'_20\d\d-\d\d-\d\d', suffix))
    data = collections.defaultdict(dict)
    issues = collections.Counter()
    tables = []
    rates = {}
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    metrics = set()
    try:
        for ws in wb:
            rows = list(ws.values)
            # Exchange rates are daily auxiliary parameters, not 24 hourly inputs.
            if re.search(r'курс|kurs|exchange', ws.title, re.I):
                for row in rows:
                    if not row:
                        continue
                    day = parse_date(row[0])
                    if day and len(row) >= 4 and number(row[3]):
                        unit = row[2] if number(row[2]) and row[2] != 0 else 1
                        rates[day.isoformat()] = row[3] / unit
                continue
            hours = None
            metric = currency = day = None
            price_seen = set()
            for i, row in enumerate(rows):
                candidate = {c: hour_label(v) for c, v in enumerate(row) if hour_label(v)}
                if len(candidate) >= 23:
                    hours = candidate
                    header = ' '.join(str(v) for previous in rows[max(0, i-2):i] for v in previous if isinstance(v, str))
                    metric, currency = classify(header, ws.title)
                    day = None
                    price_seen = set()
                    if not metric:
                        raise ValueError(f'Unknown hourly table: {path.name}, {ws.title}, row {i+1}: {header}')
                    tables.append(dict(sheet=ws.title, header_row=i+1, metric=metric, currency=currency))
                    # Single-day supplement dates can occur only in the heading.
                    if supplement:
                        day = parse_date(header)
                    continue
                if not hours or not metric:
                    continue
                left = row[:min(hours)]
                explicit_date = next((d for v in left if (d := parse_date(v))), None)
                invalid_date = any(isinstance(v, str) and re.fullmatch(r'\d{1,2}[./-]\d{1,2}[./-]20\d{2}\.?', v.strip()) and parse_date(v) is None for v in left)
                if invalid_date:
                    issues['invalid_calendar_date_template_rows'] += 1
                    day = None
                    price_seen = set()
                    continue
                if explicit_date:
                    day = explicit_date
                    price_seen = set()
                label = next((PRICE_LABELS[v.strip().lower()] for v in left if isinstance(v, str) and v.strip().lower() in PRICE_LABELS), None)
                if metric == 'price':
                    if not label or day is None:
                        continue
                    if label == 'cimb' and not any(number(row[c]) for c in hours if c < len(row)):
                        continue
                    # Trailing template rows repeat labels without dates. Never assign them to the last day.
                    if label in price_seen:
                        if any(number(row[c]) and row[c] != 0 for c in hours if c < len(row)):
                            raise ValueError(f'Undated repeated price block: {path.name}, {ws.title}, row {i+1}')
                        issues['undated_empty_or_zero_template_rows'] += 1
                        continue
                    price_seen.add(label)
                    field = f'price_{label}_{currency}_per_mwh'
                else:
                    # Energy/ACE tables have one dated row per day; no forward fill.
                    if not explicit_date:
                        continue
                    field = metric
                if day.strftime('%Y-%m') != period:
                    raise ValueError(f'Content date {day} disagrees with filename: {path.name}')
                metrics.add(field)
                for c, (hour, fold) in hours.items():
                    value = row[c] if c < len(row) else None
                    timestamp = utc_hour(day, hour, fold)
                    if timestamp is None:
                        if number(value) and value != 0:
                            issues['nonexistent_or_spurious_hour_nonzero_cells'] += 1
                        continue
                    target = data[timestamp]
                    if number(value):
                        if field in target and target[field] != value:
                            raise ValueError(f'Conflicting cells: {path.name}, {timestamp}, {field}')
                        target[field] = value
                    elif value is not None:
                        issues['nonnumeric_hourly_cells'] += 1
            if not tables and any(number(v) for row in rows for v in row):
                issues['unclassified_nonhourly_sheet'] += 1
    finally:
        wb.close()
    if not any(k.startswith('price_') for row in data.values() for k in row):
        raise ValueError(f'No numeric hourly prices extracted: {path}')
    for timestamp, row in data.items():
        day = dt.datetime.fromisoformat(timestamp.replace('Z', '+00:00')).astimezone(TZ).date().isoformat()
        if day in rates:
            row['exchange_rate_mkd_per_eur'] = rates[day]
            metrics.add('exchange_rate_mkd_per_eur')
    return dict(period=period, version=version, supplement=supplement, rows=dict(data), metrics=sorted(metrics), tables=tables, issues=dict(issues))


def imbalance_prices(row, version):
    """Combine one release's published components into the imbalance settlement price.

    MEPSO balancing rules, Articles 83-84: a single price for every BRP imbalance, chosen by
    the net activated aFRR + mFRR energy of the hour: > 0 (system short) WAPpos, < 0 (system
    long) WAPneg. With no activation (= 0) the price is VAA and depends on the sign of the
    BRP's own imbalance: VAA+ for a positive imbalance (surplus, the TSO pays the BRP), VAA-
    for a negative one (deficit, the BRP pays the TSO). Returns
    (regime, surplus_price, deficit_price, flags); both prices are equal except for VAA.
    Without activation data the regime is inferred from which components are non-zero."""
    prices = {c: row.get(f'{version}_price_{c}_eur_per_mwh') for c in COMPONENTS}
    if all(v is None for v in prices.values()):
        return None, None, None, []
    flags = []
    up = [row.get(f'{version}_{k}') for k in UP]
    down = [row.get(f'{version}_{k}') for k in DOWN]
    if any(v is not None for v in up + down):
        # Downward energy is published with a negative sign; abs() keeps this robust either way.
        net = sum(abs(v) for v in up if v is not None) - sum(abs(v) for v in down if v is not None)
        regime = 'wappos' if net > 0 else 'wapneg' if net < 0 else 'vaa'
    else:
        nonzero = {c for c, v in prices.items() if v not in (None, 0)}
        if nonzero == {'wappos'} or nonzero == {'wapneg'}:
            regime = nonzero.pop()
        elif nonzero and nonzero <= {'vaa_plus', 'vaa_minus'}:
            regime = 'vaa'
        else:
            return None, None, None, [f'{version}_imbalance_regime_ambiguous']
        flags.append(f'{version}_imbalance_regime_from_prices')
    if regime == 'vaa':
        surplus, deficit = prices['vaa_plus'], prices['vaa_minus']
        others = ('wappos', 'wapneg')
    else:
        surplus = deficit = prices[regime]
        others = tuple(c for c in COMPONENTS if c != regime)
    if surplus is None or deficit is None:
        flags.append(f'{version}_imbalance_price_component_missing')
    if any(prices[c] not in (None, 0) for c in others):
        flags.append(f'{version}_imbalance_unselected_component_nonzero')
    return regime, surplus, deficit, flags


def month_start(month):
    return dt.datetime.strptime(month, '%Y-%m').replace(tzinfo=TZ)


def next_month(value):
    return value.replace(year=value.year+1, month=1) if value.month == 12 else value.replace(month=value.month+1)


def atomic_write(path, writer):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', newline='', encoding='utf-8') as handle:
            writer(handle)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def load_applied_references(path):
    references = {}
    if not path.exists():
        return references
    with path.open(newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            key = row['timestamp_utc']
            price = float(row['reference_price_eur_per_mwh'])
            if not math.isfinite(price):
                raise ValueError(f'Invalid reference price: {key}')
            if key in references and not math.isclose(references[key]['price'],price,rel_tol=1e-9,abs_tol=1e-8):
                raise ValueError(f'Conflicting applied-price references: {key}')
            references[key] = dict(price=price, source=row['reference_filename'], cell=row['reference_cell'])
    return references


def select_applied_price(values, version, reference=None):
    """Use reported EUR values only. Never reverse signs, impute, or mix versions."""
    components = {c: values[f'{version}_price_{c}_eur_per_mwh'] for c in ['cimb','wappos','wapneg','vaa_plus','vaa_minus']
                  if f'{version}_price_{c}_eur_per_mwh' in values}
    if not components:
        return None, '', 'missing_eur_components'
    if reference:
        matches = [c for c,p in components.items() if math.isclose(p,reference['price'],rel_tol=1e-9,abs_tol=1e-8)]
        if matches:
            return components[matches[0]], ';'.join(matches), 'matched_settlement_reference'
        return None, '', 'reference_mismatch'
    if 'cimb' in components:
        return components['cimb'], 'cimb', 'reported_cimb'
    if len(components)==1:
        component,price = next(iter(components.items()))
        return price,component,'single_reported_component'
    if len(set(components.values()))==1:
        return next(iter(components.values())), ';'.join(components), 'equal_reported_components'
    directional = [values.get(f'{version}_{reserve}_{direction}_mwh')
                   for reserve in ['afrr','mfrr'] for direction in ['up','down']]
    net_fields = [values.get(f'{version}_{reserve}_net_mwh') for reserve in ['afrr','mfrr']]
    if all(x is not None for x in directional) and directional[0]>=0 and directional[1]<=0 and directional[2]>=0 and directional[3]<=0:
        net = sum(directional)
        basis = 'directional_activation'
    elif all(x is not None for x in net_fields):
        net = sum(net_fields)
        basis = 'legacy_net_activation'
    else:
        return None,'','ambiguous_components_missing_activation'
    if abs(net)>1e-8:
        component = 'wappos' if net>0 else 'wapneg'
        if component not in components:
            return None,'','activation_component_missing'
        opposite = 'wapneg' if component=='wappos' else 'wappos'
        if components.get(opposite,0)!=0:
            return None,'','ambiguous_multiple_directional_prices'
        return components[component], component, 'selected_'+basis
    fallback = {c:p for c,p in components.items() if c.startswith('vaa_')}
    if fallback and len(set(fallback.values()))==1:
        return next(iter(fallback.values())), ';'.join(fallback), 'equal_fallback_components'
    return None,'','ambiguous_fallback'


def run(args):
    base = args.input.resolve()
    output = (args.output or base/'MEPSO_balancing_prices_hourly.csv').resolve()
    state = (args.state or base/'.mepso-import.sqlite3').resolve()
    reference_path = (getattr(args,'applied_price_references',None) or base/'applied_price_references.csv').resolve()
    if getattr(args,'applied_price_references',None) and not reference_path.exists():
        raise FileNotFoundError(reference_path)
    references = load_applied_references(reference_path)
    state.parent.mkdir(parents=True, exist_ok=True)
    state_existed = state.exists()
    if output.exists() and not state_existed and not args.rebuild:
        raise ValueError('CSV already exists without importer state. Choose another --output or use --rebuild deliberately.')
    files = sorted(p for p in base.rglob('*.xlsx') if not p.name.startswith('~$'))
    if not files:
        raise ValueError(f'No Excel files found in {base}')
    conn = sqlite3.connect(state, timeout=1)
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, digest TEXT, parser TEXT, payload BLOB)')
        conn.execute('CREATE TABLE IF NOT EXISTS generated_outputs (path TEXT PRIMARY KEY)')
        conn.commit()
        owned = conn.execute('SELECT 1 FROM generated_outputs WHERE path=?', (str(output),)).fetchone()
        if output.exists() and not owned and not args.rebuild:
            raise ValueError('Output path is not registered in this importer state. Choose another --output or use --rebuild deliberately.')
        conn.execute('BEGIN IMMEDIATE')
        parsed = reused = 0
        active = []
        inventory = []
        failures = []
        for path in files:
            rel = path.relative_to(base).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            cached = conn.execute('SELECT digest,parser,payload FROM files WHERE path=?', (rel,)).fetchone()
            if cached and cached[:2] == (digest, PARSER_VERSION) and not args.rebuild:
                payload = json.loads(zlib.decompress(cached[2]))
                reused += 1
            else:
                try:
                    payload = parse_workbook(path)
                except Exception as error:
                    failures.append(f'{rel}: {error}')
                    continue
                packed = zlib.compress(json.dumps(payload, separators=(',', ':')).encode())
                conn.execute('INSERT OR REPLACE INTO files VALUES (?,?,?,?)', (rel, digest, PARSER_VERSION, packed))
                conn.commit()
                parsed += 1
                print(f'Parsed {rel}', flush=True)
            inventory.append(dict(source_filename=rel, sha256=digest, period=payload['period'], version=payload['version'], excluded=payload.get('excluded'), issues=payload.get('issues', {}), tables=payload.get('tables', [])))
            if not payload.get('excluded'):
                active.append((rel, payload))
        if failures:
            raise ValueError('Import stopped; previous CSV preserved. Valid files cached.\n'+'\n'.join(failures))
        current = {p.relative_to(base).as_posix() for p in files}
        removed = [row[0] for row in conn.execute('SELECT path FROM files') if row[0] not in current]
        for path in removed:
            conn.execute('DELETE FROM files WHERE path=?', (path,))
        conn.commit()
    finally:
        conn.close()
    # Monthly files first, then the explicit daylight-saving correction supplements.
    active.sort(key=lambda item: (bool(item[1].get('supplement')), item[0]))
    merged = collections.defaultdict(dict)
    sources = collections.defaultdict(dict)
    conflicts = []
    schema = set()
    expected_by_period = collections.defaultdict(set)
    for rel, payload in active:
        version = payload['version']
        schema.update(f'{version}_{k}' for k in payload['metrics'])
        expected_by_period[(payload['period'], version)].update(payload['metrics'])
        for timestamp, row in payload['rows'].items():
            for metric, value in row.items():
                field = f'{version}_{metric}'
                previous = merged[timestamp].get(field)
                if previous is not None and previous != value:
                    if not payload.get('supplement'):
                        raise ValueError(f'Conflicting overlapping monthly sources: {timestamp}, {field}. Supply only one revision per version/month.')
                    conflicts.append(dict(timestamp_utc=timestamp, column=field, previous=previous, replacement=value, source_filename=rel, reason='explicit_single_day_supplement'))
                merged[timestamp][field] = value
                sources[timestamp][field] = rel
    # Stable schema includes both versions even where only one has a given metric.
    metrics = sorted({k.split('_', 1)[1] for k in schema})
    value_columns = [f'{v}_{k}' for v in ['preliminary', 'final'] for k in metrics]
    applied_columns = [f'{v}_{field}' for v in ['preliminary','final'] for field in
                       ['price_applied_eur_per_mwh','applied_price_component','applied_price_status','applied_price_source_filename','applied_price_reference']]
    start = month_start(args.start or min(p['period'] for _, p in active)).astimezone(UTC)
    end = next_month(month_start(args.end or max(p['period'] for _, p in active))).astimezone(UTC)
    if end <= start:
        raise ValueError('--end must be on or after --start')
    leading = ['timestamp_utc', 'local_timestamp', 'local_date', 'local_hour', 'local_fold', 'status', 'preliminary_status', 'final_status', 'quality_flags', 'preliminary_source_filename', 'final_source_filename', 'source_filename']
    counts = collections.Counter()
    imbalance_counts = collections.Counter()
    written = 0
    applied_counts = {v:collections.Counter() for v in ['preliminary','final']}

    def write_csv(handle):
        nonlocal written
        writer = csv.DictWriter(handle, fieldnames=leading+value_columns+IMBALANCE_COLUMNS+applied_columns)
        writer.writeheader()
        timestamp = start
        while timestamp < end:
            key = timestamp.strftime('%Y-%m-%dT%H:00:00Z')
            local = timestamp.astimezone(TZ)
            row = dict(merged.get(key, {}))
            provenance = sources.get(key, {})
            statuses = {}
            flags = []
            for version in ['preliminary', 'final']:
                price_present = any(k.startswith(version+'_price_') for k in row)
                any_present = any(k.startswith(version+'_') and 'exchange_rate' not in k for k in row)
                file_expected = bool(expected_by_period.get((local.strftime('%Y-%m'), version)))
                statuses[version] = 'available' if price_present else 'missing_price' if any_present else 'missing_hour' if file_expected else 'missing_file'
                if not price_present:
                    flags.append(f'{version}_{statuses[version]}')
                # Blanks within an existing non-price series remain blanks and are identified.
                expected = expected_by_period.get((local.strftime('%Y-%m'), version), set())
                absent = [k for k in expected if not k.startswith('price_') and f'{version}_{k}' not in row]
                if any_present and absent:
                    flags.append(version+'_missing_parameters:'+','.join(sorted(absent)))
                names = sorted({name for field, name in provenance.items() if field.startswith(version+'_')})
                row[version+'_source_filename'] = ';'.join(names)
            # Derived imbalance settlement prices, per release; the unprefixed columns use final, else preliminary.
            best = None
            for version in ['preliminary', 'final']:
                regime, surplus, deficit, imbalance_flags = imbalance_prices(row, version)
                flags.extend(imbalance_flags)
                row.update({f'{version}_imbalance_regime': regime, f'{version}_imbalance_price_surplus_eur_per_mwh': surplus, f'{version}_imbalance_price_deficit_eur_per_mwh': deficit})
                if regime and surplus is not None and deficit is not None:
                    best = (regime, surplus, deficit, version)
            if best:
                row.update(dict(zip(list(IMBALANCE_FIELDS)+['imbalance_price_version'], best)))
                imbalance_counts[best[3]] += 1
            available = [v for v in statuses if statuses[v]=='available']
            status = 'both' if len(available)==2 else available[0]+'_only' if available else 'missing_price' if any(v=='missing_price' for v in statuses.values()) else 'missing'
            counts[status] += 1
            row.update(timestamp_utc=key, local_timestamp=local.isoformat(), local_date=local.date().isoformat(), local_hour=local.hour, local_fold=local.fold, status=status, preliminary_status=statuses['preliminary'], final_status=statuses['final'], quality_flags=';'.join(flags), source_filename=';'.join(sorted(set(provenance.values()))))
            for version in ['preliminary','final']:
                reference = references.get(key)
                price,components,selection_status = select_applied_price(merged.get(key,{}),version,reference)
                row[version+'_price_applied_eur_per_mwh'] = price
                row[version+'_applied_price_component'] = components
                row[version+'_applied_price_status'] = selection_status
                row[version+'_applied_price_source_filename'] = ';'.join(sorted({provenance[f'{version}_price_{component}_eur_per_mwh'] for component in components.split(';') if component}))
                row[version+'_applied_price_reference'] = (reference['source']+'!'+reference['cell']) if reference else ''
                applied_counts[version][selection_status] += 1
                if price is None:
                    flag=version+'_applied_price_'+selection_status
                    row['quality_flags'] += (';' if row['quality_flags'] else '')+flag
            writer.writerow(row)
            written += 1
            timestamp += HOUR
    atomic_write(output, write_csv)
    summary = dict(parser_version=PARSER_VERSION, output=os.path.relpath(output, base), source_timezone='Europe/Skopje', timestamp_semantics='UTC interval start; local H1 = 00:00–01:00; H3B = second occurrence of 02:00', first_timestamp_utc=start.isoformat(), end_exclusive_utc=end.isoformat(), rows=written, input_files=len(files), parsed_files=parsed, reused_files=reused, removed_files=removed, status_counts=dict(counts), imbalance_price_version_counts=dict(imbalance_counts), excluded_files=[x for x in inventory if x['excluded']], supplement_overrides=len(conflicts), columns=leading+value_columns+IMBALANCE_COLUMNS+applied_columns, inventory=inventory, applied_price_version=APPLIED_PRICE_VERSION, applied_price_selection_counts={v:dict(c) for v,c in applied_counts.items()}, applied_price_reference_file=os.path.relpath(reference_path, base) if reference_path.exists() else None, applied_price_reference_sha256=hashlib.sha256(reference_path.read_bytes()).hexdigest() if reference_path.exists() else None)
    atomic_write(output.with_suffix('.status.json'), lambda f: json.dump(summary, f, indent=2, ensure_ascii=False))
    atomic_write(output.with_suffix('.overrides.json'), lambda f: json.dump(conflicts, f, indent=2, ensure_ascii=False))
    connection = sqlite3.connect(state)
    try:
        connection.execute('INSERT OR IGNORE INTO generated_outputs VALUES (?)', (str(output),))
        connection.commit()
    finally:
        connection.close()
    print(json.dumps({k:v for k,v in summary.items() if k not in ['inventory','columns','excluded_files']}, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DATASET/'raw', help='Folder with the year subfolders of MEPSO workbooks (default: raw/)')
    parser.add_argument('--output', type=Path, default=DATASET/'processed'/'MEPSO_balancing_prices_hourly.csv')
    parser.add_argument('--state', type=Path, default=DATASET/'processed'/'.mepso-import.sqlite3', help='Parsing cache (not in git; rebuilt with --rebuild)')
    parser.add_argument('--start', help='First local month, YYYY-MM (default: earliest input month)')
    parser.add_argument('--end', help='Last local month, YYYY-MM, inclusive (default: latest input month)')
    parser.add_argument('--applied-price-references', type=Path, help='Optional applied-price reference CSV; default applied_price_references.csv in the input folder (raw/)')
    parser.add_argument('--rebuild', action='store_true', help='Reparse all workbooks and deliberately replace an existing generated CSV')
    run(parser.parse_args())


if __name__ == '__main__':
    main()
