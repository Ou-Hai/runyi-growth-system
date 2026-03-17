import pandas as pd
import streamlit as st

from data_manager import (
    get_current_week_daily_logs,
    get_current_week_redeem_logs,
    get_current_week_start,
    load_points,
)
from ui import init_sidebar, inject_styles, render_hero, t

st.set_page_config(page_title="Weekly Summary", page_icon="📈", layout="wide")

init_sidebar()
inject_styles()

current_points = load_points()
current_week_start = get_current_week_start()

render_hero(
    t("📈 每周总结", "📈 Weekly Summary"),
    t("快速回看本周的打卡和兑换记录。", "A quick review of this week's records and redemptions."),
    [t("本周视角", "This week"), t("数据汇总", "Summaries"), t("兑换历史", "Redemptions")],
)

col1, col2 = st.columns(2)
col1.metric(t("当前可用积分", "Current Points"), current_points)
col2.metric(t("本周开始日期", "Week Start"), current_week_start)

logs = get_current_week_daily_logs()
redeem_logs = get_current_week_redeem_logs()

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
