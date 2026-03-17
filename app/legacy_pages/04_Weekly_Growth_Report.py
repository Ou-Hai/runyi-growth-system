import pandas as pd
import streamlit as st

from data_manager import get_current_week_daily_logs, get_current_week_start, load_points
from rules import CHILD_NAME_EN, CHILD_NAME_ZH, EARNING_TASKS, WEEKLY_START_POINTS
from ui import init_sidebar, inject_styles, render_hero, t

st.set_page_config(page_title="Weekly Growth Report", page_icon="📝", layout="wide")


def get_level_info(points: int) -> dict:
    if points >= 38:
        return {"level": 4, "title_zh": "大师", "title_en": "Master", "current_min": 38, "next_level_points": None}
    if points >= 24:
        return {"level": 3, "title_zh": "冠军", "title_en": "Champion", "current_min": 24, "next_level_points": 38}
    if points >= 12:
        return {"level": 2, "title_zh": "探索者", "title_en": "Explorer", "current_min": 12, "next_level_points": 24}
    return {"level": 1, "title_zh": "萌芽者", "title_en": "Budding Star", "current_min": 0, "next_level_points": 12}


def get_week_status(net_growth: int) -> str:
    if net_growth >= 8:
        return t("优秀的一周", "Excellent Week")
    if net_growth >= 4:
        return t("进步明显", "Good Progress")
    if net_growth >= 1:
        return t("积极开始", "Positive Start")
    return t("继续加油", "Keep Trying")


def get_progress_data(current_points: int, level_info: dict) -> tuple[int, float]:
    if level_info["next_level_points"] is None:
        return 0, 1.0

    points_needed = max(level_info["next_level_points"] - current_points, 0)
    if level_info["current_min"] == 0:
        effective_floor = WEEKLY_START_POINTS
        effective_current = max(current_points - effective_floor, 0)
        effective_range = max(level_info["next_level_points"] - effective_floor, 1)
        progress_value = max(0.0, min(effective_current / effective_range, 1.0))
        return points_needed, progress_value

    level_range = level_info["next_level_points"] - level_info["current_min"]
    progress_value = max(0.0, min((current_points - level_info["current_min"]) / level_range, 1.0))
    return points_needed, progress_value


init_sidebar()
inject_styles()

current_points = load_points()
logs = get_current_week_daily_logs()
level_info = get_level_info(current_points)

render_hero(
    t("📝 周成长报告", "📝 Weekly Growth Report"),
    t(
        f"用一页看清 {CHILD_NAME_ZH} 这周的习惯节奏、积分变化和成长状态。",
        f"See {CHILD_NAME_EN}'s weekly rhythm, point changes, and growth story in one page.",
    ),
    [
        t("等级成长", "Level growth"),
        t("习惯高光", "Habit highlights"),
        t("每周故事", "Weekly story"),
    ],
)

col1, col2 = st.columns(2)
col1.metric(t("当前可用积分", "Current Points"), current_points)
col2.metric(t("本周开始日期", "Week Start"), get_current_week_start())

st.markdown("---")
st.subheader(t("⭐ 成长等级", "⭐ Growth Level"))

col1, col2 = st.columns(2)
col1.metric(t("当前等级", "Current Level"), f"Level {level_info['level']}")
col2.metric(t("等级称号", "Level Title"), t(level_info["title_zh"], level_info["title_en"]))

points_needed, progress_value = get_progress_data(current_points, level_info)
if level_info["next_level_points"] is not None:
    st.write(f"{t('距离下一等级还差', 'Points needed for next level')}: **{points_needed}**")
    st.progress(progress_value)
    if level_info["current_min"] == 0:
        st.caption(
            t(
                "第一档进度条不把每周起始赠送的 2 分算进进度，所以初始状态不会自带进度。",
                "The first progress bar excludes the weekly gifted 2 points, so the initial state starts at zero.",
            )
        )
else:
    st.success(t("已经达到最高等级。", "Highest level reached."))
    st.progress(1.0)

if not logs:
    st.info(t("本周还没有记录，请先去任务中心打卡。", "No records this week yet. Please add records in Task Center first."))
    st.stop()

df = pd.DataFrame(logs)
df["earned_points"] = pd.to_numeric(df["earned_points"])
df["deduction_points"] = pd.to_numeric(df["deduction_points"])
df["net_change"] = pd.to_numeric(df["net_change"])

total_days = len(df)
total_earned = int(df["earned_points"].sum())
total_deducted = int(df["deduction_points"].sum())
net_growth = int(df["net_change"].sum())
week_status = get_week_status(net_growth)

task_counter = {task["label_en"]: 0 for task in EARNING_TASKS}
for task_str in df["earned_tasks"].fillna(""):
    for item in [part.strip() for part in str(task_str).split("|") if part.strip()]:
        if item in task_counter:
            task_counter[item] += 1

top_task_en = max(task_counter, key=task_counter.get)
task_name_map = {task["label_en"]: t(task["label_zh"], task["label_en"]) for task in EARNING_TASKS}
top_task = task_name_map[top_task_en]
top_task_count = task_counter[top_task_en]

st.markdown("---")
col1, col2 = st.columns([0.95, 1.05])

with col1:
    st.markdown(
        f"""
        <div class="soft-card">
            <h3>{t('本周摘要', 'Weekly Snapshot')}</h3>
            <p>{t('记录天数', 'Recorded Days')}: <b>{total_days}</b></p>
            <p>{t('总加分', 'Total Earned')}: <b>{total_earned}</b></p>
            <p>{t('总扣分', 'Total Deducted')}: <b>{total_deducted}</b></p>
            <p>{t('净增长', 'Net Growth')}: <b>{net_growth}</b></p>
            <p>{t('本周状态', 'Week Status')}: <b>{week_status}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="soft-card">
            <h3>{t(f'{CHILD_NAME_ZH}本周成长故事', f"{CHILD_NAME_EN}'s Weekly Story")}</h3>
            <p>{t(
                f"{CHILD_NAME_ZH} 这一周记录了 {total_days} 天，净增长 {net_growth} 分，最稳定的习惯是 {top_task}，一共完成了 {top_task_count} 次。",
                f"{CHILD_NAME_EN} logged {total_days} day(s) this week, gained {net_growth} net points, and the strongest habit was {top_task} with {top_task_count} completions."
            )}</p>
            <p>{t(
                f"继续保持，温柔稳定地积累，就是最好的成长节奏。",
                f"Keep going. Calm, steady accumulation is the best kind of growth."
            )}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
st.subheader(t("📊 每日净变化", "📊 Daily Net Change"))
st.bar_chart(df[["date", "net_change"]].copy().set_index("date"))
