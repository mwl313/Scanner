from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Iterable

from app.utils.datetime_utils import as_kst, utcnow


def build_report_timestamp(now: datetime | None = None) -> str:
    target = as_kst(now or utcnow())
    return target.strftime('%Y%m%d-%H%M%S')


def ensure_report_dir(output_dir: str | Path) -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def write_markdown_report(content: str, *, output_dir: str | Path, prefix: str, now: datetime | None = None) -> Path:
    directory = ensure_report_dir(output_dir)
    path = directory / f'{prefix}-{build_report_timestamp(now)}.md'
    path.write_text(content, encoding='utf-8')
    return path


def write_csv_report(
    *,
    rows: Iterable[dict],
    fieldnames: list[str],
    output_dir: str | Path,
    prefix: str,
    now: datetime | None = None,
) -> Path:
    directory = ensure_report_dir(output_dir)
    path = directory / f'{prefix}-{build_report_timestamp(now)}.csv'
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return path

