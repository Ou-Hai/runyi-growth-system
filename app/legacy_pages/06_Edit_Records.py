from pathlib import Path

import pandas as pd
import streamlit as st

from data_manager import DAILY_FIELDS, REDEEM_FIELDS, get_week_start, recalculate_points
from ui import init_sidebar, inject_styles, render_hero, t

st.set_page_config(page_title="Edit Records", page_icon="✏️", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DAILY_LOG_FILE = DATA_DIR / "daily_log.csv"
REDEEM_LOG_FILE = DATA_DIR / "redeem_log.csv"


def load_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(path)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def safe_str(value) -> str:
    return "" if pd.isna(value) else str(value)


def safe_int(value, default=0) -> int:
    try:
        return default if pd.isna(value) else int(value)
    except Exception:
        return default


init_sidebar()
inject_styles()

render_hero(
    t("✏️ 编辑记录", "✏️ Edit Records"),
    t("修正历史记录后，积分会自动从日志重新计算。", "After correcting a record, points are recalculated directly from logs."),
    [t("每日记录", "Daily logs"), t("兑换记录", "Redeem logs"), t("自动重算", "Auto recalculation")],
)

daily_df = load_csv(DAILY_LOG_FILE, DAILY_FIELDS)
st.subheader(t("🗓️ 每日记录", "🗓️ Daily Log"))

if daily_df.empty:
    st.info(t("还没有每日记录。", "No daily log yet."))
else:
    daily_df["timestamp"] = daily_df["timestamp"].astype(str)
    daily_show = daily_df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
    st.dataframe(daily_show, use_container_width=True, hide_index=True)

    daily_show["display_label"] = daily_show["date"].astype(str) + " | " + daily_show["timestamp"].astype(str)
    selected_daily = st.selectbox(t("选择一条记录", "Select a row"), daily_show["display_label"].tolist())
    selected_row = daily_show[daily_show["display_label"] == selected_daily].iloc[0]
    row_idx = daily_df[daily_df["timestamp"].astype(str) == str(selected_row["timestamp"])].index[0]
    row = daily_df.loc[row_idx]

    with st.form("edit_daily_form"):
        new_date = st.text_input(t("日期", "Date"), value=safe_str(row["date"]))
        new_earned_tasks = st.text_area(t("加分任务", "Earned Tasks"), value=safe_str(row["earned_tasks"]))
        new_deduction_tasks = st.text_area(t("扣分任务", "Deduction Tasks"), value=safe_str(row["deduction_tasks"]))
        new_earned_points = st.number_input(t("加分", "Earned Points"), step=1, value=safe_int(row["earned_points"]))
        new_deduction_points = st.number_input(t("扣分", "Deduction Points"), step=1, value=safe_int(row["deduction_points"]))
        save_daily = st.form_submit_button(t("保存每日记录", "Save Daily Log"))

    if save_daily:
        week_start = get_week_start(new_date.strip())
        daily_df.at[row_idx, "date"] = new_date.strip()
        daily_df.at[row_idx, "week_start_date"] = week_start
        daily_df.at[row_idx, "earned_tasks"] = new_earned_tasks.strip()
        daily_df.at[row_idx, "deduction_tasks"] = new_deduction_tasks.strip()
        daily_df.at[row_idx, "earned_points"] = int(new_earned_points)
        daily_df.at[row_idx, "deduction_points"] = int(new_deduction_points)
        daily_df.at[row_idx, "net_change"] = int(new_earned_points) - int(new_deduction_points)
        save_csv(daily_df.sort_values(by="timestamp"), DAILY_LOG_FILE)
        recalculate_points()
        st.success(t("每日记录已更新。", "Daily log updated successfully."))
        st.rerun()

st.markdown("---")
redeem_df = load_csv(REDEEM_LOG_FILE, REDEEM_FIELDS)
st.subheader(t("🧸 兑换记录", "🧸 Redeem Log"))

if redeem_df.empty:
    st.info(t("还没有兑换记录。", "No redeem log records found."))
else:
    redeem_df["timestamp"] = redeem_df["timestamp"].astype(str)
    redeem_show = redeem_df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
    st.dataframe(redeem_show, use_container_width=True, hide_index=True)

    redeem_show["display_label"] = redeem_show["date"].astype(str) + " | " + redeem_show["timestamp"].astype(str)
    selected_label = st.selectbox(t("选择一条兑换记录", "Select a redeem row"), redeem_show["display_label"].tolist())
    selected_redeem = redeem_show[redeem_show["display_label"] == selected_label].iloc[0]
    redeem_row_idx = redeem_df[redeem_df["timestamp"].astype(str) == str(selected_redeem["timestamp"])].index[0]
    redeem_row = redeem_df.loc[redeem_row_idx]

    with st.form("edit_redeem_form"):
        new_redeem_date = st.text_input(t("兑换日期", "Redeem Date"), value=safe_str(redeem_row["date"]))
        new_reward_name = st.text_input(t("奖励名称", "Reward Name"), value=safe_str(redeem_row["reward_name"]))
        new_points_cost = st.number_input(t("消耗积分", "Points Cost"), step=1, value=safe_int(redeem_row["points_cost"]))
        new_points_after_redeem = st.number_input(
            t("兑换后积分", "Points After Redeem"),
            step=1,
            value=safe_int(redeem_row["points_after_redeem"]),
        )
        save_redeem = st.form_submit_button(t("保存兑换记录", "Save Redeem Log"))

    if save_redeem:
        redeem_df.at[redeem_row_idx, "date"] = new_redeem_date.strip()
        redeem_df.at[redeem_row_idx, "week_start_date"] = get_week_start(new_redeem_date.strip())
        redeem_df.at[redeem_row_idx, "reward_name"] = new_reward_name.strip()
        redeem_df.at[redeem_row_idx, "points_cost"] = int(new_points_cost)
        redeem_df.at[redeem_row_idx, "points_after_redeem"] = int(new_points_after_redeem)
        save_csv(redeem_df.sort_values(by="timestamp"), REDEEM_LOG_FILE)
        recalculate_points()
        st.success(t("兑换记录已更新。", "Redeem log updated successfully."))
        st.rerun()
