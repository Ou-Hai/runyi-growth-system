from datetime import datetime

import streamlit as st

from auth import is_admin
from data_manager import load_points
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


def _format_date_metric(value: datetime) -> str:
    return value.strftime("%m.%d")


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

    def build_label(title: str, desc: str) -> str:
        return f"{icon}  {title}" if not desc else f"{icon}  {title}\n{desc}"

    label = t(
        build_label(title_zh, desc_zh),
        build_label(title_en, desc_en),
        build_label(title_de, desc_de),
    )
    if st.button(label, key=f"map_{route}", use_container_width=True):
        open_route(route)
    st.markdown("</div>", unsafe_allow_html=True)


route = st.session_state["route"]

if route == "home":
    current_points = load_points()
    today = datetime.now()

    render_hero(
        t(f"🌟 {APP_TITLE_ZH}", f"🌟 {APP_TITLE_EN}", f"🌟 {APP_TITLE_DE}"),
        t(
            f"欢迎来到{CHILD_NAME_ZH}的成长地图。选任务糖果屋、本周总览或奖励玩具店，开始今天的成长冒险。",
            f"Welcome to {CHILD_NAME_EN}'s growth map. Pick the Task Candy House, Weekly Overview, or Reward Toy Shop to begin today's growth adventure.",
            f"Willkommen auf {CHILD_NAME_DE}s Wachstumskarte. Wähle das Aufgaben-Süßigkeitenhaus, den Wochenüberblick oder den Belohnungs-Spielzeugladen und starte das heutige Wachstumsabenteuer.",
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
        col2.metric(t("今天日期", "Today", "Heute"), _format_date_metric(today))

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
            "",
            "",
            "",
        )
    with row1[1]:
        render_map_card(
            "weekly_summary", "📮", "本周总览", "Weekly Overview", "Wochenüberblick",
            "",
            "",
            "",
        )

    row2 = st.columns(2)
    with row2[0]:
        render_map_card(
            "reward_shop", "🧸", "奖励玩具店", "Reward Toy Shop", "Belohnungs-Spielzeugladen",
            "",
            "",
            "",
        )
    with row2[1]:
        render_map_card(
            "monthly_report", "🗓️", "月度报告", "Monthly Report", "Monatsbericht",
            "",
            "",
            "",
        )

    if is_admin():
        render_map_card(
            "edit_records", "🛠️", "修修工坊", "Fix-It Workshop", "Reparaturwerkstatt",
            "",
            "",
            "",
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
