from __future__ import annotations

import csv
import os
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import streamlit as st
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, delete, func, insert, select, update
from sqlalchemy.engine import Engine

from rules import WEEKLY_START_POINTS

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

LOG_FILE = DATA_DIR / "daily_log.csv"
REDEEM_FILE = DATA_DIR / "redeem_log.csv"
WEEK_FILE = DATA_DIR / "weekly_log.csv"

DAILY_FIELDS = [
    "date",
    "timestamp",
    "week_start_date",
    "earned_tasks",
    "deduction_tasks",
    "earned_points",
    "deduction_points",
    "net_change",
]

REDEEM_FIELDS = [
    "date",
    "timestamp",
    "week_start_date",
    "reward_name",
    "points_cost",
    "points_after_redeem",
]

WEEK_FIELDS = ["week_start_date", "timestamp", "weekly_start_points"]

metadata = MetaData()


def StringColumn(name: str, primary_key: bool = False) -> Any:
    return TableColumnFactory(name, String, primary_key=primary_key)


def IntegerColumn(name: str, primary_key: bool = False) -> Any:
    return TableColumnFactory(name, Integer, primary_key=primary_key)


def TableColumnFactory(name: str, column_type: Any, primary_key: bool = False) -> Any:
    return Column(name, column_type, primary_key=primary_key, nullable=False, default="" if column_type is String else 0)


daily_log_table = Table(
    "daily_log",
    metadata,
    StringColumn("date", primary_key=False),
    StringColumn("timestamp", primary_key=True),
    StringColumn("week_start_date"),
    StringColumn("earned_tasks"),
    StringColumn("deduction_tasks"),
    IntegerColumn("earned_points"),
    IntegerColumn("deduction_points"),
    IntegerColumn("net_change"),
)

redeem_log_table = Table(
    "redeem_log",
    metadata,
    StringColumn("date", primary_key=False),
    StringColumn("timestamp", primary_key=True),
    StringColumn("week_start_date"),
    StringColumn("reward_name"),
    IntegerColumn("points_cost"),
    IntegerColumn("points_after_redeem"),
)

weekly_log_table = Table(
    "weekly_log",
    metadata,
    StringColumn("week_start_date", primary_key=True),
    StringColumn("timestamp"),
    IntegerColumn("weekly_start_points"),
)


def _today() -> date:
    return date.today()


def get_week_start(value: date | datetime | str | None = None) -> str:
    if value is None:
        base_date = _today()
    elif isinstance(value, datetime):
        base_date = value.date()
    elif isinstance(value, date):
        base_date = value
    else:
        base_date = datetime.fromisoformat(str(value)).date()

    week_start = base_date - timedelta(days=base_date.weekday())
    return week_start.isoformat()


def get_current_week_start() -> str:
    return get_week_start(_today())


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_daily_row(row: dict[str, Any]) -> dict[str, Any]:
    row_date = str(row.get("date", "") or "")
    timestamp = str(row.get("timestamp", "") or "")
    if not timestamp and row_date:
        timestamp = f"{row_date}T00:00:00"

    return {
        "date": row_date,
        "timestamp": timestamp,
        "week_start_date": str(row.get("week_start_date", "") or get_week_start(row_date or _today())),
        "earned_tasks": str(row.get("earned_tasks", "") or ""),
        "deduction_tasks": str(row.get("deduction_tasks", "") or ""),
        "earned_points": _safe_int(row.get("earned_points", 0)),
        "deduction_points": _safe_int(row.get("deduction_points", 0)),
        "net_change": _safe_int(row.get("net_change", 0)),
    }


def _normalize_redeem_row(row: dict[str, Any]) -> dict[str, Any]:
    row_date = str(row.get("date", "") or "")
    timestamp = str(row.get("timestamp", "") or "")
    if not timestamp and row_date:
        timestamp = f"{row_date}T00:00:00"

    return {
        "date": row_date,
        "timestamp": timestamp,
        "week_start_date": str(row.get("week_start_date", "") or get_week_start(row_date or _today())),
        "reward_name": str(row.get("reward_name", "") or ""),
        "points_cost": _safe_int(row.get("points_cost", 0)),
        "points_after_redeem": _safe_int(row.get("points_after_redeem", 0)),
    }


