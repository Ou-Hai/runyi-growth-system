from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st

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


def _safe_int(value, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_daily_row(row: dict) -> dict:
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


def _normalize_redeem_row(row: dict) -> dict:
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


def _normalize_week_row(row: dict) -> dict:
    week_start = str(row.get("week_start_date", "") or "")
    timestamp = str(row.get("timestamp", "") or "")
    if not timestamp and week_start:
        timestamp = f"{week_start}T00:00:00"

    return {
        "week_start_date": week_start or get_current_week_start(),
        "timestamp": timestamp or _now_iso(),
        "weekly_start_points": _safe_int(row.get("weekly_start_points", WEEKLY_START_POINTS), WEEKLY_START_POINTS),
    }


def _sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda row: (str(row.get("timestamp", "")), str(row.get("date", ""))))


def _ensure_csv_file(path: Path, fieldnames: list[str]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()


@st.cache_data(show_spinner=False)
def _read_csv(path_str: str, fieldnames: tuple[str, ...]) -> list[dict]:
    path = Path(path_str)
    _ensure_csv_file(path, list(fieldnames))

    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    _ensure_csv_file(path, fieldnames)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def clear_data_caches() -> None:
    _read_csv.clear()


def initialize_log_file() -> None:
    _ensure_csv_file(LOG_FILE, DAILY_FIELDS)


def initialize_redeem_log_file() -> None:
    _ensure_csv_file(REDEEM_FILE, REDEEM_FIELDS)


def initialize_week_log_file() -> None:
    _ensure_csv_file(WEEK_FILE, WEEK_FIELDS)


def load_daily_logs() -> list[dict]:
    initialize_log_file()
    rows = [_normalize_daily_row(row) for row in _read_csv(str(LOG_FILE), tuple(DAILY_FIELDS))]
    return _sort_rows(rows)


def load_redeem_logs() -> list[dict]:
    initialize_redeem_log_file()
    rows = [_normalize_redeem_row(row) for row in _read_csv(str(REDEEM_FILE), tuple(REDEEM_FIELDS))]
    return _sort_rows(rows)


def load_week_logs() -> list[dict]:
    initialize_week_log_file()
    rows = [_normalize_week_row(row) for row in _read_csv(str(WEEK_FILE), tuple(WEEK_FIELDS))]
    return sorted(rows, key=lambda row: row["week_start_date"])


def ensure_current_week_initialized() -> None:
    initialize_week_log_file()
    current_week_start = get_current_week_start()
    rows = load_week_logs()

    if any(row["week_start_date"] == current_week_start for row in rows):
        return

    rows.append(
        {
            "week_start_date": current_week_start,
            "timestamp": _now_iso(),
            "weekly_start_points": WEEKLY_START_POINTS,
        }
    )
    _write_csv(WEEK_FILE, WEEK_FIELDS, sorted(rows, key=lambda row: row["week_start_date"]))
    clear_data_caches()


def ensure_logged_weeks_initialized() -> None:
    initialize_week_log_file()

    existing_rows = load_week_logs()
    existing_weeks = {row["week_start_date"] for row in existing_rows}

    referenced_weeks = {get_current_week_start()}
    referenced_weeks.update(
        row["week_start_date"] for row in load_daily_logs() if row.get("week_start_date")
    )
    referenced_weeks.update(
        row["week_start_date"] for row in load_redeem_logs() if row.get("week_start_date")
    )

    missing_weeks = sorted(referenced_weeks - existing_weeks)
    if not missing_weeks:
        return

    for week_start_date in missing_weeks:
        existing_rows.append(
            {
                "week_start_date": week_start_date,
                "timestamp": f"{week_start_date}T00:00:00",
                "weekly_start_points": WEEKLY_START_POINTS,
            }
        )

    _write_csv(WEEK_FILE, WEEK_FIELDS, sorted(existing_rows, key=lambda row: row["week_start_date"]))
    clear_data_caches()


def _calculate_points_from_rows(
    week_rows: list[dict],
    daily_rows: list[dict],
    redeem_rows: list[dict],
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


def get_current_week_daily_logs() -> list[dict]:
    current_week_start = get_current_week_start()
    return [row for row in load_daily_logs() if row["week_start_date"] == current_week_start]


def get_current_week_redeem_logs() -> list[dict]:
    current_week_start = get_current_week_start()
    return [row for row in load_redeem_logs() if row["week_start_date"] == current_week_start]


def append_daily_log(earned_tasks, deduction_tasks, earned_points, deduction_points, net_change):
    rows = load_daily_logs()
    rows.append(
        {
            "date": _today().isoformat(),
            "timestamp": _now_iso(),
            "week_start_date": get_current_week_start(),
            "earned_tasks": " | ".join(earned_tasks),
            "deduction_tasks": " | ".join(deduction_tasks),
            "earned_points": int(earned_points),
            "deduction_points": int(deduction_points),
            "net_change": int(net_change),
        }
    )
    _write_csv(LOG_FILE, DAILY_FIELDS, _sort_rows(rows))
    clear_data_caches()


def upsert_daily_log(earned_tasks, deduction_tasks, earned_points, deduction_points, net_change):
    ensure_current_week_initialized()
    rows = load_daily_logs()
    today_str = _today().isoformat()
    current_week_start = get_current_week_start()
    updated = False

    for row in rows:
        if row["date"] == today_str and row["week_start_date"] == current_week_start:
            row["timestamp"] = _now_iso()
            row["earned_tasks"] = " | ".join(earned_tasks)
            row["deduction_tasks"] = " | ".join(deduction_tasks)
            row["earned_points"] = int(earned_points)
            row["deduction_points"] = int(deduction_points)
            row["net_change"] = int(net_change)
            updated = True
            break

    if not updated:
        rows.append(
            {
                "date": today_str,
                "timestamp": _now_iso(),
                "week_start_date": current_week_start,
                "earned_tasks": " | ".join(earned_tasks),
                "deduction_tasks": " | ".join(deduction_tasks),
                "earned_points": int(earned_points),
                "deduction_points": int(deduction_points),
                "net_change": int(net_change),
            }
        )

    _write_csv(LOG_FILE, DAILY_FIELDS, _sort_rows(rows))
    clear_data_caches()


def append_redeem_log(reward_name, points_cost, points_after_redeem):
    ensure_current_week_initialized()
    rows = load_redeem_logs()
    rows.append(
        {
            "date": _today().isoformat(),
            "timestamp": _now_iso(),
            "week_start_date": get_current_week_start(),
            "reward_name": reward_name,
            "points_cost": int(points_cost),
            "points_after_redeem": int(points_after_redeem),
        }
    )
    _write_csv(REDEEM_FILE, REDEEM_FIELDS, _sort_rows(rows))
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

    if last_daily and (not last_redeem or last_daily["timestamp"] >= last_redeem["timestamp"]):
        daily_rows.pop()
        _write_csv(LOG_FILE, DAILY_FIELDS, daily_rows)
        clear_data_caches()
        return f"Last daily record undone. Current points: {load_points()}."

    redeem_rows.pop()
    _write_csv(REDEEM_FILE, REDEEM_FIELDS, redeem_rows)
    clear_data_caches()
    return f"Last reward redemption undone. Current points: {load_points()}."
