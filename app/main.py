import streamlit as st

from data_manager import get_current_week_start, load_points
from router_views import (
    render_edit_records,
    render_growth_report,
    render_parent_dashboard,
    render_reward_shop,
    render_task_center,
    render_weekly_summary,
)
from rules import APP_TITLE_EN, APP_TITLE_ZH, CHILD_NAME_EN, CHILD_NAME_ZH
from ui import init_sidebar, inject_styles, render_hero, render_home_scene, t

ROUTES = {
    "home": {"emoji": "🗺️", "zh": "糖果地图", "en": "Candy Map", "render": None},
    "task_center": {"emoji": "🍭", "zh": "任务糖果屋", "en": "Task Candy House", "render": render_task_center},
    "weekly_summary": {"emoji": "📮", "zh": "总结邮局", "en": "Summary Post Office", "render": render_weekly_summary},
    "reward_shop": {"emoji": "🧸", "zh": "奖励玩具店", "en": "Reward Toy Shop", "render": render_reward_shop},
    "growth_report": {"emoji": "🚪", "zh": "星星门报告", "en": "Star Gate Report", "render": render_growth_report},
    "parent_dashboard": {"emoji": "🏡", "zh": "家长小屋", "en": "Parent Cottage", "render": render_parent_dashboard},
    "edit_records": {"emoji": "🛠️", "zh": "修修工坊", "en": "Fix-It Workshop", "render": render_edit_records},
}

st.set_page_config(
    page_title=APP_TITLE_EN,
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


def render_map_card(route: str, icon: str, title_zh: str, title_en: str, desc_zh: str, desc_en: str) -> None:
    st.markdown('<div class="map-card">', unsafe_allow_html=True)
    label = t(
        f"{icon}  {title_zh}\n{desc_zh}",
        f"{icon}  {title_en}\n{desc_en}",
    )
    if st.button(label, key=f"map_{route}", use_container_width=True):
        open_route(route)
    st.markdown("</div>", unsafe_allow_html=True)


route = st.session_state["route"]

if route == "home":
    current_points = load_points()
    current_week_start = get_current_week_start()

    render_hero(
        t(f"🌟 {APP_TITLE_ZH}", f"🌟 {APP_TITLE_EN}"),
        t(
            f"欢迎来到 {CHILD_NAME_ZH} 的插画小地图。选一扇星星门、糖果屋或玩具店，开始今天的成长冒险。",
            f"Welcome to {CHILD_NAME_EN}'s illustrated little map. Pick a star gate, candy house, or toy shop to begin today's growth adventure.",
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
                <h3>{t("🎈 出发前的小提示", "🎈 Little Hint Before You Start")}</h3>
                <p>{t(
                    f"今天可以先去任务糖果屋打卡，再去总结邮局看记录，周日晚上还能去奖励玩具店兑换礼物。",
                    f"Start with the Task Candy House, stop by the Summary Post Office, and visit the Reward Toy Shop on Sunday night for prizes."
                )}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with info_right:
        col1, col2 = st.columns(2)
        col1.metric(t("当前可用积分", "Current Points"), current_points)
        col2.metric(t("本周开始日期", "Week Start"), current_week_start)

    st.markdown(
        f"""
        <div class="map-panel">
            <div class="map-title">{t('🗺️ 呦呦冒险地图', "🗺️ Yoyo's Adventure Map")}</div>
        """,
        unsafe_allow_html=True,
    )

    row1 = st.columns(3)
    with row1[0]:
        render_map_card(
            "task_center", "🍭", "任务糖果屋", "Task Candy House",
            "把今天的好习惯变成亮晶晶的积分。",
            "Turn today's good habits into sparkling points.",
        )
    with row1[1]:
        render_map_card(
            "weekly_summary", "📮", "总结邮局", "Summary Post Office",
            "收一收这周的记录和兑换信件。",
            "Collect this week's records and reward letters.",
        )
    with row1[2]:
        render_map_card(
            "reward_shop", "🧸", "奖励玩具店", "Reward Toy Shop",
            "周日晚上拿积分换喜欢的小礼物。",
            "Trade points for little favorite rewards on Sunday night.",
        )

    row2 = st.columns(3)
    with row2[0]:
        render_map_card(
            "growth_report", "🚪", "星星门报告", "Star Gate Report",
            "看看离下一个等级还有多远。",
            "See how far the next level is.",
        )
    with row2[1]:
        render_map_card(
            "parent_dashboard", "🏡", "家长小屋", "Parent Cottage",
            "给家长看一眼就懂的本周概览。",
            "A quick weekly overview for parents.",
        )
    with row2[2]:
        render_map_card(
            "edit_records", "🛠️", "修修工坊", "Fix-It Workshop",
            "如果历史记录需要改动，从这里进去。",
            "Go here whenever a historical record needs fixing.",
        )

    st.markdown("</div>", unsafe_allow_html=True)
else:
    meta = ROUTES[route]
    st.markdown(
        f"""
        <div class="soft-card" style="margin-bottom:18px;">
            <div style="font-size:0.98rem;opacity:0.72;">{t("当前位置", "You Are Here")}</div>
            <div style="font-size:1.6rem;font-weight:700;margin-top:6px;">{meta['emoji']} {t(meta['zh'], meta['en'])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    meta["render"]()
