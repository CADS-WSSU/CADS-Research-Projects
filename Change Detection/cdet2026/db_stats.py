"""Empirical sanity check on docs.db — derive the date range and per-day document
counts from the database itself (never assume 1000/day or a fixed number of days).

The timestamp field in the cdet-api collection is `date` (ISO 8601, e.g.
2021-08-01T02:08:10.000Z); the day bucket is its first 10 chars (`date[:10]`), which is
exactly what build_doc_db stores in the `day` column and the server returns as `day`.

Used at day-loop startup (logged) and runnable standalone:
    python -m cdet2026.db_stats
"""
from __future__ import annotations

import statistics
from datetime import date

from cdet_api.models import Document, db

# The confirmed timestamp field name in the cdet-api server output / docs.db.
TIMESTAMP_FIELD = "date"


def day_of( timestamp: str) -> str:  # noqa: E251  (kept explicit for clarity)
    """Day bucket = first 10 chars of the `date` timestamp (YYYY-MM-DD)."""
    return timestamp[:10]


def db_stats() -> dict:
    db.connect(reuse_if_open=True)
    rows = db.execute_sql("SELECT day, COUNT(*) FROM documents GROUP BY day ORDER BY day").fetchall()
    days = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    first, last = days[0], days[-1]
    calendar_span = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
    return {
        "timestamp_field": TIMESTAMP_FIELD,
        "first_date": first,
        "last_date": last,
        "days_present": len(days),
        "calendar_span_days": calendar_span,
        "days_missing": calendar_span - len(days),
        "docs_total": sum(counts),
        "docs_per_day_min": min(counts),
        "docs_per_day_median": int(statistics.median(counts)),
        "docs_per_day_max": max(counts),
    }


def log_startup_stats(prefix: str = "[startup] ") -> dict:
    s = db_stats()
    print(f"{prefix}timestamp field = '{s['timestamp_field']}'; day = date[:10]")
    print(f"{prefix}date range: {s['first_date']} .. {s['last_date']}  "
          f"({s['days_present']} days present of {s['calendar_span_days']} calendar days; "
          f"{s['days_missing']} with no documents)")
    print(f"{prefix}docs/day: min={s['docs_per_day_min']} median={s['docs_per_day_median']} "
          f"max={s['docs_per_day_max']}  (total {s['docs_total']:,})")
    return s


if __name__ == "__main__":
    log_startup_stats(prefix="")
