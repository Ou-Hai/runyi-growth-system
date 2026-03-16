import streamlit as st
from data_manager import load_points, save_points, append_daily_log

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Task Center", page_icon="✅", layout="wide")

# -------------------------
# Constants based on the rule file
# -------------------------
WEEKLY_START_POINTS = 2
MAX_DAILY_EARN = 3
MAX_DAILY_DEDUCT = 2

EARNING_TASKS = {
    "Learning": 1,
    "Self-management": 1,
    "Daily Habit": 1,
}

DEDUCTION_TASKS = {
    "Lost stationery": -1,
    "Messy eating": -1,
    "Did not organize school bag after reminders": -1,
    "Delaying tasks": -1,
}

REWARD_TIERS = {
    12: "Toy reward",
    30: "Better toy reward",
    38: "Big reward",
}

# -------------------------
# Session state init
# -------------------------
if "weekly_points" not in st.session_state:
    st.session_state.weekly_points = load_points()

# -------------------------
# Title
# -------------------------
st.title("✅ Task Center")
st.caption("Track today's good habits and deductions")

# -------------------------
# Show current weekly points
# -------------------------
st.metric("Current Weekly Points", st.session_state.weekly_points)

st.markdown("---")

# -------------------------
# Daily earning section
# -------------------------
st.subheader("Earn Points Today")

selected_earnings = []
for task_name in EARNING_TASKS:
    checked = st.checkbox(f"{task_name} (+1)", key=f"earn_{task_name}")
    if checked:
        selected_earnings.append(task_name)

earning_points = min(len(selected_earnings), MAX_DAILY_EARN)

st.write(f"Earned today: **{earning_points}** / {MAX_DAILY_EARN}")

st.markdown("---")

# -------------------------
# Daily deduction section
# -------------------------
st.subheader("Deduct Points Today")

selected_deductions = []
for task_name in DEDUCTION_TASKS:
    checked = st.checkbox(f"{task_name} (-1)", key=f"deduct_{task_name}")
    if checked:
        selected_deductions.append(task_name)

deduction_points = min(len(selected_deductions), MAX_DAILY_DEDUCT)

st.write(f"Deducted today: **{deduction_points}** / {MAX_DAILY_DEDUCT}")

st.markdown("---")

# -------------------------
# Daily result
# -------------------------
net_change = earning_points - deduction_points
st.subheader("Today's Result")
st.write(f"Net change today: **{net_change:+}** points")

# -------------------------
# Apply button
# -------------------------
if st.button("Apply Today's Record"):
    st.session_state.weekly_points += net_change
    save_points(st.session_state.weekly_points)

    append_daily_log(
        earned_tasks=selected_earnings,
        deduction_tasks=selected_deductions,
        earned_points=earning_points,
        deduction_points=deduction_points,
        net_change=net_change,
    )

    st.success(
        f"Record saved. Weekly points updated to {st.session_state.weekly_points}."
    )

st.markdown("---")

# -------------------------
# Reward preview
# -------------------------
st.subheader("Reward Preview")

current_points = st.session_state.weekly_points
available_rewards = [pts for pts in REWARD_TIERS if current_points >= pts]

if available_rewards:
    best_reward = max(available_rewards)
    st.success(f"Current redeemable reward: {best_reward} points - {REWARD_TIERS[best_reward]}")
else:
    st.info("Not enough points for reward redemption yet.")

st.caption("Rewards can be redeemed on Sunday evening only.")