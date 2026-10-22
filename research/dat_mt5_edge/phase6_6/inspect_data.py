"""Prepared offline audit, not a broker interface; no archive extraction/execution."""
import argparse
import csv
import ctypes
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import stat
import time
from datetime import datetime, timezone

SOURCE = Path(r"C:\DirectiveAutoTrader\Researchdata\data\data")
MAX_FILES = 20000
MAX_FILE_BYTES = 2 * 1024**3
MAX_HASH_BYTES = 8 * 1024**3
MAX_DECODED_BYTES = 128 * 1024**2
MAX_LINE_BYTES = 65536
MAX_ROWS = 500000


def reparse(p):
    s = p.lstat()
    return p.is_symlink() or bool(getattr(s, 'st_file_attributes', 0) & 0x400)


def boundary(source, output, attestation):
    if os.name != 'nt':
        raise ValueError('BLOCKED: Windows restricted source session required')
    if ctypes.windll.shell32.IsUserAnAdmin():
        raise ValueError('BLOCKED: administrator token')
    if attestation != 'VERIFIED_STANDARD_USER_SOURCE_READ_ONLY':
        raise ValueError('BLOCKED: independent restriction verification missing')
    if source != SOURCE or not source.is_dir():
        raise ValueError('BLOCKED: exact source unavailable')
    # Refuse junctions/reparse points in the source/output ancestor chains.
    for p in (source, *source.parents, output, *output.parents):
        if p.exists() and reparse(p):
            raise ValueError('BLOCKED: reparse path')
    a, b = source.resolve(), output.resolve()
    if a == b or a in b.parents or b in a.parents:
        raise ValueError('BLOCKED: output overlaps source')
    forbidden = Path(r'C:\DirectiveAutoTrader').resolve()
    if b == forbidden or forbidden in b.parents:
        raise ValueError('BLOCKED: output under production tree')
    if not output.is_dir():
        raise ValueError('BLOCKED: operator must provide existing isolated output')


def census(source, output):
    start = time.monotonic()
    total = 0
    count = 0
    complete = True
    hashes_complete = True
    with (output / 'inventory.jsonl').open('x', encoding='utf-8') as dest:
        stack = [source]
        while stack:
            directory = stack.pop()
            try:
                with os.scandir(directory) as entries:
                    for entry in entries:
                        if count >= MAX_FILES or time.monotonic() - start > 600:
                            complete = False
                            break
                        p = Path(entry.path)
                        s = p.lstat()
                        rel = p.relative_to(source).as_posix()
                        if reparse(p):
                            dest.write(json.dumps(dict(path=rel, status='SKIP_REPARSE'))+'\n')
                            complete = False
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(p)
                            continue
                        count += 1
                        row = dict(path=rel, bytes=s.st_size,
                                   modified_ns=s.st_mtime_ns,
                                   extension=''.join(p.suffixes).lower(),
                                   instrument_hint='FILENAME_ONLY_NOT_VERIFIED',
                                   status='ZERO_BYTE_FAIL' if s.st_size == 0 else 'UNINSPECTED',
                                   sha256=None)
                        if not stat.S_ISREG(s.st_mode):
                            row['status'] = 'NON_REGULAR_SKIP'
                            complete = False
                        elif s.st_size > MAX_FILE_BYTES or total+s.st_size > MAX_HASH_BYTES:
                            row['status'] = 'HASH_BUDGET_SKIP'
                            hashes_complete = False
                        else:
                            h = hashlib.sha256()
                            read = 0
                            with p.open('rb') as stream:
                                while True:
                                    if time.monotonic()-start > 600 or read > MAX_FILE_BYTES:
                                        raise ValueError('census time/file budget reached')
                                    chunk = stream.read(1024**2)
                                    if not chunk:
                                        break
                                    read += len(chunk)
                                    total += len(chunk)
                                    if total > MAX_HASH_BYTES:
                                        raise ValueError('census total hash budget reached')
                                    h.update(chunk)
                            after = p.stat()
                            if (after.st_size, after.st_mtime_ns) != (s.st_size, s.st_mtime_ns):
                                row['status'] = 'UNSTABLE_SOURCE_FAIL'
                                hashes_complete = False
                            else:
                                row['sha256'] = h.hexdigest()
                        dest.write(json.dumps(row, sort_keys=True)+'\n')
                    else:
                        continue
                    break
            except OSError as exc:
                complete = False
                dest.write(json.dumps(dict(path=directory.relative_to(source).as_posix(),
                                           status='ACCESS_ERROR', errno=exc.errno))+'\n')
    return dict(file_count=count, enumeration_complete=complete,
                checksums_complete=hashes_complete and complete, bytes_hashed=total,
                archives_extracted=False, certification='NOT_EVALUATED')


