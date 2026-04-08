# -------------------------------
# run: streamlit run app.py
# -------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

st.set_page_config(page_title="FX Exposure Dashboard", layout="wide")

# -------------------------------
# TITLE
# -------------------------------
st.title("🌍 FX Exposure & Hedging Dashboard")
st.caption("Live FX Rates | Exposure Monitoring | Hedging | Scenario Analysis")
st.markdown("**Created by Steven Amet**")

# -------------------------------
# DATA INPUT
# -------------------------------
st.sidebar.header("📁 Portfolio Input")

input_method = st.sidebar.radio(
    "Select Input Method",
    ["Manual Entry", "Upload CSV"]
)

if input_method == "Upload CSV":
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if file:
        df = pd.read_csv(file)
    else:
        st.stop()

else:
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = pd.DataFrame({
            "asset_name": ["Asset 1"],
            "currency": ["EUR"],
            "value": [100000]
        })

    df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True
    )

    st.session_state.portfolio = df

# -------------------------------
# VALIDATION
# -------------------------------
if df.empty or df["value"].sum() == 0:
    st.warning("Enter valid data")
    st.stop()

# -------------------------------
# BASE CURRENCY
# -------------------------------
currencies = sorted(df["currency"].unique())

base_currency = st.sidebar.selectbox(
    "Base Currency",
    currencies
)

# -------------------------------
# LIVE FX RATES
# -------------------------------
st.markdown("### 💱 Live FX Rates")

@st.cache_data
def get_fx_rate(from_curr, to_curr):
    if from_curr == to_curr:
        return 1.0
    pair = f"{from_curr}{to_curr}=X"
    try:
        data = yf.download(pair, period="1d", interval="1m")
        return data["Close"].iloc[-1]
    except:
        return np.nan

fx_rates = {}

for c in currencies:
    fx_rates[c] = get_fx_rate(c, base_currency)

fx_df = pd.DataFrame.from_dict(fx_rates, orient="index", columns=["FX Rate"])
st.dataframe(fx_df)

# -------------------------------
# CONVERT TO BASE
# -------------------------------
df["fx_rate"] = df["currency"].map(fx_rates)
df["value_base"] = df["value"] * df["fx_rate"]

total_value = df["value_base"].sum()

# -------------------------------
# EXPOSURE (TRUE FX)
# -------------------------------
st.markdown("### 🌍 FX Exposure (Base Currency Adjusted)")

fx_exposure = df.groupby("currency")["value_base"].sum().sort_values(ascending=False)
fx_pct = fx_exposure / total_value

col1, col2 = st.columns(2)

with col1:
    st.dataframe(pd.DataFrame({
        "Exposure (Base)": fx_exposure,
        "Weight": fx_pct.map("{:.2%}".format)
    }))

with col2:
    fig, ax = plt.subplots()
    fx_exposure.plot(kind="pie", autopct="%1.1f%%", ax=ax)
    ax.set_ylabel("")
    st.pyplot(fig)

# -------------------------------
# RISK MONITORING
# -------------------------------
st.markdown("### ⚠️ FX Risk Monitoring")

non_base = fx_pct.drop(base_currency, errors="ignore").sum()

c1, c2 = st.columns(2)
c1.metric("Base Currency", base_currency)
c2.metric("Non-Base Exposure", f"{non_base:.2%}")

limit = st.slider("FX Exposure Limit", 0.0, 1.0, 0.4)

if non_base > limit:
    st.error("⚠️ Breach — hedging required")
else:
    st.success("✅ Within limits")

# -------------------------------
# TARGET FX (DYNAMIC)
# -------------------------------
st.markdown("### 🎯 Target FX Allocation")

target_fx = {}

cols = st.columns(len(fx_exposure))

for i, c in enumerate(fx_exposure.index):
    with cols[i]:
        target_fx[c] = st.number_input(
            c,
            min_value=0.0,
            max_value=1.0,
            value=float(fx_pct[c]),
            step=0.01
        )

# -------------------------------
# HEDGING
# -------------------------------
st.markdown("### 🔁 Hedging Requirements")

current = fx_pct.to_dict()

hedge = {
    c: target_fx[c] - current.get(c, 0)
    for c in target_fx
}

hedge_df = pd.DataFrame({
    "Current": current,
    "Target": target_fx,
    "Adjustment": hedge
})

st.dataframe(hedge_df.style.format("{:.2%}"))

# -------------------------------
# TRADE GENERATION
# -------------------------------
st.markdown("### 💱 Suggested FX Trades")

trade_df = pd.DataFrame({
    "Currency": hedge_df.index,
    "Trade (Base)": hedge_df["Adjustment"] * total_value
})

trade_df["Action"] = trade_df["Trade (Base)"].apply(
    lambda x: "BUY" if x > 0 else "SELL"
)

st.dataframe(trade_df.style.format({"Trade (Base)": "€{:,.0f}"}))

# -------------------------------
# SCENARIO
# -------------------------------
st.markdown("### 📉 FX Scenario Analysis")

shock = st.slider("Base Currency Strengthens (%)", 0, 10, 5) / 100

df["shock_rate"] = df["currency"].apply(
    lambda c: 1 if c == base_currency else (1 - shock)
)

df["stressed_value"] = df["value_base"] * df["shock_rate"]

impact = df["stressed_value"].sum() - total_value

st.metric("Portfolio Impact", f"€{impact:,.0f}")

# -------------------------------
# CONTRIBUTION
# -------------------------------
st.markdown("### 📊 FX Contribution")

contrib = df.groupby("currency")["stressed_value"].sum() - fx_exposure

fig2, ax2 = plt.subplots()
contrib.plot(kind="bar", ax=ax2)
ax2.set_ylabel("Impact (€)")
st.pyplot(fig2)

# -------------------------------
# EXECUTIVE SUMMARY
# -------------------------------
st.markdown("### 🧠 Executive Summary")

st.write(f"""
The portfolio totals €{total_value:,.0f} in {base_currency} terms.

Non-base currency exposure is {non_base:.2%}, relative to a limit of {limit:.2%}.

FX scenario analysis shows a potential impact of €{impact:,.0f} under a {shock:.0%} currency move.

Hedging analysis suggests adjustments are required to align with target allocations.

👉 FX exposure is a key driver of portfolio risk and requires active management.
""")