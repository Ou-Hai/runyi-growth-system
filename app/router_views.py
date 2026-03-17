from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    from .data_manager import (
        DAILY_FIELDS,
        REDEEM_FIELDS,
        append_redeem_log,
        get_current_week_daily_logs,
        get_current_week_redeem_logs,
        get_current_week_start,
        get_week_start,
        load_points,
        recalculate_points,
        undo_last_action,
        upsert_daily_log,
    )
    from .rules import (
        CHILD_NAME_EN,
        CHILD_NAME_ZH,
        DEDUCTION_TASKS,
        EARNING_TASKS,
        MAX_DAILY_DEDUCT,
        MAX_DAILY_EARN,
        REWARD_TIERS,
        WEEKLY_START_POINTS,
    )
    from .ui import render_hero, t
except ImportError:
    from data_manager import (
        DAILY_FIELDS,
        REDEEM_FIELDS,
        append_redeem_log,
        get_current_week_daily_logs,
        get_current_week_redeem_logs,
        get_current_week_start,
        get_week_start,
        load_points,
        recalculate_points,
        undo_last_action,
        upsert_daily_log,
    )
    from rules import (
        CHILD_NAME_EN,
        CHILD_NAME_ZH,
        DEDUCTION_TASKS,
        EARNING_TASKS,
        MAX_DAILY_DEDUCT,
        MAX_DAILY_EARN,
        REWARD_TIERS,
        WEEKLY_START_POINTS,
    )
    from ui import render_hero, t

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DAILY_LOG_FILE = DATA_DIR / "daily_log.csv"
REDEEM_LOG_FILE = DATA_DIR / "redeem_log.csv"


def render_task_center() -> None:
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
                t(task["label_zh"], task["label_en"]),
                help=t(task["detail_zh"], task["detail_en"]),
                key=f"earn_{task['id']}",
            )
            if checked:
                selected_earnings.append(t(task["label_zh"], task["label_en"]))

        st.subheader(t("⚠️ 今日提醒项", "⚠️ Today's Reminder Items"))
        selected_deductions = []
        for task in DEDUCTION_TASKS:
            checked = st.checkbox(
                t(task["label_zh"], task["label_en"]),
                key=f"deduct_{task['id']}",
            )
            if checked:
                selected_deductions.append(t(task["label_zh"], task["label_en"]))

    with right:
        earning_points = min(len(selected_earnings), MAX_DAILY_EARN)
        deduction_points = min(len(selected_deductions), MAX_DAILY_DEDUCT)
        net_change = earning_points - deduction_points
        completion_ratio = min((earning_points + deduction_points) / (MAX_DAILY_EARN + MAX_DAILY_DEDUCT), 1.0)

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
                <h3>{t("今日完成感", "Today's Completion Feeling")}</h3>
                <p style="font-size:2rem;font-weight:700;margin:6px 0 10px 0;">{net_change:+}</p>
                <p>{mood}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(completion_ratio)
        st.caption(t("这是今天填写完成度的小动画进度。", "This is the little completion progress for today's check-in."))

        next_reward = next((reward for reward in REWARD_TIERS if current_points < reward["points"]), None)
        reward_feedback = (
            t(
                f"再努力 {next_reward['points'] - current_points} 分，就能点亮 {next_reward['name_zh']}。",
                f"{next_reward['points'] - current_points} more points to light up {next_reward['name_en']}.",
            )
            if next_reward
            else t("已经达到最高奖励档位啦。", "The highest reward tier is already unlocked.")
        )

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
            if net_change > 0:
                st.balloons()
                st.toast(t("太棒了，今天的努力记下来了。", "Nice work. Today's effort has been saved."))
            st.success(f"{t('记录已保存，当前积分', 'Record saved. Current points')}: {load_points()}")
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


