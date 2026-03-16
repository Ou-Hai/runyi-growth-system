import streamlit as st
import pandas as pd

from app.data_manager import load_points, load_daily_logs, load_redeem_logs

st.markdown("---")
st.subheader("🧸 Reward Redemption History")

redeem_logs = load_redeem_logs()

if not redeem_logs:
    st.info("No rewards redeemed yet.")
else:
    redeem_df = pd.DataFrame(redeem_logs)

    redeem_df["points_cost"] = pd.to_numeric(redeem_df["points_cost"])
    redeem_df["points_after_redeem"] = pd.to_numeric(redeem_df["points_after_redeem"])

    st.dataframe(redeem_df, use_container_width=True)



st.set_page_config(page_title="Weekly Summary", page_icon="📈", layout="wide")

st.title("📈 Weekly Summary")
st.caption("Review Runyi's recent growth records")

current_points = load_points()
st.metric("Current Weekly Points", current_points)

logs = load_daily_logs()

if not logs:
    st.info("No daily records yet.")
else:
    df = pd.DataFrame(logs)

    # convert numeric columns
    df["earned_points"] = pd.to_numeric(df["earned_points"])
    df["deduction_points"] = pd.to_numeric(df["deduction_points"])
    df["net_change"] = pd.to_numeric(df["net_change"])

    st.subheader("Daily Records")
    st.dataframe(df, use_container_width=True)

    st.subheader("Net Change Trend")
    chart_df = df[["date", "net_change"]].copy()
    chart_df = chart_df.set_index("date")
    st.line_chart(chart_df)

    st.subheader("Quick Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(df))
    col2.metric("Total Earned", int(df["earned_points"].sum()))
    col3.metric("Total Deducted", int(df["deduction_points"].sum()))