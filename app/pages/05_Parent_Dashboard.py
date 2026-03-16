import pandas as pd
import streamlit as st
from data_manager import load_points, load_daily_logs, load_redeem_logs, reset_week

st.set_page_config(page_title="Parent Dashboard", page_icon="👨‍👩‍👦", layout="wide")

st.title("👨‍👩‍👦 Parent Dashboard")
st.caption("A clear overview for parents to track Runyi's weekly progress")

st.markdown("---")
st.subheader("Weekly Management")

col1, col2 = st.columns([1,3])

with col1:
    if st.button("🔄 Reset New Week"):
        reset_week()
        st.success("New week started. Points reset to 2.")
        st.rerun()

with col2:
    st.caption("Use this at the beginning of a new week.")

current_points = load_points()
daily_logs = load_daily_logs()
redeem_logs = load_redeem_logs()

if daily_logs:
    daily_df = pd.DataFrame(daily_logs)
    daily_df["earned_points"] = pd.to_numeric(daily_df["earned_points"])
    daily_df["deduction_points"] = pd.to_numeric(daily_df["deduction_points"])
    daily_df["net_change"] = pd.to_numeric(daily_df["net_change"])
else:
    daily_df = pd.DataFrame(
        columns=["date", "earned_tasks", "deduction_tasks", "earned_points", "deduction_points", "net_change"]
    )

if redeem_logs:
    redeem_df = pd.DataFrame(redeem_logs)
    redeem_df["points_cost"] = pd.to_numeric(redeem_df["points_cost"])
    redeem_df["points_after_redeem"] = pd.to_numeric(redeem_df["points_after_redeem"])
else:
    redeem_df = pd.DataFrame(
        columns=["date", "reward_name", "points_cost", "points_after_redeem"]
    )

# -------------------------
# Core metrics
# -------------------------
total_days = len(daily_df)
weekly_net_growth = int(daily_df["net_change"].sum()) if not daily_df.empty else 0
total_rewards_redeemed = len(redeem_df)

task_counter = {
    "Learning": 0,
    "Self-management": 0,
    "Daily Habit": 0,
}

if not daily_df.empty:
    for task_str in daily_df["earned_tasks"].fillna(""):
        items = [item.strip() for item in str(task_str).split("|") if item.strip()]
        for item in items:
            if item in task_counter:
                task_counter[item] += 1

top_habit = max(task_counter, key=task_counter.get)
top_habit_count = task_counter[top_habit]

# -------------------------
# KPI area
# -------------------------
st.markdown("---")
st.subheader("Weekly Snapshot")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Current Points", current_points)
col2.metric("Weekly Net Growth", weekly_net_growth)
col3.metric("Recorded Days", total_days)
col4.metric("Rewards Redeemed", total_rewards_redeemed)
col5.metric("Top Habit", top_habit)

# -------------------------
# Habit summary
# -------------------------
st.markdown("---")
st.subheader("Habit Summary")

habit_df = pd.DataFrame(
    {
        "Habit": list(task_counter.keys()),
        "Count": list(task_counter.values()),
    }
)

col1, col2 = st.columns(2)

with col1:
    st.dataframe(habit_df, use_container_width=True, hide_index=True)

with col2:
    chart_df = habit_df.set_index("Habit")
    st.bar_chart(chart_df)

st.caption(f"Most frequent habit: {top_habit} ({top_habit_count} time(s))")

# -------------------------
# Daily trend
# -------------------------
st.markdown("---")
st.subheader("Daily Net Change Trend")

if daily_df.empty:
    st.info("No daily records yet.")
else:
    trend_df = daily_df[["date", "net_change"]].copy().set_index("date")
    st.line_chart(trend_df)

# -------------------------
# Daily record table
# -------------------------
st.markdown("---")
st.subheader("Daily Records")

if daily_df.empty:
    st.info("No daily records yet.")
else:
    st.dataframe(daily_df, use_container_width=True, hide_index=True)

# -------------------------
# Redemption history
# -------------------------
st.markdown("---")
st.subheader("Reward Redemption History")

if redeem_df.empty:
    st.info("No rewards redeemed yet.")
else:
    st.dataframe(redeem_df, use_container_width=True, hide_index=True)