def render_weekly_summary() -> None:
    current_points = load_points()
    current_week_start = get_current_week_start()
    logs = get_current_week_daily_logs()
    redeem_logs = get_current_week_redeem_logs()

    render_hero(
        t("📈 每周总结", "📈 Weekly Summary"),
        t("快速回看本周的打卡和兑换记录。", "A quick review of this week's records and redemptions."),
        [t("本周视角", "This week"), t("数据汇总", "Summaries"), t("兑换历史", "Redemptions")],
    )

    col1, col2 = st.columns(2)
    col1.metric(t("当前可用积分", "Current Points"), current_points)
    col2.metric(t("本周开始日期", "Week Start"), current_week_start)

    st.markdown("---")
    st.subheader(t("🗓️ 本周每日记录", "🗓️ Daily Records This Week"))
    if not logs:
        st.info(t("本周还没有每日记录。", "No daily records for this week yet."))
    else:
        df = pd.DataFrame(logs)
        df["earned_points"] = pd.to_numeric(df["earned_points"])
        df["deduction_points"] = pd.to_numeric(df["deduction_points"])
        df["net_change"] = pd.to_numeric(df["net_change"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.line_chart(df[["date", "net_change"]].copy().set_index("date"))

    st.markdown("---")
    st.subheader(t("🧸 本周兑换记录", "🧸 Reward Redemption This Week"))
    if not redeem_logs:
        st.info(t("本周还没有兑换记录。", "No reward redemption this week yet."))
    else:
        redeem_df = pd.DataFrame(redeem_logs)
        redeem_df["points_cost"] = pd.to_numeric(redeem_df["points_cost"])
        redeem_df["points_after_redeem"] = pd.to_numeric(redeem_df["points_after_redeem"])
        st.dataframe(redeem_df, use_container_width=True, hide_index=True)


def render_reward_shop() -> None:
    current_points = load_points()
    can_redeem_today = datetime.today().weekday() == 6

    render_hero(
        t("🧸 奖励商店", "🧸 Reward Shop"),
        t("在周日晚上用积分换喜欢的小玩具。", "Redeem favorite little rewards with points on Sunday."),
        [t("周日兑换", "Sunday only"), t("积分累积", "Carry-over points"), t("奖励分档", "Reward tiers")],
    )

    st.metric(t("当前可用积分", "Current Points"), current_points)
    if can_redeem_today:
        st.success(t("今天是周日，可以兑换奖励。", "Today is Sunday. Reward redemption is available."))
    else:
        st.warning(t("今天不是周日，奖励仅可在周日兑换。", "Today is not Sunday. Rewards can only be redeemed on Sunday."))

    st.markdown("---")
    for reward in REWARD_TIERS:
        st.markdown(
            f"""
            <div class="soft-card">
                <h3>{t(reward['name_zh'], reward['name_en'])}</h3>
                <p>{reward['points']} {t('分', 'points')}</p>
                <p>{t(reward['desc_zh'], reward['desc_en'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        can_afford = current_points >= reward["points"]
        can_redeem = can_redeem_today and can_afford
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button(t("立即兑换", "Redeem Now"), key=f"redeem_{reward['id']}", disabled=not can_redeem, use_container_width=True):
                new_points = current_points - reward["points"]
                append_redeem_log(
                    reward_name=t(reward["name_zh"], reward["name_en"]),
                    points_cost=reward["points"],
                    points_after_redeem=new_points,
                )
                st.success(f"{t('兑换成功，剩余积分', 'Redeemed successfully. Remaining points')}: {new_points}")
                st.rerun()
        with col2:
            if not can_afford:
                st.info(t("积分不足。", "Not enough points yet."))
            elif not can_redeem_today:
                st.info(t("请在周日再来兑换。", "Please come back on Sunday to redeem."))
            else:
                st.info(t("已经满足兑换条件。", "Ready to redeem."))
        st.markdown("---")


def render_growth_report() -> None:
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
            return points_needed, max(0.0, min(effective_current / effective_range, 1.0))
        level_range = level_info["next_level_points"] - level_info["current_min"]
        return points_needed, max(0.0, min((current_points - level_info["current_min"]) / level_range, 1.0))

    current_points = load_points()
    logs = get_current_week_daily_logs()
    level_info = get_level_info(current_points)

    render_hero(
        t("📝 周成长报告", "📝 Weekly Growth Report"),
        t(
            f"用一页看清 {CHILD_NAME_ZH} 这周的习惯节奏、积分变化和成长状态。",
            f"See {CHILD_NAME_EN}'s weekly rhythm, point changes, and growth story in one page.",
        ),
        [t("等级成长", "Level growth"), t("习惯高光", "Habit highlights"), t("每周故事", "Weekly story")],
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
    else:
        st.success(t("已经达到最高等级。", "Highest level reached."))
        st.progress(1.0)

    if not logs:
        st.info(t("本周还没有记录，请先去任务中心打卡。", "No records this week yet. Please add records in Task Center first."))
        return

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
    top_task = next(ti for ti in [t(task["label_zh"], task["label_en"]) for task in EARNING_TASKS if task["label_en"] == top_task_en])
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
                <p>{t('继续保持，温柔稳定地积累，就是最好的成长节奏。', 'Keep going. Calm, steady accumulation is the best kind of growth.')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("---")
    st.subheader(t("📊 每日净变化", "📊 Daily Net Change"))
    st.bar_chart(df[["date", "net_change"]].copy().set_index("date"))


def render_parent_dashboard() -> None:
    current_points = load_points()
    daily_logs = get_current_week_daily_logs()
    redeem_logs = get_current_week_redeem_logs()

    render_hero(
        t("👨‍👩‍👦 家长面板", "👨‍👩‍👦 Parent Dashboard"),
        t("从家长视角快速查看本周表现。", "A parent-friendly view of the current week's performance."),
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
    habit_df = pd.DataFrame({"Habit": [t(task["label_zh"], task["label_en"]) for task in EARNING_TASKS], "Count": list(task_counter.values())})
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


def _load_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    df = pd.read_csv(path)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[columns]


def render_edit_records() -> None:
    render_hero(
        t("✏️ 编辑记录", "✏️ Edit Records"),
        t("修正历史记录后，积分会自动从日志重新计算。", "After correcting a record, points are recalculated directly from logs."),
        [t("每日记录", "Daily logs"), t("兑换记录", "Redeem logs"), t("自动重算", "Auto recalculation")],
    )

    daily_df = _load_csv(DAILY_LOG_FILE, DAILY_FIELDS)
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
            new_date = st.text_input(t("日期", "Date"), value="" if pd.isna(row["date"]) else str(row["date"]))
            new_earned_tasks = st.text_area(t("加分任务", "Earned Tasks"), value="" if pd.isna(row["earned_tasks"]) else str(row["earned_tasks"]))
            new_deduction_tasks = st.text_area(t("扣分任务", "Deduction Tasks"), value="" if pd.isna(row["deduction_tasks"]) else str(row["deduction_tasks"]))
            new_earned_points = st.number_input(t("加分", "Earned Points"), step=1, value=int(row["earned_points"]) if not pd.isna(row["earned_points"]) else 0)
            new_deduction_points = st.number_input(t("扣分", "Deduction Points"), step=1, value=int(row["deduction_points"]) if not pd.isna(row["deduction_points"]) else 0)
            save_daily = st.form_submit_button(t("保存每日记录", "Save Daily Log"))

        if save_daily:
            daily_df.at[row_idx, "date"] = new_date.strip()
            daily_df.at[row_idx, "week_start_date"] = get_week_start(new_date.strip())
            daily_df.at[row_idx, "earned_tasks"] = new_earned_tasks.strip()
            daily_df.at[row_idx, "deduction_tasks"] = new_deduction_tasks.strip()
            daily_df.at[row_idx, "earned_points"] = int(new_earned_points)
            daily_df.at[row_idx, "deduction_points"] = int(new_deduction_points)
            daily_df.at[row_idx, "net_change"] = int(new_earned_points) - int(new_deduction_points)
            daily_df.sort_values(by="timestamp").to_csv(DAILY_LOG_FILE, index=False)
            recalculate_points()
            st.success(t("每日记录已更新。", "Daily log updated successfully."))
            st.rerun()

    st.markdown("---")
    redeem_df = _load_csv(REDEEM_LOG_FILE, REDEEM_FIELDS)
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
            new_redeem_date = st.text_input(t("兑换日期", "Redeem Date"), value="" if pd.isna(redeem_row["date"]) else str(redeem_row["date"]))
            new_reward_name = st.text_input(t("奖励名称", "Reward Name"), value="" if pd.isna(redeem_row["reward_name"]) else str(redeem_row["reward_name"]))
            new_points_cost = st.number_input(t("消耗积分", "Points Cost"), step=1, value=int(redeem_row["points_cost"]) if not pd.isna(redeem_row["points_cost"]) else 0)
            new_points_after_redeem = st.number_input(t("兑换后积分", "Points After Redeem"), step=1, value=int(redeem_row["points_after_redeem"]) if not pd.isna(redeem_row["points_after_redeem"]) else 0)
            save_redeem = st.form_submit_button(t("保存兑换记录", "Save Redeem Log"))

        if save_redeem:
            redeem_df.at[redeem_row_idx, "date"] = new_redeem_date.strip()
            redeem_df.at[redeem_row_idx, "week_start_date"] = get_week_start(new_redeem_date.strip())
            redeem_df.at[redeem_row_idx, "reward_name"] = new_reward_name.strip()
            redeem_df.at[redeem_row_idx, "points_cost"] = int(new_points_cost)
            redeem_df.at[redeem_row_idx, "points_after_redeem"] = int(new_points_after_redeem)
            redeem_df.sort_values(by="timestamp").to_csv(REDEEM_LOG_FILE, index=False)
            recalculate_points()
            st.success(t("兑换记录已更新。", "Redeem log updated successfully."))
            st.rerun()
