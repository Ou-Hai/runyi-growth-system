import streamlit as st
import pandas as pd

from app.data_manager import load_points, load_daily_logs

st.set_page_config(page_title="Weekly Growth Report", page_icon="📝", layout="wide")

def get_level_info(points):
    if points >= 38:
        return {
            "level": 4,
            "title": "👑 Master",
            "current_min": 38,
            "next_level_points": None,
        }
    elif points >= 24:
        return {
            "level": 3,
            "title": "🏆 Champion",
            "current_min": 24,
            "next_level_points": 38,
        }
    elif points >= 12:
        return {
            "level": 2,
            "title": "🚀 Explorer",
            "current_min": 12,
            "next_level_points": 24,
        }
    else:
        return {
            "level": 1,
            "title": "🌱 Beginner",
            "current_min": 0,
            "next_level_points": 12,
        }


def get_level_message(level_title):
    if "Master" in level_title:
        return "Runyi has reached the highest level. Amazing job!"
    if "Champion" in level_title:
        return "Runyi is doing a great job and is getting close to the top."
    if "Explorer" in level_title:
        return "Runyi is growing steadily and exploring good habits every day."
    return "Every small step matters. Runyi is building a strong foundation."

def get_week_status(net_growth):
    if net_growth >= 8:
        return "⭐ Excellent Week"
    elif net_growth >= 4:
        return "👍 Good Progress"
    elif net_growth >= 1:
        return "🌱 Positive Start"
    else:
        return "💪 Keep Trying"

st.title("📝 Weekly Growth Report")
st.balloons()
st.caption("A simple weekly story about Runyi's growth")

current_points = load_points()
logs = load_daily_logs()

level_info = get_level_info(current_points)
level_message = get_level_message(level_info["title"])

st.metric("Current Weekly Points", current_points)

st.markdown("---")
st.subheader("⭐ Runyi Level System")

col1, col2 = st.columns(2)
col1.metric("Current Level", f"Level {level_info['level']}")
col2.metric("Level Title", level_info["title"])

if level_info["next_level_points"] is not None:
    points_needed = level_info["next_level_points"] - current_points
    level_range = level_info["next_level_points"] - level_info["current_min"]
    progress_value = (current_points - level_info["current_min"]) / level_range
    progress_value = max(0.0, min(progress_value, 1.0))

    st.write(f"**{points_needed} more point(s)** needed to reach the next level.")
    st.progress(progress_value)
else:
    st.success("Runyi has reached the highest level!")
    st.progress(1.0)

st.info(level_message)

if not logs:
    st.info("No weekly records yet. Please add daily records in Task Center first.")
    st.stop()

df = pd.DataFrame(logs)

# convert numeric columns
df["earned_points"] = pd.to_numeric(df["earned_points"])
df["deduction_points"] = pd.to_numeric(df["deduction_points"])
df["net_change"] = pd.to_numeric(df["net_change"])

# basic stats
total_days = len(df)
total_earned = int(df["earned_points"].sum())
total_deducted = int(df["deduction_points"].sum())
net_growth = int(df["net_change"].sum())

week_status = get_week_status(net_growth)

task_counter = {
    "Learning": 0,
    "Self-management": 0,
    "Daily Habit": 0,
}

for task_str in df["earned_tasks"].fillna(""):
    items = [item.strip() for item in str(task_str).split("|") if item.strip()]
    for item in items:
        if item in task_counter:
            task_counter[item] += 1

top_task = max(task_counter, key=task_counter.get)
top_task_count = task_counter[top_task]

st.markdown(
    f"""
<div style="
padding:20px;
border-radius:12px;
background-color:#f6f9ff;
border:1px solid #dde6ff;
">

<h2>👦 Runyi</h2>

<h3>{level_info['title']} — Level {level_info['level']}</h3>

<p><b>Current Points:</b> {current_points}</p>

<p><b>Weekly Net Growth:</b> {net_growth}</p>

<p><b>Weekly Performance:</b> {week_status}</p>

<p><b>Top Habit:</b> {top_task}</p>

<p>Keep going Runyi! Every small habit builds a stronger future 🚀</p>

</div>
""",
unsafe_allow_html=True
)

st.markdown("---")
st.subheader("Weekly Key Stats")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Recorded Days", total_days)
col2.metric("Total Earned", total_earned)
col3.metric("Total Deducted", total_deducted)
col4.metric("Net Growth", net_growth)

# analyze task frequency
task_counter = {
    "Learning": 0,
    "Self-management": 0,
    "Daily Habit": 0,
}

for task_str in df["earned_tasks"].fillna(""):
    items = [item.strip() for item in str(task_str).split("|") if item.strip()]
    for item in items:
        if item in task_counter:
            task_counter[item] += 1

top_task = max(task_counter, key=task_counter.get)
top_task_count = task_counter[top_task]

st.markdown("---")
st.subheader("Habit Highlights")

col1, col2 = st.columns(2)
col1.metric("Top Habit", top_task)
col2.metric("Top Habit Count", top_task_count)

# report text
if net_growth >= 8:
    growth_comment = "Runyi had an excellent growth week and showed strong consistency."
elif net_growth >= 4:
    growth_comment = "Runyi had a good growth week with steady progress."
elif net_growth >= 1:
    growth_comment = "Runyi made positive progress this week."
elif net_growth == 0:
    growth_comment = "Runyi stayed stable this week and can aim even higher next week."
else:
    growth_comment = "This week had some challenges, but next week is a new chance to improve."

report_text = f"""
### 🌱 Runyi's Growth Story This Week

Runyi stayed engaged in her growth journey for **{total_days} day(s)** this week.

She gained **{total_earned} points** and lost **{total_deducted} points**,
resulting in a **net growth of {net_growth} points**.

Her strongest habit this week was **{top_task}**,
which she completed **{top_task_count} time(s)**.

Runyi is currently at **Level {level_info['level']} — {level_info['title']}**.

{growth_comment}

Keep going, Runyi! Every small habit builds a stronger future. 🚀
"""

st.markdown("---")
st.subheader("Auto-generated Weekly Report")
st.markdown(report_text)

st.markdown("---")
st.subheader("Daily Net Growth Trend")

chart_df = df[["date", "net_change"]].copy()
chart_df = chart_df.set_index("date")
st.bar_chart(chart_df)