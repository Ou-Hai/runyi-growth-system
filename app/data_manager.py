import json
import csv
from pathlib import Path
from datetime import datetime

POINTS_FILE = Path("data/points.json")
LOG_FILE = Path("data/daily_log.csv")


def load_points():
    if not POINTS_FILE.exists():
        return 2

    with open(POINTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("weekly_points", 2)


def save_points(points):
    POINTS_FILE.parent.mkdir(exist_ok=True)

    with open(POINTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"weekly_points": points}, f, ensure_ascii=False, indent=2)


def initialize_log_file():
    LOG_FILE.parent.mkdir(exist_ok=True)

    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["date", "earned_tasks", "deduction_tasks", "earned_points", "deduction_points", "net_change"]
            )


def append_daily_log(earned_tasks, deduction_tasks, earned_points, deduction_points, net_change):
    initialize_log_file()

    today_str = datetime.today().strftime("%Y-%m-%d")

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                today_str,
                " | ".join(earned_tasks),
                " | ".join(deduction_tasks),
                earned_points,
                deduction_points,
                net_change,
            ]
        )


def load_daily_logs():
    initialize_log_file()

    rows = []
    with open(LOG_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def initialize_redeem_log_file():
    redeem_file = Path("data/redeem_log.csv")
    redeem_file.parent.mkdir(exist_ok=True)

    if not redeem_file.exists():
        with open(redeem_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "reward_name", "points_cost", "points_after_redeem"])


def append_redeem_log(reward_name, points_cost, points_after_redeem):
    initialize_redeem_log_file()

    redeem_file = Path("data/redeem_log.csv")
    today_str = datetime.today().strftime("%Y-%m-%d")

    with open(redeem_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([today_str, reward_name, points_cost, points_after_redeem])


def load_redeem_logs():
    redeem_file = Path("data/redeem_log.csv")
    initialize_redeem_log_file()

    rows = []
    with open(redeem_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows

def reset_week():
    """
    Reset the weekly system:
    - set points to starting value
    - clear daily logs
    """

    # reset points
    save_points(2)

    # clear daily log
    with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "date",
                "earned_tasks",
                "deduction_tasks",
                "earned_points",
                "deduction_points",
                "net_change",
            ]
        )