"""Streamlit UI for Agent 1. ALL DATA IS SYNTHETIC. Runs fully offline."""
import pandas as pd
import streamlit as st

from agent import analyse

st.set_page_config(page_title="FinOps Waste & Savings Advisor", layout="wide")
st.title("FinOps Waste & Savings Advisor")
st.caption(
    "Synthetic data only. Findings come from deterministic read-only SQL rules; "
    "the local LLM only explains them. Savings are rough illustrative estimates."
)

scenario = st.sidebar.selectbox("Scenario", ["flawed", "partial", "clean"])
use_llm = st.sidebar.checkbox("Use local LLM explanations", value=False)
run_one = st.sidebar.button("Run analysis")
run_all = st.sidebar.button("Compare scenarios (before / after)")

if run_all:
    rows = []
    for name in ["flawed", "partial", "clean"]:
        r = analyse(name, use_llm=False)
        rows.append({"scenario": name, "findings": len(r["findings"]),
                     "est_monthly_saving_usd": r["total_saving"]})
    df = pd.DataFrame(rows)
    st.subheader("Projected savings: before vs after")
    st.bar_chart(df.set_index("scenario")["est_monthly_saving_usd"])
    st.table(df)

if run_one:
    with st.spinner("Running analysis..."):
        r = analyse(scenario, use_llm=use_llm)
    c1, c2, c3 = st.columns(3)
    c1.metric("Findings", len(r["findings"]))
    c2.metric("Est. monthly saving (USD)", f"${r['total_saving']:,.2f}")
    c3.metric("Audit chain", "verified" if r["audit"]["ok"] else "BROKEN")
    if r["findings"]:
        cols = ["rule_id", "rule_name", "severity", "resource_id", "est_monthly_saving_usd", "source"]
        st.subheader("Findings")
        st.dataframe(pd.DataFrame(r["findings"])[cols], width='stretch')
        st.subheader("Explanations")
        for f in r["findings"]:
            st.markdown(f"**{f['resource_id']}** [{f['severity']}]: {f['explanation']}")
    else:
        st.success("No findings in this scenario.")

if run_one:
    st.subheader("Sovereignty check")
    st.write(r["sovereignty"]["claim"])
    st.caption(r["sovereignty"]["scope"])
    st.write("External connections:", r["sovereignty"]["external_connections"])
    st.write("Loopback connections:", r["sovereignty"]["loopback_connections"])
    st.subheader("Audit log")
    st.write(r["audit"])