def _normalize_week_row(row: dict[str, Any]) -> dict[str, Any]:
    week_start = str(row.get("week_start_date", "") or "")
    timestamp = str(row.get("timestamp", "") or "")
    if not timestamp and week_start:
        timestamp = f"{week_start}T00:00:00"

    return {
        "week_start_date": week_start or get_current_week_start(),
        "timestamp": timestamp or _now_iso(),
        "weekly_start_points": _safe_int(row.get("weekly_start_points", WEEKLY_START_POINTS), WEEKLY_START_POINTS),
    }


def _sort_rows(rows: list[dict[str, Any]], sort_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: tuple(str(row.get(key, "")) for key in sort_keys))


def _get_database_url() -> str:
    candidates = [
        os.getenv("DATABASE_URL"),
        os.getenv("SUPABASE_DB_URL"),
        os.getenv("SUPABASE_DATABASE_URL"),
    ]

    try:
        candidates.extend(
            [
                st.secrets.get("DATABASE_URL"),
                st.secrets.get("SUPABASE_DB_URL"),
                st.secrets.get("SUPABASE_DATABASE_URL"),
            ]
        )
    except Exception:
        pass

    for value in candidates:
        if value:
            return str(value)

    raise RuntimeError(
        "DATABASE_URL is not configured. Set DATABASE_URL or SUPABASE_DB_URL in environment variables or Streamlit secrets."
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    database_url = _get_database_url()
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    engine = create_engine(database_url, future=True, pool_pre_ping=True)
    metadata.create_all(engine)
    _bootstrap_from_csv_if_empty(engine)
    return engine


def clear_data_caches() -> None:
    load_daily_logs.clear()
    load_redeem_logs.clear()
    load_week_logs.clear()


def _table_count(engine: Engine, table: Table) -> int:
    with engine.begin() as conn:
        result = conn.execute(select(func.count()).select_from(table))
        return int(result.scalar_one())


def _read_csv_rows(path: Path, fieldnames: list[str]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    for row in rows:
        for field in fieldnames:
            row.setdefault(field, "")
    return rows


def _bootstrap_from_csv_if_empty(engine: Engine) -> None:
    daily_count = _table_count(engine, daily_log_table)
    redeem_count = _table_count(engine, redeem_log_table)
    weekly_count = _table_count(engine, weekly_log_table)

    if daily_count or redeem_count or weekly_count:
        return

    daily_rows = [_normalize_daily_row(row) for row in _read_csv_rows(LOG_FILE, DAILY_FIELDS)]
    redeem_rows = [_normalize_redeem_row(row) for row in _read_csv_rows(REDEEM_FILE, REDEEM_FIELDS)]
    weekly_rows = [_normalize_week_row(row) for row in _read_csv_rows(WEEK_FILE, WEEK_FIELDS)]

    referenced_weeks = {get_current_week_start()}
    referenced_weeks.update(row["week_start_date"] for row in daily_rows if row.get("week_start_date"))
    referenced_weeks.update(row["week_start_date"] for row in redeem_rows if row.get("week_start_date"))
    existing_weeks = {row["week_start_date"] for row in weekly_rows}

    for week_start_date in sorted(referenced_weeks - existing_weeks):
        weekly_rows.append(
            {
                "week_start_date": week_start_date,
                "timestamp": f"{week_start_date}T00:00:00",
                "weekly_start_points": WEEKLY_START_POINTS,
            }
        )

    with engine.begin() as conn:
        if weekly_rows:
            conn.execute(insert(weekly_log_table), _sort_rows(weekly_rows, ("week_start_date",)))
        if daily_rows:
            conn.execute(insert(daily_log_table), _sort_rows(daily_rows, ("timestamp", "date")))
        if redeem_rows:
            conn.execute(insert(redeem_log_table), _sort_rows(redeem_rows, ("timestamp", "date")))


def initialize_log_file() -> None:
    get_engine()


def initialize_redeem_log_file() -> None:
    get_engine()


def initialize_week_log_file() -> None:
    get_engine()


def _fetch_rows(table: Table, fieldnames: list[str], order_columns: list[Any]) -> list[dict[str, Any]]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(select(*[table.c[name] for name in fieldnames]).order_by(*order_columns)).mappings().all()
    return [dict(row) for row in rows]


@st.cache_data(show_spinner=False)
def load_daily_logs() -> list[dict[str, Any]]:
    rows = _fetch_rows(daily_log_table, DAILY_FIELDS, [daily_log_table.c.timestamp, daily_log_table.c.date])
    return [_normalize_daily_row(row) for row in rows]


@st.cache_data(show_spinner=False)
def load_redeem_logs() -> list[dict[str, Any]]:
    rows = _fetch_rows(redeem_log_table, REDEEM_FIELDS, [redeem_log_table.c.timestamp, redeem_log_table.c.date])
    return [_normalize_redeem_row(row) for row in rows]


@st.cache_data(show_spinner=False)
def load_week_logs() -> list[dict[str, Any]]:
    rows = _fetch_rows(weekly_log_table, WEEK_FIELDS, [weekly_log_table.c.week_start_date])
    return [_normalize_week_row(row) for row in rows]


def ensure_current_week_initialized() -> None:
    initialize_week_log_file()
    current_week_start = get_current_week_start()
    rows = load_week_logs()
    if any(row["week_start_date"] == current_week_start for row in rows):
        return

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            insert(weekly_log_table).values(
                week_start_date=current_week_start,
                timestamp=_now_iso(),
                weekly_start_points=WEEKLY_START_POINTS,
            )
        )
    clear_data_caches()


def ensure_logged_weeks_initialized() -> None:
    initialize_week_log_file()

    existing_rows = load_week_logs()
    existing_weeks = {row["week_start_date"] for row in existing_rows}

    referenced_weeks = {get_current_week_start()}
    referenced_weeks.update(row["week_start_date"] for row in load_daily_logs() if row.get("week_start_date"))
    referenced_weeks.update(row["week_start_date"] for row in load_redeem_logs() if row.get("week_start_date"))

    missing_weeks = sorted(referenced_weeks - existing_weeks)
    if not missing_weeks:
        return

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            insert(weekly_log_table),
            [
                {
                    "week_start_date": week_start_date,
                    "timestamp": f"{week_start_date}T00:00:00",
                    "weekly_start_points": WEEKLY_START_POINTS,
                }
                for week_start_date in missing_weeks
            ],
        )
    clear_data_caches()


