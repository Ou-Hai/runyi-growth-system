import streamlit as st

from data_manager import get_current_week_start, load_points, undo_last_action, upsert_daily_log
from rules import (
    CHILD_NAME_EN,
    CHILD_NAME_ZH,
    DEDUCTION_TASKS,
    EARNING_TASKS,
    MAX_DAILY_DEDUCT,
    MAX_DAILY_EARN,
    REWARD_TIERS,
)
from ui import init_sidebar, inject_styles, render_hero, t

st.set_page_config(page_title="Task Center", page_icon="✅", layout="wide")

init_sidebar()
inject_styles()

current_points = load_points()

render_hero(
    t("✅ 今日任务中心", "✅ Task Center"),
    t(
        f"像完成小冒险一样，帮 {CHILD_NAME_ZH} 记录今天的闪光点。",
        f"Track today's bright moments for {CHILD_NAME_EN} like a tiny adventure.",
    ),
    [
        t("完成感反馈", "Completion feedback"),
        t("今日小冒险", "Today's mini quest"),
        t("奖励会发光", "Rewards glow brighter"),
    ],
)

col1, col2, col3 = st.columns(3)
col1.metric(t("当前可用积分", "Current Points"), current_points)
col2.metric(t("本周开始日期", "Week Start"), get_current_week_start())
col3.metric(t("今日目标上限", "Today's Max"), f"+{MAX_DAILY_EARN} / -{MAX_DAILY_DEDUCT}")

st.markdown("---")
left, right = st.columns([1.1, 0.9])

with left:
    st.subheader(t("🟢 今日得分任务", "🟢 Today's Earning Tasks"))

    selected_earnings = []
    for task in EARNING_TASKS:
        checked = st.checkbox(
            f"{t(task['label_zh'], task['label_en'])}",
            help=t(task["detail_zh"], task["detail_en"]),
            key=f"earn_{task['id']}",
        )
        if checked:
            selected_earnings.append(t(task["label_zh"], task["label_en"]))

    st.subheader(t("⚠️ 今日提醒项", "⚠️ Today's Reminder Items"))
    selected_deductions = []
    for task in DEDUCTION_TASKS:
        checked = st.checkbox(
            f"{t(task['label_zh'], task['label_en'])}",
            key=f"deduct_{task['id']}",
        )
        if checked:
            selected_deductions.append(t(task["label_zh"], task["label_en"]))

with right:
    earning_points = min(len(selected_earnings), MAX_DAILY_EARN)
    deduction_points = min(len(selected_deductions), MAX_DAILY_DEDUCT)
    net_change = earning_points - deduction_points
    completion_ratio = min((earning_points + deduction_points) / (MAX_DAILY_EARN + MAX_DAILY_DEDUCT), 1.0)
    completion_title = t("今日完成感", "Today's Completion Feeling")

    mood = (
        t("今天状态超棒，像小太阳一样。", "Today feels bright, like a little sun.")
        if net_change >= 2
        else t("今天有进步，继续稳稳前进。", "Nice progress today. Keep going steadily.")
        if net_change >= 0
        else t("今天有一点挑战，明天再来。", "A few bumps today. Tomorrow is another try.")
    )

    st.markdown(
        f"""
        <div class="celebration-card">
            <h3>{completion_title}</h3>
            <p style="font-size:2rem;font-weight:700;margin:6px 0 10px 0;">{net_change:+}</p>
            <p>{mood}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(completion_ratio)
    st.caption(t("这是今天填写完成度的小动画进度。", "This is the little completion progress for today's check-in."))

    next_reward = next((reward for reward in REWARD_TIERS if current_points < reward["points"]), None)
    if next_reward:
        reward_feedback = t(
            f"再努力 {next_reward['points'] - current_points} 分，就能点亮 {next_reward['name_zh']}。",
            f"{next_reward['points'] - current_points} more points to light up {next_reward['name_en']}.",
        )
    else:
        reward_feedback = t("已经达到最高奖励档位啦。", "The highest reward tier is already unlocked.")

    st.markdown(
        f"""
        <div class="soft-card">
            <h3>{t('奖励雷达', 'Reward Radar')}</h3>
            <p>{reward_feedback}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(t("保存今天记录", "Save Today's Record"), use_container_width=True):
        upsert_daily_log(
            earned_tasks=selected_earnings,
            deduction_tasks=selected_deductions,
            earned_points=earning_points,
            deduction_points=deduction_points,
            net_change=net_change,
        )
        updated_points = load_points()
        if net_change > 0:
            st.balloons()
            st.toast(t("太棒了，今天的努力记下来了。", "Nice work. Today's effort has been saved."))
        st.success(
            f"{t('记录已保存，当前积分', 'Record saved. Current points')}: {updated_points}"
        )
        st.rerun()

    if st.button(t("撤销上一次操作", "Undo Last Action"), use_container_width=True):
        st.success(undo_last_action())
        st.rerun()

st.markdown("---")
st.subheader(t("🌈 奖励预览", "🌈 Reward Preview"))

reward_cols = st.columns(len(REWARD_TIERS))
for col, reward in zip(reward_cols, REWARD_TIERS):
    with col:
        unlocked = current_points >= reward["points"]
        state = t("已点亮", "Unlocked") if unlocked else t("还差", "Need")
        remain = 0 if unlocked else reward["points"] - current_points
        st.markdown(
            f"""
            <div class="play-card">
                <div style="font-size:1.8rem;margin-bottom:8px;">{"✨" if unlocked else "⭐"}</div>
                <h3>{t(reward['name_zh'], reward['name_en'])}</h3>
                <p>{reward['points']} {t('分', 'points')}</p>
                <p>{t(reward['desc_zh'], reward['desc_en'])}</p>
                <p style="margin-top:10px;font-weight:700;">{state} {remain if remain else ""}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
