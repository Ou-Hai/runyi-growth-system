from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from auth import auth_configured, is_admin
from data_manager import (
    DAILY_FIELDS,
    REDEEM_FIELDS,
    append_redeem_log,
    get_current_week_daily_logs,
    get_current_week_redeem_logs,
    get_current_week_start,
    get_week_start,
    load_daily_logs,
    load_points,
    load_redeem_logs,
    recalculate_points,
    undo_last_action,
    update_daily_log_by_timestamp,
    update_redeem_log_by_timestamp,
    upsert_daily_log,
)
from rules import (
    CHILD_NAME_DE,
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

DAILY_COLUMN_LABELS = {
    "date": ("日期", "Date", "Datum"),
    "timestamp": ("时间戳", "Timestamp", "Zeitstempel"),
    "week_start_date": ("周开始日期", "Week Start Date", "Wochenstartdatum"),
    "earned_tasks": ("加分任务", "Earned Tasks", "Pluspunkte-Aufgaben"),
    "deduction_tasks": ("扣分任务", "Deduction Tasks", "Abzugsaufgaben"),
    "earned_points": ("加分", "Earned Points", "Pluspunkte"),
    "deduction_points": ("扣分", "Deduction Points", "Abzugspunkte"),
    "net_change": ("净变化", "Net Change", "Nettoveränderung"),
}

REDEEM_COLUMN_LABELS = {
    "date": ("日期", "Date", "Datum"),
    "timestamp": ("时间戳", "Timestamp", "Zeitstempel"),
    "week_start_date": ("周开始日期", "Week Start Date", "Wochenstartdatum"),
    "reward_name": ("奖励名称", "Reward Name", "Belohnungsname"),
    "points_cost": ("消耗积分", "Points Cost", "Eingelöste Punkte"),
    "points_after_redeem": ("兑换后积分", "Points After Redeem", "Punkte nach Einlösung"),
}


def _task_name_maps() -> tuple[dict[str, str], dict[str, str]]:
    earning_map: dict[str, str] = {}
    deduction_map: dict[str, str] = {}
    for task in EARNING_TASKS:
        translated = t(task["label_zh"], task["label_en"], task["label_de"])
        for key in (task["label_zh"], task["label_en"], task["label_de"]):
            earning_map[key] = translated
    for task in DEDUCTION_TASKS:
        translated = t(task["label_zh"], task["label_en"], task["label_de"])
        for key in (task["label_zh"], task["label_en"], task["label_de"]):
            deduction_map[key] = translated
    return earning_map, deduction_map


def _reward_name_map() -> dict[str, str]:
    reward_map: dict[str, str] = {}
    for reward in REWARD_TIERS:
        translated = t(reward["name_zh"], reward["name_en"], reward["name_de"])
        for key in (reward["name_zh"], reward["name_en"], reward["name_de"]):
            reward_map[key] = translated
    return reward_map


def _translate_joined_labels(value: object, mapping: dict[str, str]) -> str:
    if value is None or pd.isna(value):
        return ""
    parts = [part.strip() for part in str(value).split("|") if part.strip()]
    return " | ".join(mapping.get(part, part) for part in parts)


def _localize_daily_df(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()
    earning_map, deduction_map = _task_name_maps()
    if "earned_tasks" in display_df.columns:
        display_df["earned_tasks"] = display_df["earned_tasks"].apply(lambda value: _translate_joined_labels(value, earning_map))
    if "deduction_tasks" in display_df.columns:
        display_df["deduction_tasks"] = display_df["deduction_tasks"].apply(lambda value: _translate_joined_labels(value, deduction_map))
    return display_df.rename(columns={column: t(*labels) for column, labels in DAILY_COLUMN_LABELS.items() if column in display_df.columns})


def _localize_redeem_df(df: pd.DataFrame) -> pd.DataFrame:
    display_df = df.copy()
    reward_map = _reward_name_map()
    if "reward_name" in display_df.columns:
        display_df["reward_name"] = display_df["reward_name"].apply(lambda value: "" if value is None or pd.isna(value) else reward_map.get(str(value), str(value)))
    return display_df.rename(columns={column: t(*labels) for column, labels in REDEEM_COLUMN_LABELS.items() if column in display_df.columns})


def _month_label(month_value: str) -> str:
    return datetime.strptime(month_value, "%Y-%m").strftime("%Y-%m")


def _format_record_value(value: object) -> str:
    if value is None or pd.isna(value):
        return t("无", "None", "Keine")
    text = str(value).strip()
    if not text or text.upper() == "EMPTY":
        return t("无", "None", "Keine")
    return text


def _render_daily_log_cards(df: pd.DataFrame) -> None:
    localized = _localize_daily_df(df)
    date_label = t(*DAILY_COLUMN_LABELS["date"])
    net_label = t(*DAILY_COLUMN_LABELS["net_change"])
    for row in localized.to_dict("records"):
        st.markdown(
            f"""
            <div class="record-card">
                <div class="record-card-header">
                    <div class="record-card-title">{_format_record_value(row.get(date_label))}</div>
                    <div class="record-pill">{net_label}: {_format_record_value(row.get(net_label))}</div>
                </div>
                <div class="record-grid">
                    <div><div class="record-cell-label">{t(*DAILY_COLUMN_LABELS["earned_tasks"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*DAILY_COLUMN_LABELS["earned_tasks"])))}</div></div>
                    <div><div class="record-cell-label">{t(*DAILY_COLUMN_LABELS["deduction_tasks"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*DAILY_COLUMN_LABELS["deduction_tasks"])))}</div></div>
                    <div><div class="record-cell-label">{t(*DAILY_COLUMN_LABELS["earned_points"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*DAILY_COLUMN_LABELS["earned_points"])))}</div></div>
                    <div><div class="record-cell-label">{t(*DAILY_COLUMN_LABELS["deduction_points"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*DAILY_COLUMN_LABELS["deduction_points"])))}</div></div>
                    <div><div class="record-cell-label">{t(*DAILY_COLUMN_LABELS["week_start_date"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*DAILY_COLUMN_LABELS["week_start_date"])))}</div></div>
                    <div><div class="record-cell-label">{t(*DAILY_COLUMN_LABELS["timestamp"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*DAILY_COLUMN_LABELS["timestamp"])))}</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_redeem_log_cards(df: pd.DataFrame) -> None:
    localized = _localize_redeem_df(df)
    date_label = t(*REDEEM_COLUMN_LABELS["date"])
    reward_label = t(*REDEEM_COLUMN_LABELS["reward_name"])
    for row in localized.to_dict("records"):
        st.markdown(
            f"""
            <div class="record-card">
                <div class="record-card-header">
                    <div class="record-card-title">{_format_record_value(row.get(date_label))}</div>
                    <div class="record-pill">{_format_record_value(row.get(reward_label))}</div>
                </div>
                <div class="record-grid">
                    <div><div class="record-cell-label">{reward_label}</div><div class="record-cell-value">{_format_record_value(row.get(reward_label))}</div></div>
                    <div><div class="record-cell-label">{t(*REDEEM_COLUMN_LABELS["points_cost"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*REDEEM_COLUMN_LABELS["points_cost"])))}</div></div>
                    <div><div class="record-cell-label">{t(*REDEEM_COLUMN_LABELS["points_after_redeem"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*REDEEM_COLUMN_LABELS["points_after_redeem"])))}</div></div>
                    <div><div class="record-cell-label">{t(*REDEEM_COLUMN_LABELS["timestamp"])}</div><div class="record-cell-value">{_format_record_value(row.get(t(*REDEEM_COLUMN_LABELS["timestamp"])))}</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_readonly_notice() -> None:
    if auth_configured() and not is_admin():
        st.info(t("当前为只读模式。登录管理员后才可以修改积分、保存记录或兑换奖励。", "This session is read-only. Log in as admin to change points, save records, or redeem rewards.", "Diese Sitzung ist schreibgeschützt. Melde dich als Admin an, um Punkte zu ändern, Einträge zu speichern oder Belohnungen einzulösen."))


def _get_level_info(points: int) -> dict:
    if points >= 38:
        return {"level": 4, "title_zh": "大师", "title_en": "Master", "title_de": "Meister", "current_min": 38, "next_level_points": None}
    if points >= 24:
        return {"level": 3, "title_zh": "冠军", "title_en": "Champion", "title_de": "Champion", "current_min": 24, "next_level_points": 38}
    if points >= 12:
        return {"level": 2, "title_zh": "探索者", "title_en": "Explorer", "title_de": "Entdecker", "current_min": 12, "next_level_points": 24}
    return {"level": 1, "title_zh": "萌芽者", "title_en": "Budding Star", "title_de": "Kleiner Stern", "current_min": 0, "next_level_points": 12}


def _get_week_status(net_growth: int) -> str:
    if net_growth >= 8:
        return t("优秀的一周", "Excellent Week", "Eine starke Woche")
    if net_growth >= 4:
        return t("进步明显", "Good Progress", "Deutlicher Fortschritt")
    if net_growth >= 1:
        return t("积极开始", "Positive Start", "Positiver Start")
    return t("继续加油", "Keep Trying", "Weiter so")


def _get_progress_data(current_points: int, level_info: dict) -> tuple[int, float]:
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


def render_task_center() -> None:
    current_points = load_points()
    admin_mode = is_admin()

    render_hero(
        t("✅ 今日任务中心", "✅ Task Center", "✅ Aufgabenbereich"),
        t(
            f"像完成小冒险一样，帮 {CHILD_NAME_ZH} 记录今天的闪光点。",
            f"Track today's bright moments for {CHILD_NAME_EN} like a tiny adventure.",
            f"Halte die schönen Momente von heute für {CHILD_NAME_DE} wie ein kleines Abenteuer fest.",
        ),
        [
            t("完成感反馈", "Completion feedback", "Erfolgsgefühl"),
            t("今日小冒险", "Today's mini quest", "Heutige Mini-Mission"),
            t("奖励会发光", "Rewards glow brighter", "Belohnungen leuchten heller"),
        ],
    )

    col1, col2, col3 = st.columns(3)
    col1.metric(t("当前可用积分", "Current Points", "Aktuelle Punkte"), current_points)
    col2.metric(t("本周开始日期", "Week Start", "Wochenbeginn"), get_current_week_start())
    col3.metric(t("今日目标上限", "Today's Max", "Heutiges Maximum"), f"+{MAX_DAILY_EARN} / -{MAX_DAILY_DEDUCT}")
    _render_readonly_notice()

    st.markdown("---")
    left, right = st.columns([1.1, 0.9])

    with left:
        st.subheader(t("🟢 今日得分任务", "🟢 Today's Earning Tasks", "🟢 Heutige Pluspunkte-Aufgaben"))
        selected_earnings = []
        for task in EARNING_TASKS:
            checked = st.checkbox(
                t(task["label_zh"], task["label_en"], task["label_de"]),
                help=t(task["detail_zh"], task["detail_en"], task["detail_de"]),
                key=f"earn_{task['id']}",
            )
            if checked:
                selected_earnings.append(task["label_en"])

        st.subheader(t("⚠️ 今日提醒项", "⚠️ Today's Reminder Items", "⚠️ Heutige Erinnerungspunkte"))
        selected_deductions = []
        for task in DEDUCTION_TASKS:
            checked = st.checkbox(
                t(task["label_zh"], task["label_en"], task["label_de"]),
                key=f"deduct_{task['id']}",
            )
            if checked:
                selected_deductions.append(task["label_en"])

    with right:
        earning_points = min(len(selected_earnings), MAX_DAILY_EARN)
        deduction_points = min(len(selected_deductions), MAX_DAILY_DEDUCT)
        net_change = earning_points - deduction_points
        completion_ratio = min((earning_points + deduction_points) / (MAX_DAILY_EARN + MAX_DAILY_DEDUCT), 1.0)

        mood = (
            t("今天状态超棒，像小太阳一样。", "Today feels bright, like a little sun.", "Heute lief es richtig gut, wie eine kleine Sonne.")
            if net_change >= 2
            else t("今天有进步，继续稳稳前进。", "Nice progress today. Keep going steadily.", "Heute gab es Fortschritt. Geh ruhig und stetig weiter.")
            if net_change >= 0
            else t("今天有一点挑战，明天再来。", "A few bumps today. Tomorrow is another try.", "Heute war es etwas schwierig. Morgen gibt es einen neuen Versuch.")
        )

        st.markdown(
            f"""
            <div class="celebration-card">
                <h3>{t("今日完成感", "Today's Completion Feeling", "Heutiges Erfolgsgefühl")}</h3>
                <p style="font-size:2rem;font-weight:700;margin:6px 0 10px 0;">{net_change:+}</p>
                <p>{mood}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(completion_ratio)

        next_reward = next((reward for reward in REWARD_TIERS if current_points < reward["points"]), None)
        reward_feedback = (
            t(
                f"再努力 {next_reward['points'] - current_points} 分，就能点亮 {next_reward['name_zh']}。",
                f"{next_reward['points'] - current_points} more points to light up {next_reward['name_en']}.",
                f"Noch {next_reward['points'] - current_points} Punkte bis {next_reward['name_de']} leuchtet.",
            )
            if next_reward
            else t("已经达到最高奖励档位啦。", "The highest reward tier is already unlocked.", "Die höchste Belohnungsstufe ist bereits freigeschaltet.")
        )

        st.markdown(
            f"""
            <div class="soft-card">
                <h3>{t('奖励雷达', 'Reward Radar', 'Belohnungsradar')}</h3>
                <p>{reward_feedback}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(t("保存今天记录", "Save Today's Record", "Heutigen Eintrag speichern"), use_container_width=True, disabled=not admin_mode):
            upsert_daily_log(
                earned_tasks=selected_earnings,
                deduction_tasks=selected_deductions,
                earned_points=earning_points,
                deduction_points=deduction_points,
                net_change=net_change,
            )
            if net_change > 0:
                st.balloons()
                st.toast(t("太棒了，今天的努力记下来了。", "Nice work. Today's effort has been saved.", "Sehr gut. Die heutige Leistung wurde gespeichert."))
            st.success(f"{t('记录已保存，当前积分', 'Record saved. Current points', 'Eintrag gespeichert. Aktuelle Punkte')}: {load_points()}")
            st.rerun()

        if st.button(t("撤销上一次操作", "Undo Last Action", "Letzte Aktion rückgängig machen"), use_container_width=True, disabled=not admin_mode):
            st.success(undo_last_action())
            st.rerun()

    st.markdown("---")
    st.subheader(t("🌈 奖励预览", "🌈 Reward Preview", "🌈 Belohnungsvorschau"))
    reward_cols = st.columns(len(REWARD_TIERS))
    for col, reward in zip(reward_cols, REWARD_TIERS):
        with col:
            unlocked = current_points >= reward["points"]
            state = t("已点亮", "Unlocked", "Freigeschaltet") if unlocked else t("还差", "Need", "Noch nötig")
            remain = 0 if unlocked else reward["points"] - current_points
            st.markdown(
                f"""
                <div class="play-card">
                    <div style="font-size:1.8rem;margin-bottom:8px;">{"✨" if unlocked else "⭐"}</div>
                    <h3>{t(reward['name_zh'], reward['name_en'], reward['name_de'])}</h3>
                    <p>{reward['points']} {t('分', 'points', 'Punkte')}</p>
                    <p>{t(reward['desc_zh'], reward['desc_en'], reward['desc_de'])}</p>
                    <p style="margin-top:10px;font-weight:700;">{state} {remain if remain else ""}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_weekly_summary() -> None:
    current_points = load_points()
    current_week_start = get_current_week_start()
    daily_logs = get_current_week_daily_logs()
    redeem_logs = get_current_week_redeem_logs()
    level_info = _get_level_info(current_points)

    render_hero(
        t("📈 本周总览", "📈 Weekly Overview", "📈 Wochenüberblick"),
        t(
            f"一页看完 {CHILD_NAME_ZH} 这周的记录、成长和兑换。",
            f"See {CHILD_NAME_EN}'s records, progress, and redemptions for this week on one page.",
            f"Sieh {CHILD_NAME_DE}s Einträge, Fortschritt und Einlösungen dieser Woche auf einer Seite.",
        ),
        [t("本周数据", "Weekly data", "Wochendaten"), t("成长等级", "Growth level", "Wachstumslevel"), t("兑换记录", "Redemptions", "Einlösungen")],
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

    weekly_net_growth = int(daily_df["net_change"].sum()) if not daily_df.empty else 0
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("当前可用积分", "Current Points", "Aktuelle Punkte"), current_points)
    col2.metric(t("本周开始日期", "Week Start", "Wochenbeginn"), current_week_start)
    col3.metric(t("本周净增长", "Weekly Net Growth", "Nettozuwachs diese Woche"), weekly_net_growth)
    col4.metric(t("记录天数", "Recorded Days", "Erfasste Tage"), len(daily_df))

    st.markdown("---")
    st.subheader(t("⭐ 成长等级", "⭐ Growth Level", "⭐ Wachstumslevel"))
    level_col1, level_col2 = st.columns(2)
    level_col1.metric(t("当前等级", "Current Level", "Aktuelles Level"), f"Level {level_info['level']}")
    level_col2.metric(t("等级称号", "Level Title", "Leveltitel"), t(level_info["title_zh"], level_info["title_en"], level_info["title_de"]))

    points_needed, progress_value = _get_progress_data(current_points, level_info)
    if level_info["next_level_points"] is not None:
        st.write(f"{t('距离下一等级还差', 'Points needed for next level', 'Punkte bis zum nächsten Level')}: **{points_needed}**")
        st.progress(progress_value)
    else:
        st.success(t("已经达到最高等级。", "Highest level reached.", "Das höchste Level ist erreicht."))
        st.progress(1.0)

    task_counter = {task["label_en"]: 0 for task in EARNING_TASKS}
    if not daily_df.empty:
        for task_str in daily_df["earned_tasks"].fillna(""):
            for item in [part.strip() for part in str(task_str).split("|") if part.strip()]:
                if item in task_counter:
                    task_counter[item] += 1

    total_earned = int(daily_df["earned_points"].sum()) if not daily_df.empty else 0
    total_deducted = int(daily_df["deduction_points"].sum()) if not daily_df.empty else 0
    week_status = _get_week_status(weekly_net_growth)
    top_task_en = max(task_counter, key=task_counter.get) if task_counter else ""
    top_task_count = task_counter.get(top_task_en, 0)
    top_task = next(
        (t(task["label_zh"], task["label_en"], task["label_de"]) for task in EARNING_TASKS if task["label_en"] == top_task_en),
        t("暂无", "None yet", "Noch keine"),
    )

    st.markdown("---")
    story_col, summary_col = st.columns([1.05, 0.95])
    with story_col:
        st.markdown(
            f"""
            <div class="soft-card">
                <h3>{t(f'{CHILD_NAME_ZH}本周成长故事', f"{CHILD_NAME_EN}'s Weekly Story", f'{CHILD_NAME_DE}s Wochengeschichte')}</h3>
                <p>{t(
                    f"{CHILD_NAME_ZH} 这一周记录了 {len(daily_df)} 天，净增长 {weekly_net_growth} 分，最稳定的习惯是 {top_task}，一共完成了 {top_task_count} 次。",
                    f"{CHILD_NAME_EN} logged {len(daily_df)} day(s) this week, gained {weekly_net_growth} net points, and the strongest habit was {top_task} with {top_task_count} completions.",
                    f"{CHILD_NAME_DE} hat diese Woche an {len(daily_df)} Tag(en) Einträge gemacht, {weekly_net_growth} Nettopunkte gesammelt und die stärkste Gewohnheit war {top_task} mit {top_task_count} Abschlüssen."
                )}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with summary_col:
        st.markdown(
            f"""
            <div class="soft-card">
                <h3>{t('本周摘要', 'Weekly Snapshot', 'Wochenüberblick')}</h3>
                <p>{t('总加分', 'Total Earned', 'Gesammelte Pluspunkte')}: <b>{total_earned}</b></p>
                <p>{t('总扣分', 'Total Deducted', 'Abgezogene Punkte')}: <b>{total_deducted}</b></p>
                <p>{t('净增长', 'Net Growth', 'Nettozuwachs')}: <b>{weekly_net_growth}</b></p>
                <p>{t('本周状态', 'Week Status', 'Wochenstatus')}: <b>{week_status}</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader(t("📚 习惯统计", "📚 Habit Summary", "📚 Gewohnheitsübersicht"))
    habit_df = pd.DataFrame({"Habit": [t(task["label_zh"], task["label_en"], task["label_de"]) for task in EARNING_TASKS], "Count": list(task_counter.values())})
    habit_col1, habit_col2 = st.columns(2)
    with habit_col1:
        st.dataframe(habit_df, use_container_width=True, hide_index=True)
    with habit_col2:
        st.bar_chart(habit_df.set_index("Habit"))

    if daily_df.empty:
        st.markdown("---")
        st.info(t("本周还没有每日记录。", "No daily records for this week yet.", "Für diese Woche gibt es noch keine Tagesprotokolle."))
    else:
        st.markdown("---")
        st.subheader(t("📊 每日净变化", "📊 Daily Net Change", "📊 Tägliche Nettoveränderung"))
        st.line_chart(daily_df[["date", "net_change"]].copy().set_index("date"))

        st.markdown("---")
        st.subheader(t("🗂️ 本周每日记录", "🗂️ Daily Records This Week", "🗂️ Tagesprotokolle dieser Woche"))
        card_tab, table_tab = st.tabs([t("卡片视图", "Card View", "Kartenansicht"), t("表格视图", "Table View", "Tabellenansicht")])
        with card_tab:
            _render_daily_log_cards(daily_df)
        with table_tab:
            st.dataframe(_localize_daily_df(daily_df), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(t("🧸 本周兑换记录", "🧸 Reward Redemption This Week", "🧸 Einlösungen dieser Woche"))
    if redeem_df.empty:
        st.info(t("本周还没有兑换记录。", "No reward redemption this week yet.", "Für diese Woche gibt es noch keine Einlösungen."))
    else:
        card_tab, table_tab = st.tabs([t("卡片视图", "Card View", "Kartenansicht"), t("表格视图", "Table View", "Tabellenansicht")])
        with card_tab:
            _render_redeem_log_cards(redeem_df)
        with table_tab:
            st.dataframe(_localize_redeem_df(redeem_df), use_container_width=True, hide_index=True)


def render_reward_shop() -> None:
    current_points = load_points()
    can_redeem_today = datetime.today().weekday() == 6
    admin_mode = is_admin()

    render_hero(
        t("🧸 奖励商店", "🧸 Reward Shop", "🧸 Belohnungsladen"),
        t("在周日晚上用积分换喜欢的小玩具。", "Redeem favorite little rewards with points on Sunday.", "Löse am Sonntag mit Punkten kleine Lieblingsbelohnungen ein."),
        [t("周日兑换", "Sunday only", "Nur sonntags"), t("积分累积", "Carry-over points", "Punkte bleiben erhalten"), t("奖励分档", "Reward tiers", "Belohnungsstufen")],
    )

    st.metric(t("当前可用积分", "Current Points", "Aktuelle Punkte"), current_points)
    _render_readonly_notice()

    if can_redeem_today:
        st.success(t("今天是周日，可以兑换奖励。", "Today is Sunday. Reward redemption is available.", "Heute ist Sonntag. Belohnungen können eingelöst werden."))
    else:
        st.warning(t("今天不是周日，奖励仅可在周日兑换。", "Today is not Sunday. Rewards can only be redeemed on Sunday.", "Heute ist nicht Sonntag. Belohnungen können nur sonntags eingelöst werden."))

    st.markdown("---")
    sorted_rewards = sorted(REWARD_TIERS, key=lambda reward: reward["points"])
    for reward in sorted_rewards:
        can_afford = current_points >= reward["points"]
        can_redeem = can_redeem_today and can_afford
        unlocked_text = (
            t("可以兑换", "Ready to redeem", "Bereit zum Einlösen")
            if can_redeem
            else t("积分够了，等周日", "Enough points, wait for Sunday", "Genug Punkte, bis Sonntag warten")
            if can_afford
            else t("还差", "Need", "Noch nötig")
        )
        remain = 0 if can_afford else reward["points"] - current_points

        st.markdown(
            f"""
            <div class="play-card">
                <h3>{t(reward['name_zh'], reward['name_en'], reward['name_de'])}</h3>
                <p style="font-weight:700;">{reward['points']} {t('分', 'points', 'Punkte')}</p>
                <p>{t(reward['desc_zh'], reward['desc_en'], reward['desc_de'])}</p>
                <p style="margin-top:10px;font-weight:700;">{unlocked_text} {remain if remain else ""}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action_col, state_col = st.columns([1.1, 0.9])
        with action_col:
            if st.button(t("立即兑换", "Redeem Now", "Jetzt einlösen"), key=f"redeem_{reward['id']}", disabled=not (can_redeem and admin_mode), use_container_width=True):
                new_points = current_points - reward["points"]
                append_redeem_log(
                    reward_name=reward["name_en"],
                    points_cost=reward["points"],
                    points_after_redeem=new_points,
                )
                st.success(f"{t('兑换成功，剩余积分', 'Redeemed successfully. Remaining points', 'Erfolgreich eingelöst. Verbleibende Punkte')}: {new_points}")
                st.rerun()
        with state_col:
            if not admin_mode:
                st.info(t("只读查看。管理员登录后可兑换。", "Read-only view. Log in as admin to redeem.", "Nur Ansicht. Als Admin anmelden, um einzulösen."))
            elif not can_afford:
                st.info(t("积分不足。", "Not enough points yet.", "Noch nicht genug Punkte."))
            elif not can_redeem_today:
                st.info(t("请在周日再来兑换。", "Please come back on Sunday to redeem.", "Bitte komm am Sonntag zum Einlösen wieder."))
            else:
                st.info(t("已经满足兑换条件。", "Ready to redeem.", "Bereit zum Einlösen."))
        st.markdown("---")


def render_growth_report() -> None:
    render_weekly_summary()


def render_parent_dashboard() -> None:
    render_weekly_summary()


def render_monthly_report() -> None:
    daily_df = pd.DataFrame(load_daily_logs(), columns=DAILY_FIELDS)
    redeem_df = pd.DataFrame(load_redeem_logs(), columns=REDEEM_FIELDS)

    render_hero(
        t("🗓️ 月度报告", "🗓️ Monthly Report", "🗓️ Monatsbericht"),
        t(
            "按月份回看积分变化、习惯完成情况和奖励兑换。",
            "Review point changes, habit completions, and reward redemptions by month.",
            "Sieh dir Punkteveränderungen, Gewohnheiten und Einlösungen nach Monat an.",
        ),
        [
            t("月度汇总", "Monthly totals", "Monatssummen"),
            t("习惯趋势", "Habit trends", "Gewohnheitstrends"),
            t("兑换记录", "Redemptions", "Einlösungen"),
        ],
    )

    month_values: list[str] = []
    if not daily_df.empty:
        month_values.extend(pd.to_datetime(daily_df["date"]).dt.strftime("%Y-%m").tolist())
    if not redeem_df.empty:
        month_values.extend(pd.to_datetime(redeem_df["date"]).dt.strftime("%Y-%m").tolist())
    month_options = sorted(set(month_values), reverse=True)

    if not month_options:
        st.info(t("还没有月度数据。", "No monthly data yet.", "Es gibt noch keine Monatsdaten."))
        return

    selected_month = st.selectbox(
        t("选择月份", "Select Month", "Monat auswählen"),
        month_options,
        format_func=_month_label,
    )

    month_start = pd.Timestamp(f"{selected_month}-01")
    month_end = month_start + pd.offsets.MonthEnd(1)

    if not daily_df.empty:
        daily_df["date"] = pd.to_datetime(daily_df["date"])
        daily_df["earned_points"] = pd.to_numeric(daily_df["earned_points"])
        daily_df["deduction_points"] = pd.to_numeric(daily_df["deduction_points"])
        daily_df["net_change"] = pd.to_numeric(daily_df["net_change"])
        month_daily = daily_df[(daily_df["date"] >= month_start) & (daily_df["date"] <= month_end)].copy()
        month_daily["date"] = month_daily["date"].dt.strftime("%Y-%m-%d")
    else:
        month_daily = pd.DataFrame(columns=DAILY_FIELDS)

    if not redeem_df.empty:
        redeem_df["date"] = pd.to_datetime(redeem_df["date"])
        redeem_df["points_cost"] = pd.to_numeric(redeem_df["points_cost"])
        redeem_df["points_after_redeem"] = pd.to_numeric(redeem_df["points_after_redeem"])
        month_redeem = redeem_df[(redeem_df["date"] >= month_start) & (redeem_df["date"] <= month_end)].copy()
        month_redeem["date"] = month_redeem["date"].dt.strftime("%Y-%m-%d")
    else:
        month_redeem = pd.DataFrame(columns=REDEEM_FIELDS)

    total_earned = int(month_daily["earned_points"].sum()) if not month_daily.empty else 0
    total_deducted = int(month_daily["deduction_points"].sum()) if not month_daily.empty else 0
    net_growth = int(month_daily["net_change"].sum()) if not month_daily.empty else 0
    redeem_total = int(month_redeem["points_cost"].sum()) if not month_redeem.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("月总加分", "Monthly Earned", "Monatliche Pluspunkte"), total_earned)
    col2.metric(t("月总扣分", "Monthly Deducted", "Monatliche Abzüge"), total_deducted)
    col3.metric(t("月净增长", "Monthly Net Growth", "Monatlicher Nettozuwachs"), net_growth)
    col4.metric(t("月兑换积分", "Redeemed This Month", "Diesen Monat eingelöst"), redeem_total)

    st.markdown("---")
    left, right = st.columns([1.05, 0.95])
    with left:
        st.subheader(t("📊 每日净变化", "📊 Daily Net Change", "📊 Tägliche Nettoveränderung"))
        if month_daily.empty:
            st.info(t("这个月还没有每日记录。", "No daily records for this month yet.", "Für diesen Monat gibt es noch keine Tagesprotokolle."))
        else:
            st.bar_chart(month_daily[["date", "net_change"]].copy().set_index("date"))

    with right:
        st.subheader(t("📚 本月习惯统计", "📚 Habit Summary This Month", "📚 Gewohnheiten diesen Monat"))
        habit_rows = []
        source_series = month_daily["earned_tasks"].fillna("") if "earned_tasks" in month_daily.columns else pd.Series(dtype=str)
        for task in EARNING_TASKS:
            count = 0
            for task_str in source_series:
                count += sum(
                    1
                    for item in [part.strip() for part in str(task_str).split("|") if part.strip()]
                    if item in (task["label_zh"], task["label_en"], task["label_de"])
                )
            habit_rows.append(
                {
                    t("习惯", "Habit", "Gewohnheit"): t(task["label_zh"], task["label_en"], task["label_de"]),
                    t("次数", "Count", "Anzahl"): count,
                }
            )
        st.dataframe(pd.DataFrame(habit_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(t("🗂️ 本月每日记录", "🗂️ Daily Records This Month", "🗂️ Tagesprotokolle dieses Monats"))
    if month_daily.empty:
        st.info(t("这个月还没有每日记录。", "No daily records for this month yet.", "Für diesen Monat gibt es noch keine Tagesprotokolle."))
    else:
        card_tab, table_tab = st.tabs([t("卡片视图", "Card View", "Kartenansicht"), t("表格视图", "Table View", "Tabellenansicht")])
        with card_tab:
            _render_daily_log_cards(month_daily)
        with table_tab:
            st.dataframe(_localize_daily_df(month_daily), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader(t("🧸 本月兑换记录", "🧸 Redemptions This Month", "🧸 Einlösungen dieses Monats"))
    if month_redeem.empty:
        st.info(t("这个月还没有兑换记录。", "No redemptions for this month yet.", "Für diesen Monat gibt es noch keine Einlösungen."))
    else:
        card_tab, table_tab = st.tabs([t("卡片视图", "Card View", "Kartenansicht"), t("表格视图", "Table View", "Tabellenansicht")])
        with card_tab:
            _render_redeem_log_cards(month_redeem)
        with table_tab:
            st.dataframe(_localize_redeem_df(month_redeem), use_container_width=True, hide_index=True)


def render_edit_records() -> None:
    if not is_admin():
        render_hero(
            t("✏️ 编辑记录", "✏️ Edit Records", "✏️ Einträge bearbeiten"),
            t("这个页面仅管理员可用。", "This page is available to admins only.", "Diese Seite ist nur für Admins verfügbar."),
            [t("只读访问", "Read-only access", "Nur Lesen")],
        )
        st.warning(t("请先登录管理员后再编辑历史记录。", "Please log in as admin before editing records.", "Bitte melde dich als Admin an, bevor du Einträge bearbeitest."))
        return

    render_hero(
        t("✏️ 编辑记录", "✏️ Edit Records", "✏️ Einträge bearbeiten"),
        t("修正历史记录后，积分会自动从日志重新计算。", "After correcting a record, points are recalculated directly from logs.", "Nach einer Korrektur werden die Punkte direkt aus den Protokollen neu berechnet."),
        [t("每日记录", "Daily logs", "Tagesprotokolle"), t("兑换记录", "Redeem logs", "Einlöseprotokolle"), t("自动重算", "Auto recalculation", "Automatische Neuberechnung")],
    )

    daily_df = pd.DataFrame(load_daily_logs(), columns=DAILY_FIELDS)
    st.subheader(t("🗓️ 每日记录", "🗓️ Daily Log", "🗓️ Tagesprotokoll"))
    if daily_df.empty:
        st.info(t("还没有每日记录。", "No daily log yet.", "Es gibt noch kein Tagesprotokoll."))
    else:
        daily_df["timestamp"] = daily_df["timestamp"].astype(str)
        daily_show = daily_df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
        card_tab, table_tab = st.tabs([t("卡片视图", "Card View", "Kartenansicht"), t("表格视图", "Table View", "Tabellenansicht")])
        with card_tab:
            _render_daily_log_cards(daily_show)
        with table_tab:
            st.dataframe(_localize_daily_df(daily_show), use_container_width=True, hide_index=True)
        daily_show["display_label"] = daily_show["date"].astype(str) + " | " + daily_show["timestamp"].astype(str)
        selected_daily = st.selectbox(t("选择一条记录", "Select a row", "Zeile auswählen"), daily_show["display_label"].tolist())
        selected_row = daily_show[daily_show["display_label"] == selected_daily].iloc[0]
        row_idx = daily_df[daily_df["timestamp"].astype(str) == str(selected_row["timestamp"])].index[0]
        row = daily_df.loc[row_idx]

        with st.form("edit_daily_form"):
            new_date = st.text_input(t("日期", "Date", "Datum"), value="" if pd.isna(row["date"]) else str(row["date"]))
            new_earned_tasks = st.text_area(t("加分任务", "Earned Tasks", "Pluspunkte-Aufgaben"), value="" if pd.isna(row["earned_tasks"]) else str(row["earned_tasks"]))
            new_deduction_tasks = st.text_area(t("扣分任务", "Deduction Tasks", "Abzugsaufgaben"), value="" if pd.isna(row["deduction_tasks"]) else str(row["deduction_tasks"]))
            new_earned_points = st.number_input(t("加分", "Earned Points", "Pluspunkte"), step=1, value=int(row["earned_points"]) if not pd.isna(row["earned_points"]) else 0)
            new_deduction_points = st.number_input(t("扣分", "Deduction Points", "Abzugspunkte"), step=1, value=int(row["deduction_points"]) if not pd.isna(row["deduction_points"]) else 0)
            save_daily = st.form_submit_button(t("保存每日记录", "Save Daily Log", "Tagesprotokoll speichern"))

        if save_daily:
            update_daily_log_by_timestamp(
                str(row["timestamp"]),
                row_date=new_date.strip(),
                earned_tasks=new_earned_tasks.strip(),
                deduction_tasks=new_deduction_tasks.strip(),
                earned_points=int(new_earned_points),
                deduction_points=int(new_deduction_points),
            )
            recalculate_points()
            st.success(t("每日记录已更新。", "Daily log updated successfully.", "Tagesprotokoll erfolgreich aktualisiert."))
            st.rerun()

    st.markdown("---")
    redeem_df = pd.DataFrame(load_redeem_logs(), columns=REDEEM_FIELDS)
    st.subheader(t("🧸 兑换记录", "🧸 Redeem Log", "🧸 Einlöseprotokoll"))
    if redeem_df.empty:
        st.info(t("还没有兑换记录。", "No redeem log records found.", "Es wurden noch keine Einlöseprotokolle gefunden."))
    else:
        redeem_df["timestamp"] = redeem_df["timestamp"].astype(str)
        redeem_show = redeem_df.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
        card_tab, table_tab = st.tabs([t("卡片视图", "Card View", "Kartenansicht"), t("表格视图", "Table View", "Tabellenansicht")])
        with card_tab:
            _render_redeem_log_cards(redeem_show)
        with table_tab:
            st.dataframe(_localize_redeem_df(redeem_show), use_container_width=True, hide_index=True)
        redeem_show["display_label"] = redeem_show["date"].astype(str) + " | " + redeem_show["timestamp"].astype(str)
        selected_label = st.selectbox(t("选择一条兑换记录", "Select a redeem row", "Einlösezeile auswählen"), redeem_show["display_label"].tolist())
        selected_redeem = redeem_show[redeem_show["display_label"] == selected_label].iloc[0]
        redeem_row_idx = redeem_df[redeem_df["timestamp"].astype(str) == str(selected_redeem["timestamp"])].index[0]
        redeem_row = redeem_df.loc[redeem_row_idx]

        with st.form("edit_redeem_form"):
            new_redeem_date = st.text_input(t("兑换日期", "Redeem Date", "Einlösedatum"), value="" if pd.isna(redeem_row["date"]) else str(redeem_row["date"]))
            new_reward_name = st.text_input(t("奖励名称", "Reward Name", "Belohnungsname"), value="" if pd.isna(redeem_row["reward_name"]) else str(redeem_row["reward_name"]))
            new_points_cost = st.number_input(t("消耗积分", "Points Cost", "Eingelöste Punkte"), step=1, value=int(redeem_row["points_cost"]) if not pd.isna(redeem_row["points_cost"]) else 0)
            new_points_after_redeem = st.number_input(t("兑换后积分", "Points After Redeem", "Punkte nach Einlösung"), step=1, value=int(redeem_row["points_after_redeem"]) if not pd.isna(redeem_row["points_after_redeem"]) else 0)
            save_redeem = st.form_submit_button(t("保存兑换记录", "Save Redeem Log", "Einlöseprotokoll speichern"))

        if save_redeem:
            update_redeem_log_by_timestamp(
                str(redeem_row["timestamp"]),
                row_date=new_redeem_date.strip(),
                reward_name=new_reward_name.strip(),
                points_cost=int(new_points_cost),
                points_after_redeem=int(new_points_after_redeem),
            )
            recalculate_points()
            st.success(t("兑换记录已更新。", "Redeem log updated successfully.", "Einlöseprotokoll erfolgreich aktualisiert."))
            st.rerun()