def _calculate_points_from_rows(
    week_rows: list[dict[str, Any]],
    daily_rows: list[dict[str, Any]],
    redeem_rows: list[dict[str, Any]],
) -> int:
    starting_total = sum(_safe_int(row.get("weekly_start_points", 0)) for row in week_rows)
    earned_total = sum(_safe_int(row.get("net_change", 0)) for row in daily_rows)
    redeem_total = sum(_safe_int(row.get("points_cost", 0)) for row in redeem_rows)
    return starting_total + earned_total - redeem_total


def load_points() -> int:
    ensure_logged_weeks_initialized()
    return _calculate_points_from_rows(load_week_logs(), load_daily_logs(), load_redeem_logs())


def recalculate_points() -> int:
    clear_data_caches()
    ensure_current_week_initialized()
    return load_points()


def get_current_week_daily_logs() -> list[dict[str, Any]]:
    current_week_start = get_current_week_start()
    return [row for row in load_daily_logs() if row["week_start_date"] == current_week_start]


def get_current_week_redeem_logs() -> list[dict[str, Any]]:
    current_week_start = get_current_week_start()
    return [row for row in load_redeem_logs() if row["week_start_date"] == current_week_start]


def append_daily_log(earned_tasks, deduction_tasks, earned_points, deduction_points, net_change):
    ensure_current_week_initialized()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            insert(daily_log_table).values(
                date=_today().isoformat(),
                timestamp=_now_iso(),
                week_start_date=get_current_week_start(),
                earned_tasks=" | ".join(earned_tasks),
                deduction_tasks=" | ".join(deduction_tasks),
                earned_points=int(earned_points),
                deduction_points=int(deduction_points),
                net_change=int(net_change),
            )
        )
    clear_data_caches()


