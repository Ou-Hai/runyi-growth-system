from datetime import datetime

import streamlit as st

from data_manager import append_redeem_log, load_points
from rules import REWARD_TIERS
from ui import init_sidebar, inject_styles, render_hero, t

st.set_page_config(page_title="Reward Shop", page_icon="🧸", layout="wide")


def is_sunday() -> bool:
    return datetime.today().weekday() == 6


init_sidebar()
inject_styles()

current_points = load_points()

render_hero(
    t("🧸 奖励商店", "🧸 Reward Shop"),
    t("在周日晚上用积分换喜欢的小玩具。", "Redeem favorite little rewards with points on Sunday."),
    [t("周日兑换", "Sunday only"), t("积分累积", "Carry-over points"), t("奖励分档", "Reward tiers")],
)

st.metric(t("当前可用积分", "Current Points"), current_points)

if is_sunday():
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
    can_redeem = is_sunday() and can_afford

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button(
            t("立即兑换", "Redeem Now"),
            key=f"redeem_{reward['id']}",
            disabled=not can_redeem,
            use_container_width=True,
        ):
            new_points = current_points - reward["points"]
            append_redeem_log(
                reward_name=t(reward["name_zh"], reward["name_en"]),
                points_cost=reward["points"],
                points_after_redeem=new_points,
            )
            st.success(
                f"{t('兑换成功，剩余积分', 'Redeemed successfully. Remaining points')}: {new_points}"
            )
            st.rerun()

    with col2:
        if not can_afford:
            st.info(t("积分不足。", "Not enough points yet."))
        elif not is_sunday():
            st.info(t("请在周日再来兑换。", "Please come back on Sunday to redeem."))
        else:
            st.info(t("已经满足兑换条件。", "Ready to redeem."))

    st.markdown("---")
