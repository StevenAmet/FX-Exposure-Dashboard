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
        try:
            df = pd.read_csv(file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()
    else:
        st.info("Please upload a CSV file")
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
# DATA CLEANING & VALIDATION
# -------------------------------
required_cols = ["currency", "value"]

for col in required_cols:
    if col not in df.columns:
        st.error(f"Missing required column: {col}")
        st.stop()

df = df.copy()

# Clean data
df["currency"] = df["currency"].astype(str).str.upper().str.strip()
df["value"] = pd.to_numeric(df["value"], errors="coerce")

# Remove invalid rows
invalid_rows = df[df["currency"] == ""]
if not invalid_rows.empty:
    st.warning("Some rows have empty currency and were removed")

df = df.dropna(subset=["currency", "value"])

# Remove negative values
if (df["value"] < 0).any():
    st.warning("Negative values detected — treating as absolute values")
    df["value"] = df["value"].abs()

# Final check
if df.empty:
    st.error("No valid data after cleaning")
    st.stop()

# -------------------------------
# BASE CURRENCY
# -------------------------------
currencies = sorted(df["currency"].dropna().unique())

if len(currencies) == 0:
    st.error("No valid currencies found")
    st.stop()

base_currency = st.sidebar.selectbox("Base Currency", currencies)

# -------------------------------
# FX RATES
# -------------------------------
st.markdown("### 💱 Live FX Rates")

@st.cache_data
def get_fx_rate(from_curr, to_curr):
    if from_curr == to_curr:
        return 1.0
    pair = f"{from_curr}{to_curr}=X"
    try:
        data = yf.download(pair, period="1d", interval="1m")
        if data.empty:
            return np.nan
        return float(data["Close"].iloc[-1])
    except:
        return np.nan

fx_rates = {}
failed_rates = []

for c in currencies:
    rate = get_fx_rate(c, base_currency)
    fx_rates[c] = rate
    if pd.isna(rate):
        failed_rates.append(c)

# Show FX table
fx_df = pd.DataFrame.from_dict(fx_rates, orient="index", columns=["FX Rate"])
st.dataframe(fx_df)

# Warn if missing rates
if failed_rates:
    st.warning(f"Missing FX rates for: {', '.join(failed_rates)}")

# -------------------------------
# CONVERSION
# -------------------------------
df["fx_rate"] = df["currency"].map(fx_rates)

missing_fx = df[df["fx_rate"].isna()]
if not missing_fx.empty:
    st.warning("Some assets could not be converted due to missing FX rates")

df["value_base"] = df["value"] * df["fx_rate"]

df = df.dropna(subset=["value_base"])

if df.empty:
    st.error("All FX conversions failed")
    st.stop()

total_value = df["value_base"].sum()

if total_value == 0:
    st.error("Total portfolio value is zero after conversion")
    st.stop()

# -------------------------------
# EXPOSURE
# -------------------------------
st.markdown("### 🌍 FX Exposure")

fx_exposure = df.groupby("currency")["value_base"].sum().sort_values(ascending=False)
fx_pct = fx_exposure / total_value

col1, col2 = st.columns(2)

with col1:
    st.dataframe(pd.DataFrame({
        "Exposure": fx_exposure,
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
    st.error("⚠️ Exposure breach — hedging required")
else:
    st.success("✅ Within limits")

# -------------------------------
# TARGET FX
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

total_target = sum(target_fx.values())

if abs(total_target - 1) > 0.01:
    st.warning("Target allocations should sum to 1 (100%)")

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
# TRADES
# -------------------------------
st.markdown("### 💱 Suggested FX Trades")

trade_df = pd.DataFrame({
    "Currency": hedge_df.index,
    "Trade": hedge_df["Adjustment"] * total_value
})

trade_df["Action"] = trade_df["Trade"].apply(
    lambda x: "BUY" if x > 0 else "SELL"
)

st.dataframe(trade_df.style.format({"Trade": "€{:,.0f}"}))

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
# SUMMARY
# -------------------------------
st.markdown("### 🧠 Executive Summary")

st.write(f"""
The portfolio totals €{total_value:,.0f} in {base_currency} terms.

Non-base currency exposure is {non_base:.2%}, relative to a limit of {limit:.2%}.

FX scenario analysis shows a potential impact of €{impact:,.0f} under a {shock:.0%} currency move.

Hedging analysis indicates adjustments are required to align with target allocations.

👉 FX exposure is a key driver of portfolio risk.
""")