def upsert_daily_log(earned_tasks, deduction_tasks, earned_points, deduction_points, net_change):
    ensure_current_week_initialized()
    engine = get_engine()
    today_str = _today().isoformat()
    current_week_start = get_current_week_start()
    payload = {
        "date": today_str,
        "timestamp": _now_iso(),
        "week_start_date": current_week_start,
        "earned_tasks": " | ".join(earned_tasks),
        "deduction_tasks": " | ".join(deduction_tasks),
        "earned_points": int(earned_points),
        "deduction_points": int(deduction_points),
        "net_change": int(net_change),
    }

    with engine.begin() as conn:
        existing = conn.execute(
            select(daily_log_table.c.timestamp)
            .where(daily_log_table.c.date == today_str)
            .where(daily_log_table.c.week_start_date == current_week_start)
            .limit(1)
        ).scalar_one_or_none()

        if existing is None:
            conn.execute(insert(daily_log_table).values(**payload))
        else:
            conn.execute(
                update(daily_log_table)
                .where(daily_log_table.c.timestamp == existing)
                .values(**payload)
            )
    clear_data_caches()


def append_redeem_log(reward_name, points_cost, points_after_redeem):
    ensure_current_week_initialized()
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            insert(redeem_log_table).values(
                date=_today().isoformat(),
                timestamp=_now_iso(),
                week_start_date=get_current_week_start(),
                reward_name=reward_name,
                points_cost=int(points_cost),
                points_after_redeem=int(points_after_redeem),
            )
        )
    clear_data_caches()


def update_daily_log_by_timestamp(
    timestamp: str,
    *,
    row_date: str,
    earned_tasks: str,
    deduction_tasks: str,
    earned_points: int,
    deduction_points: int,
) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            update(daily_log_table)
            .where(daily_log_table.c.timestamp == timestamp)
            .values(
                date=row_date,
                week_start_date=get_week_start(row_date),
                earned_tasks=earned_tasks.strip(),
                deduction_tasks=deduction_tasks.strip(),
                earned_points=int(earned_points),
                deduction_points=int(deduction_points),
                net_change=int(earned_points) - int(deduction_points),
            )
        )
    clear_data_caches()


def update_redeem_log_by_timestamp(
    timestamp: str,
    *,
    row_date: str,
    reward_name: str,
    points_cost: int,
    points_after_redeem: int,
) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            update(redeem_log_table)
            .where(redeem_log_table.c.timestamp == timestamp)
            .values(
                date=row_date,
                week_start_date=get_week_start(row_date),
                reward_name=reward_name.strip(),
                points_cost=int(points_cost),
                points_after_redeem=int(points_after_redeem),
            )
        )
    clear_data_caches()


def reset_week():
    ensure_current_week_initialized()
    clear_data_caches()
    return get_current_week_start()


def undo_last_action():
    daily_rows = load_daily_logs()
    redeem_rows = load_redeem_logs()

    last_daily = daily_rows[-1] if daily_rows else None
    last_redeem = redeem_rows[-1] if redeem_rows else None

    if not last_daily and not last_redeem:
        return f"No action to undo. Current points: {load_points()}."

    engine = get_engine()
    with engine.begin() as conn:
        if last_daily and (not last_redeem or last_daily["timestamp"] >= last_redeem["timestamp"]):
            conn.execute(delete(daily_log_table).where(daily_log_table.c.timestamp == last_daily["timestamp"]))
            clear_data_caches()
            return f"Last daily record undone. Current points: {load_points()}."

        conn.execute(delete(redeem_log_table).where(redeem_log_table.c.timestamp == last_redeem["timestamp"]))
    clear_data_caches()
    return f"Last reward redemption undone. Current points: {load_points()}."