def audit(source, schema):
    if not schema.get('reviewed_schema'):
        raise ValueError('BLOCKED: schema not reviewed')
    relative = Path(schema['relative_path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('BLOCKED: invalid relative path')
    p = source / relative
    if any(reparse(q) for q in (p, *p.parents) if q.exists()):
        raise ValueError('BLOCKED: reparse source')
    if p.suffix.lower() not in ('.csv', '.gz'):
        raise ValueError('BLOCKED: this package supports plain/gzip CSV only')
    before = p.stat()
    if before.st_size > MAX_FILE_BYTES:
        raise ValueError('BLOCKED: compressed source exceeds budget')
    if schema['timestamp_convention'] != 'UTC_VERIFIED':
        raise ValueError('BLOCKED: resolve timezone/DST externally first')
    columns = schema['columns']
    if schema['timeframe_seconds'] <= 0:
        raise ValueError('BLOCKED: invalid expected timeframe')
    start = time.monotonic()
    rows = decoded = duplicates = disorder = invalid = large_gaps = weekends = 0
    first = last = previous = None
    seen = set()
    complete = True
    seal = False
    opener = gzip.open if p.suffix.lower() == '.gz' else open
    with opener(p, 'rb') as stream:
        def lines():
            nonlocal decoded
            while True:
                raw = stream.readline(MAX_LINE_BYTES + 1)
                if not raw:
                    return
                decoded += len(raw)
                if len(raw) > MAX_LINE_BYTES or decoded > MAX_DECODED_BYTES:
                    raise ValueError('bounded CSV expansion/line limit exceeded')
                yield raw.decode(schema.get('encoding', 'utf-8-sig'), errors='strict')
        reader = csv.reader(lines(), delimiter=schema['delimiter'])
        if schema.get('header', True):
            next(reader, None)
        for record in reader:
            if rows >= MAX_ROWS or time.monotonic()-start > 30:
                complete = False
                break
            stamp = datetime.strptime(record[columns['timestamp']], schema['timestamp_format'])
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            stamp = stamp.astimezone(timezone.utc)
            # Inspect timestamp only; never parse holdout prices or continue past it.
            if stamp >= datetime(2026, 1, 1, tzinfo=timezone.utc):
                complete = False
                seal = True
                break
            rows += 1
            first = stamp if first is None else min(first, stamp)
            last = stamp if last is None else max(last, stamp)
            if previous:
                disorder += stamp < previous
                large_gaps += (stamp-previous).total_seconds() > schema['timeframe_seconds']
            previous = stamp
            weekends += stamp.weekday() >= 5
            # Timestamp duplicates include legitimate multi-ticks: this parser is OHLC only.
            duplicates += stamp in seen
            seen.add(stamp)
            o, h, l, c = (float(record[columns[k]]) for k in ('open','high','low','close'))
            invalid += not (all(math.isfinite(x) and x > 0 for x in (o,h,l,c))
                            and l <= min(o,c) <= max(o,c) <= h)
    after = p.stat()
    stable = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    return dict(relative_path=relative.as_posix(), inspected_pre2026_rows=rows,
                first_inspected_utc=first.isoformat() if first else None,
                last_inspected_utc=last.isoformat() if last else None,
                complete_stream=complete, stopped_before_2026_prices=seal,
                duplicate_bar_timestamps=duplicates, backward_timestamps=disorder,
                invalid_ohlc=invalid, large_timestamp_gaps_not_calendar_missing=large_gaps,
                weekend_rows_not_automatically_invalid=weekends, source_stable=stable,
                bid_ask='NOT_EVALUATED', timezone='OPERATOR_ATTESTED_NOT_INDEPENDENTLY_PROVEN',
                calendar_coverage='NOT_EVALUATED', volume_semantics='NOT_EVALUATED',
                contract_rolls='NOT_EVALUATED', rights='NOT_EVALUATED',
                certification='FAIL' if invalid or disorder or not stable or rows == 0
                else 'PENDING_REVIEW_NOT_CERTIFIED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('inventory', 'audit'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--restriction-attestation', required=True)
    parser.add_argument('--schema', type=Path)
    args = parser.parse_args()
    boundary(SOURCE, args.output, args.restriction_attestation)
    if args.mode == 'inventory':
        result = census(SOURCE, args.output)
        name = 'inventory_summary.json'
    else:
        if args.schema is None:
            raise ValueError('schema required')
        result = audit(SOURCE, json.loads(args.schema.read_text(encoding='utf-8')))
        name = 'quality_summary.json'
    with (args.output / name).open('x', encoding='utf-8') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)


if __name__ == '__main__':
    main()
