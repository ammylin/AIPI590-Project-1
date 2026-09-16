import streamlit as st

st.set_page_config(
    page_title="SwarmAudit Lite",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ SwarmAudit Lite")
st.subheader("Multi-agent red-teaming evaluation")

st.write(
    """
    This project investigates whether role-diverse AI red-teaming strategies
    provide broader and more reliable safety-test coverage than a single
    generic strategy.
    """
)

st.info(
    "The dashboard is currently in development. "
    "Sample evaluation results will be added next."
)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Evaluation mode", "Demo")

with col2:
    st.metric("Red-team conditions", "2")

with col3:
    st.metric("Model/API cost", "$0")