from datetime import datetime

import streamlit as st

from app.data_manager import load_points, save_points, append_redeem_log

st.set_page_config(page_title="Reward Shop", page_icon="🧸", layout="wide")

REWARDS = [
    {"name": "🧸 Small Toy Reward", "points": 12, "desc": "A small toy within the weekly family budget."},
    {"name": "🚗 Better Toy Reward", "points": 30, "desc": "A better toy for bigger effort and consistency."},
    {"name": "🏆 Big Reward", "points": 38, "desc": "A big reward for an excellent growth week."},
]


def is_sunday():
    return datetime.today().weekday() == 6


st.title("🧸 Reward Shop")
st.caption("Redeem rewards with points. Redemption is allowed on Sunday only.")

current_points = load_points()
st.metric("Current Weekly Points", current_points)

if is_sunday():
    st.success("Today is Sunday. Reward redemption is available.")
else:
    st.warning("Today is not Sunday. Rewards can only be redeemed on Sunday.")

st.markdown("---")

for reward in REWARDS:
    st.subheader(f"{reward['name']} — {reward['points']} points")
    st.write(reward["desc"])

    can_afford = current_points >= reward["points"]
    can_redeem = is_sunday() and can_afford

    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button(f"Redeem {reward['points']}", key=f"redeem_{reward['points']}", disabled=not can_redeem):
            new_points = current_points - reward["points"]
            save_points(new_points)
            append_redeem_log(
                reward_name=reward["name"],
                points_cost=reward["points"],
                points_after_redeem=new_points,
            )
            st.success(f"Redeemed successfully! Remaining points: {new_points}")
            st.rerun()

    with col2:
        if not can_afford:
            st.info("Not enough points yet.")
        elif not is_sunday():
            st.info("Please come back on Sunday to redeem.")
        else:
            st.info("Ready to redeem.")

    st.markdown("---")