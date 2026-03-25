from datetime import datetime

import streamlit as st

from auth import is_admin
from data_manager import get_current_week_start, load_points
from router_views import (
    render_edit_records,
    render_growth_report,
    render_monthly_report,
    render_parent_dashboard,
    render_reward_shop,
    render_task_center,
    render_weekly_summary,
)
from rules import APP_TITLE_DE, APP_TITLE_EN, APP_TITLE_ZH, CHILD_NAME_DE, CHILD_NAME_EN, CHILD_NAME_ZH
from ui import init_sidebar, inject_styles, render_hero, render_home_scene, t

ROUTES = {
    "home": {"emoji": "🗺️", "zh": "糖果地图", "en": "Candy Map", "de": "Bonbonkarte", "render": None},
    "task_center": {"emoji": "🍭", "zh": "任务糖果屋", "en": "Task Candy House", "de": "Aufgaben-Süßigkeitenhaus", "render": render_task_center},
    "weekly_summary": {"emoji": "📮", "zh": "本周总览", "en": "Weekly Overview", "de": "Wochenüberblick", "render": render_weekly_summary},
    "monthly_report": {"emoji": "🗓️", "zh": "月度报告", "en": "Monthly Report", "de": "Monatsbericht", "render": render_monthly_report},
    "reward_shop": {"emoji": "🧸", "zh": "奖励玩具店", "en": "Reward Toy Shop", "de": "Belohnungs-Spielzeugladen", "render": render_reward_shop},
    "growth_report": {"emoji": "📮", "zh": "本周总览", "en": "Weekly Overview", "de": "Wochenüberblick", "render": render_growth_report},
    "parent_dashboard": {"emoji": "📮", "zh": "本周总览", "en": "Weekly Overview", "de": "Wochenüberblick", "render": render_parent_dashboard},
    "edit_records": {"emoji": "🛠️", "zh": "修修工坊", "en": "Fix-It Workshop", "de": "Reparaturwerkstatt", "render": render_edit_records},
}

