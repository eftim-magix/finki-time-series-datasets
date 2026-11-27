#!/usr/bin/env python3
"""Download MEPSO imbalance-settlement workbooks into raw/<year>/.

Source page: https://www.mepso.com.mk/index.php/mk/pbee, section "Цена на порамнување"
(settlement price). MEPSO publishes one workbook per month and release: a preliminary list
first ("preliminarna"), a final list later ("konecna"), plus single-day supplements for the
autumn clock change.

    python3 scripts/fetch_mepso.py                 # download workbooks that are not in raw/ yet
    python3 scripts/fetch_mepso.py --dry-run       # only list what would be downloaded
    python3 scripts/fetch_mepso.py --recheck       # also re-download known links to detect revisions
    python3 scripts/fetch_mepso.py --page pbee.html --raw-dir /tmp/mepso-raw

Every workbook is saved byte-for-byte under the importer's naming convention
    raw/<year>/MEPSO_balancing_prices_<YYYY-MM>_<preliminary|final>[_<YYYY-MM-DD>].xlsx
The month is read from the dates inside the workbook, not from the link, because some links
point to the wrong month. A workbook whose content does not match its link is saved with a
"__source-<link name>" suffix, which process_mepso.py excludes, and is reported.

Known links (from raw/download-audit-*/mepso-files.csv and raw/fetch_log.csv) are skipped
unless --recheck is given. A file whose name exists with different content is a revision by
MEPSO: it is reported and kept aside as *.xlsx.revised-<date> unless --replace is given.
Every download is appended to raw/fetch_log.csv. Then run scripts/process_mepso.py.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import openpyxl

DATASET = Path(__file__).resolve().parents[1]          # datasets/mepso
PAGE = 'https://www.mepso.com.mk/index.php/mk/pbee'
SITE = 'https://www.mepso.com.mk/'
LINK = re.compile(r'href="([^"]*cena_poramnuvanje[^"]*\.xlsx)"', re.I)
MONTHS = {'januari': 1, 'fevruari': 2, 'mart': 3, 'april': 4, 'aril': 4, 'maj': 5, 'juni': 6, 'juli': 7,
          'avgust': 8, 'septemvri': 9, 'oktomvri': 10, 'noemvri': 11, 'dekemvri': 12}
LOG_FIELDS = ['fetched_at', 'url', 'http_status', 'sha256', 'bytes', 'content_period', 'saved_as', 'note']


def curl(url: str, out: Path) -> int:
    """Download url to out; return the HTTP status (curl uses the system certificate store)."""
    result = subprocess.run(['curl', '-sSL', '-A', 'Mozilla/5.0', '--max-time', '120', '-o', str(out),
                             '-w', '%{http_code}', url], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'curl failed for {url}: {result.stderr.strip()}')
    return int(result.stdout.strip() or 0)


def page_links(html: str) -> list[str]:
    urls = []
    for href in LINK.findall(html):
        url = urljoin(SITE, href.replace('\\', '/'))
        if url not in urls:
            urls.append(url)
    return urls


def link_info(url: str) -> tuple[int | None, int | None, str]:
    """(year, month, version) guessed from a link such as .../2026/oktomvri-preliminarna1.xlsx."""
    parts = url.rstrip('/').split('/')
    year = int(parts[-2]) if parts[-2].isdigit() else None
    stem = parts[-1].lower().removesuffix('.xlsx')
    month = next((n for name, n in MONTHS.items() if re.search(rf'(^|[-_]){name}', stem)), None)
    version = 'preliminary' if 'prelim' in stem else 'final' if 'kone' in stem else 'preliminary'
    return year, month, version


def variants(url: str) -> list[str]:
    """Spellings MEPSO has used for the same file (konecna/konecen/konecena, with or without '1')."""
    head, stem = url.rsplit('/', 1)
    stem = stem.removesuffix('.xlsx')
    base = stem[:-1] if stem.endswith('1') else stem
    words = [base]
    for typo, month in [('aril', 'april')]:                     # misspelled month names in links
        if re.search(rf'(^|[-_]){typo}', base):
            words.append(re.sub(rf'(^|[-_]){typo}', rf'\g<1>{month}', base))
    for a, b in [('konecna', 'konecen'), ('konecna', 'konecena'), ('konecen', 'konecna'), ('konecena', 'konecna')]:
        for w in list(words):
            if a in w:
                words.append(w.replace(a, b))
    out = []
    for w in words:
        for s in (w, w + '1'):
            candidate = f'{head}/{s}.xlsx'
            if candidate != url and candidate not in out:
                out.append(candidate)
    return out


def content_dates(path: Path) -> list[dt.date]:
    """Calendar dates in the price sheet (Excel dates or dd.mm.yyyy strings). Monthly workbooks
    start with the price sheet; DST supplements start with a notice sheet, so also look at the
    sheets whose name mentions the settlement price ("порамнување" / "poramnuvanje")."""
    found = []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheets = [wb.worksheets[0]] + [ws for ws in wb.worksheets[1:]
                                       if 'порамн' in ws.title.lower() or 'poramn' in ws.title.lower()]
        for ws in sheets:
            if found:
                break
            for row in ws.iter_rows(max_row=3000, values_only=True):
                for value in row:
                    if isinstance(value, dt.datetime):
                        found.append(value.date())
                    elif isinstance(value, dt.date):
                        found.append(value)
                    elif isinstance(value, str):
                        m = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', value)
                        if m:
                            try:
                                found.append(dt.date(int(m[3]), int(m[2]), int(m[1])))
                            except ValueError:
                                pass
    finally:
        wb.close()
    return [d for d in found if 2015 <= d.year <= 2100]


def target_name(dates: list[dt.date], version: str) -> tuple[str, str]:
    """(content period YYYY-MM, standard file name) from the dates inside a workbook."""
    period = collections.Counter(f'{d:%Y-%m}' for d in dates).most_common(1)[0][0]
    days = sorted({d for d in dates if f'{d:%Y-%m}' == period})
    suffix = f'_{days[0]:%Y-%m-%d}' if len(days) == 1 else ''      # single-day DST supplement
    return period, f'MEPSO_balancing_prices_{period}_{version}{suffix}.xlsx'


def known_urls(raw: Path) -> set[str]:
    known = set()
    for manifest in raw.glob('download-audit-*/mepso-files.csv'):
        with manifest.open(newline='', encoding='utf-8') as handle:
            for row in csv.DictReader(handle):
                known.add(row['url'])
                if row.get('repair_of'):
                    known.add(row['repair_of'])
    log = raw / 'fetch_log.csv'
    if log.exists():
        with log.open(newline='', encoding='utf-8') as handle:
            known.update(row['url'] for row in csv.DictReader(handle))
    return known


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--raw-dir', type=Path, default=DATASET / 'raw')
    ap.add_argument('--page', type=Path, help='Saved copy of the PBEE page instead of downloading it')
    ap.add_argument('--dry-run', action='store_true', help='List new links only; download nothing')
    ap.add_argument('--recheck', action='store_true', help='Download known links again to detect revisions')
    ap.add_argument('--replace', action='store_true', help='Overwrite a workbook that MEPSO revised')
    args = ap.parse_args()
    raw = args.raw_dir.resolve()
    raw.mkdir(parents=True, exist_ok=True)
    existing = {sha256(p): p for p in raw.rglob('*.xlsx')}

    with tempfile.TemporaryDirectory(prefix='mepso-fetch-') as tmp:
        tmp = Path(tmp)
        if args.page:
            html = args.page.read_text(encoding='utf-8', errors='replace')
        else:
            status = curl(PAGE, tmp / 'pbee.html')
            if status != 200:
                raise SystemExit(f'Could not load {PAGE}: HTTP {status}')
            html = (tmp / 'pbee.html').read_text(encoding='utf-8', errors='replace')
        links = page_links(html)
        known = set() if args.recheck else known_urls(raw)
        todo = [u for u in links if u not in known]
        print(f'{len(links)} workbook links on the page, {len(todo)} to fetch')
        if args.dry_run:
            for u in todo:
                print('  new:', u, link_info(u))
            return

        log_path = raw / 'fetch_log.csv'
        new_log = not log_path.exists()
        with log_path.open('a', newline='', encoding='utf-8') as handle:
            log = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
            if new_log:
                log.writeheader()
            for url in todo:
                record = dict(fetched_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), url=url)
                download = tmp / 'download.xlsx'
                got = None
                for candidate in [url] + variants(url):
                    status = curl(candidate, download)
                    if status == 200 and zipfile.is_zipfile(download):
                        got = candidate
                        break
                if got is None:
                    log.writerow(dict(record, http_status=status, note='not found (also tried spelling variants)'))
                    print(f'  missing  {url} (HTTP {status})')
                    continue
                digest = sha256(download)
                record.update(http_status=200, sha256=digest, bytes=download.stat().st_size,
                              note='' if got == url else f'found at {got}')
                if digest in existing:
                    log.writerow(dict(record, saved_as=existing[digest].relative_to(raw).as_posix(),
                                      note=(record['note'] + ' identical to an archived file').strip()))
                    print(f'  same     {url} = {existing[digest].relative_to(raw)}')
                    continue
                dates = content_dates(download)
                if not dates:
                    log.writerow(dict(record, note='no dates found in the workbook; not saved'))
                    print(f'  no dates {url}: not saved')
                    continue
                year, month, version = link_info(got)
                period, name = target_name(dates, version)
                if year and month and period != f'{year}-{month:02d}':
                    stem = got.rsplit('/', 1)[1].removesuffix('.xlsx')
                    name = name.removesuffix('.xlsx') + f'__source-{stem}.xlsx'
                    record['note'] = (record['note'] + f' link says {year}-{month:02d}, content is {period}').strip()
                target = raw / period[:4] / name
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists() and not args.replace:
                    # not *.xlsx, so the importer ignores it until it replaces the archived file
                    target = target.with_name(target.name + f'.revised-{dt.date.today():%Y-%m-%d}')
                    record['note'] = (record['note'] + ' revision of an archived file: kept aside, rerun with --replace to use it').strip()
                shutil.copyfile(download, target)
                existing[digest] = target
                log.writerow(dict(record, content_period=period, saved_as=target.relative_to(raw).as_posix()))
                print(f'  saved    {target.relative_to(raw)}  {record["note"]}')
    print('Next: python3 scripts/process_mepso.py')


if __name__ == '__main__':
    main()
