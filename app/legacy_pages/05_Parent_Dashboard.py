import pandas as pd
import streamlit as st

from data_manager import (
    get_current_week_daily_logs,
    get_current_week_redeem_logs,
    get_current_week_start,
    load_points,
)
from rules import EARNING_TASKS
from ui import init_sidebar, inject_styles, render_hero, t

st.set_page_config(page_title="Parent Dashboard", page_icon="👨‍👩‍👦", layout="wide")

init_sidebar()
inject_styles()

current_points = load_points()
daily_logs = get_current_week_daily_logs()
redeem_logs = get_current_week_redeem_logs()

render_hero(
    t("👨‍👩‍👦 家长面板", "👨‍👩‍👦 Parent Dashboard"),
    "",
    [t("本周数据", "Weekly data"), t("习惯趋势", "Habit trends"), t("兑换情况", "Rewards")],
)

daily_df = pd.DataFrame(daily_logs)
redeem_df = pd.DataFrame(redeem_logs)

if not daily_df.empty:
    daily_df["earned_points"] = pd.to_numeric(daily_df["earned_points"])
    daily_df["deduction_points"] = pd.to_numeric(daily_df["deduction_points"])
    daily_df["net_change"] = pd.to_numeric(daily_df["net_change"])

if not redeem_df.empty:
    redeem_df["points_cost"] = pd.to_numeric(redeem_df["points_cost"])
    redeem_df["points_after_redeem"] = pd.to_numeric(redeem_df["points_after_redeem"])

task_counter = {task["label_en"]: 0 for task in EARNING_TASKS}
if not daily_df.empty:
    for task_str in daily_df["earned_tasks"].fillna(""):
        for item in [part.strip() for part in str(task_str).split("|") if part.strip()]:
            if item in task_counter:
                task_counter[item] += 1

weekly_net_growth = int(daily_df["net_change"].sum()) if not daily_df.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("当前可用积分", "Current Points"), current_points)
col2.metric(t("本周净增长", "Weekly Net Growth"), weekly_net_growth)
col3.metric(t("记录天数", "Recorded Days"), len(daily_df))
col4.metric(t("本周开始日期", "Week Start"), get_current_week_start())

st.markdown("---")
st.subheader(t("📚 习惯统计", "📚 Habit Summary"))
habit_df = pd.DataFrame(
    {"Habit": [t(task["label_zh"], task["label_en"]) for task in EARNING_TASKS], "Count": list(task_counter.values())}
)
col1, col2 = st.columns(2)
with col1:
    st.dataframe(habit_df, use_container_width=True, hide_index=True)
with col2:
    st.bar_chart(habit_df.set_index("Habit"))

st.markdown("---")
st.subheader(t("🗂️ 每日记录", "🗂️ Daily Records"))
if daily_df.empty:
    st.info(t("本周还没有每日记录。", "No daily records yet for this week."))
else:
    st.dataframe(daily_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader(t("🧸 兑换记录", "🧸 Redemption History"))
if redeem_df.empty:
    st.info(t("本周还没有兑换记录。", "No reward redemption this week yet."))
else:
    st.dataframe(redeem_df, use_container_width=True, hide_index=True)