st.set_page_config(
    page_title=APP_TITLE_DE,
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "route" not in st.session_state:
    st.session_state["route"] = "home"

inject_styles()
init_sidebar(st.session_state["route"])


def open_route(route: str) -> None:
    st.session_state["route"] = route
    st.rerun()


def _format_week_start_metric(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value

    return t(
        parsed.strftime("%m-%d"),
        parsed.strftime("%b %d"),
        parsed.strftime("%d.%m."),
    )


def render_map_card(
    route: str,
    icon: str,
    title_zh: str,
    title_en: str,
    title_de: str,
    desc_zh: str,
    desc_en: str,
    desc_de: str,
) -> None:
    st.markdown('<div class="map-card">', unsafe_allow_html=True)
    label = t(
        f"{icon}  {title_zh}\n{desc_zh}",
        f"{icon}  {title_en}\n{desc_en}",
        f"{icon}  {title_de}\n{desc_de}",
    )
    if st.button(label, key=f"map_{route}", use_container_width=True):
        open_route(route)
    st.markdown("</div>", unsafe_allow_html=True)


route = st.session_state["route"]

if route == "home":
    current_points = load_points()
    current_week_start = get_current_week_start()

    render_hero(
        t(f"🌟 {APP_TITLE_ZH}", f"🌟 {APP_TITLE_EN}", f"🌟 {APP_TITLE_DE}"),
        t(
            f"欢迎来到 {CHILD_NAME_ZH} 的插画小地图。选任务糖果屋、本周总览或奖励玩具店，开始今天的成长冒险。",
            f"Welcome to {CHILD_NAME_EN}'s illustrated little map. Pick the Task Candy House, Weekly Overview, or Reward Toy Shop to begin today's growth adventure.",
            f"Willkommen auf {CHILD_NAME_DE}s illustrierter kleiner Karte. Wähle das Aufgaben-Süßigkeitenhaus, den Wochenüberblick oder den Belohnungs-Spielzeugladen und starte das heutige Wachstumsabenteuer.",
        ),
        [],
        variant="home",
    )
    render_home_scene()

    info_left, info_right = st.columns([1.15, 0.85])
    with info_left:
        st.markdown(
            f"""
            <div class="soft-card">
                <h3>{t("🎈 出发前的小提示", "🎈 Little Hint Before You Start", "🎈 Kleiner Hinweis vor dem Start")}</h3>
                <p>{t(
                    f"今天可以先去任务糖果屋打卡，再去本周总览看记录和成长，周日晚上还能去奖励玩具店兑换礼物。",
                    f"Start with the Task Candy House, then check Weekly Overview for records and growth, and visit the Reward Toy Shop on Sunday night for prizes."
                    ,
                    "Beginne im Aufgaben-Süßigkeitenhaus, schau dann im Wochenüberblick nach Einträgen und Fortschritt und besuche am Sonntagabend den Belohnungs-Spielzeugladen für Geschenke."
                )}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with info_right:
        col1, col2 = st.columns(2)
        col1.metric(t("当前可用积分", "Current Points", "Aktuelle Punkte"), current_points)
        col2.metric(t("本周开始日期", "Week Start", "Wochenbeginn"), _format_week_start_metric(current_week_start))

    st.markdown(
        f"""
        <div class="map-panel">
            <div class="map-title">{t('🗺️ 呦呦冒险地图', "🗺️ Yoyo's Adventure Map", "🗺️ Yoyos Abenteuerkarte")}</div>
        """,
        unsafe_allow_html=True,
    )

    row1 = st.columns(2)
    with row1[0]:
        render_map_card(
            "task_center", "🍭", "任务糖果屋", "Task Candy House", "Aufgaben-Süßigkeitenhaus",
            "把今天的好习惯变成亮晶晶的积分。",
            "Turn today's good habits into sparkling points.",
            "Verwandle die guten Gewohnheiten von heute in funkelnde Punkte.",
        )
    with row1[1]:
        render_map_card(
            "weekly_summary", "📮", "本周总览", "Weekly Overview", "Wochenüberblick",
            "把记录、成长和兑换放在一页看完。",
            "See records, growth, and redemptions on one page.",
            "Sieh Einträge, Fortschritt und Einlösungen auf einer Seite.",
        )

    row2 = st.columns(2)
    with row2[0]:
        render_map_card(
            "reward_shop", "🧸", "奖励玩具店", "Reward Toy Shop", "Belohnungs-Spielzeugladen",
            "周日晚上拿积分换喜欢的小礼物。",
            "Trade points for little favorite rewards on Sunday night.",
            "Tausche am Sonntagabend Punkte gegen kleine Lieblingsgeschenke.",
        )
    with row2[1]:
        render_map_card(
            "monthly_report", "🗓️", "月度报告", "Monthly Report", "Monatsbericht",
            "按月份回看积分、习惯和兑换情况。",
            "Review points, habits, and redemptions by month.",
            "Sieh dir Punkte, Gewohnheiten und Einlösungen nach Monat an.",
        )

    if is_admin():
        render_map_card(
            "edit_records", "🛠️", "修修工坊", "Fix-It Workshop", "Reparaturwerkstatt",
            "如果历史记录需要改动，从这里进去。",
            "Go here whenever a historical record needs fixing.",
            "Gehe hier hinein, wenn alte Einträge korrigiert werden müssen.",
        )

    st.markdown("</div>", unsafe_allow_html=True)
else:
    meta = ROUTES[route]
    if route == "edit_records" and not is_admin():
        st.warning(t("这个页面仅管理员可用。", "This page is available to admins only.", "Diese Seite ist nur für Admins verfügbar."))
        st.session_state["route"] = "home"
        st.stop()
    st.markdown(
        f"""
        <div class="soft-card" style="margin-bottom:18px;">
            <div style="font-size:0.98rem;opacity:0.72;">{t("当前位置", "You Are Here", "Du bist hier")}</div>
            <div style="font-size:1.6rem;font-weight:700;margin-top:6px;">{meta['emoji']} {t(meta['zh'], meta['en'], meta['de'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    meta["render"]()
