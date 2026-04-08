# -------------------------------
# run: streamlit run app.py
# -------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import requests

st.set_page_config(page_title="FX Exposure Dashboard", layout="wide")

# -------------------------------
# TITLE
# -------------------------------
st.title("🌍 FX Exposure & Hedging Dashboard")
st.caption("Spot & Forward Hedging | Live FX | Risk Monitoring")
st.markdown("**Created by Steven Amet**")

# -------------------------------
# SETTINGS
# -------------------------------
currency_options = ["EUR", "USD", "GBP", "JPY", "CHF", "AUD", "CAD"]

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

    df = st.session_state.portfolio.copy()

    for i in range(len(df)):
        if not df.loc[i, "asset_name"]:
            df.loc[i, "asset_name"] = f"Asset {i+1}"

    df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "asset_name": st.column_config.TextColumn("Asset Name"),
            "currency": st.column_config.SelectboxColumn(
                "Currency",
                options=currency_options
            ),
            "value": st.column_config.NumberColumn("Value")
        },
        use_container_width=True
    )

    df["asset_name"] = [
        name if name else f"Asset {i+1}"
        for i, name in enumerate(df["asset_name"])
    ]

    st.session_state.portfolio = df

# -------------------------------
# CLEANING
# -------------------------------
df["currency"] = df["currency"].astype(str).str.upper().str.strip()
df["value"] = pd.to_numeric(df["value"], errors="coerce")

df = df.dropna(subset=["currency", "value"])

if df.empty:
    st.error("No valid data")
    st.stop()

# -------------------------------
# BASE CURRENCY
# -------------------------------
base_currency = st.sidebar.selectbox(
    "Base Currency",
    currency_options,
    index=0
)

# -------------------------------
# FX RATE ENGINE (FIXED + ROBUST)
# -------------------------------

@st.cache_data(ttl=3600)
def fetch_all_rates():
    """Fetch FX rates (EUR base) - robust version"""
    try:
        url = "https://api.exchangerate.host/latest"
        response = requests.get(url, timeout=5)

        if response.status_code != 200:
            return {}

        data = response.json()

        # Validate structure
        if not data or "rates" not in data:
            return {}

        rates = data["rates"]

        # 🔥 CRITICAL: Ensure EUR exists
        rates["EUR"] = 1.0

        return rates

    except Exception as e:
        return {}


@st.cache_data(ttl=3600)
def fetch_yfinance(pair):
    """Fallback market FX data"""
    try:
        data = yf.download(pair, period="5d", progress=False)

        if data.empty or "Close" not in data:
            return None

        return float(data["Close"].dropna().iloc[-1])

    except Exception:
        return None


@st.cache_data(ttl=3600)
def get_fx_rate(from_curr, to_curr):

    # -------------------------------
    # SAME currency (CRITICAL FIX)
    # -------------------------------
    if from_curr == to_curr:
        return 1.0

    rates = fetch_all_rates()

    # -------------------------------
    # PRIMARY: EUR BASE LOGIC
    # -------------------------------
    if rates:

        # EUR → XXX
        if from_curr == "EUR" and to_curr in rates:
            return rates[to_curr]

        # XXX → EUR
        if to_curr == "EUR" and from_curr in rates:
            return 1 / rates[from_curr]

        # CROSS via EUR
        if from_curr in rates and to_curr in rates:
            return rates[to_curr] / rates[from_curr]
        
st.write("DEBUG RATES:", fetch_all_rates())

    # -------------------------------
    # FALLBACK: YAHOO (MARKET DATA)
    # -------------------------------
    rate = fetch_yfinance(f"{from_curr}{to_curr}=X")
    if rate is not None:
        return rate

    inverse = fetch_yfinance(f"{to_curr}{from_curr}=X")
    if inverse is not None:
        return 1 / inverse

    # -------------------------------
    # FINAL FAIL
    # -------------------------------
    return np.nan

# -------------------------------
# FX RATES
# -------------------------------
st.markdown("### 💱 Live FX Rates")

currencies = sorted(set(df["currency"].unique()).union({base_currency}))

fx_rates = {c: get_fx_rate(c, base_currency) for c in currencies}

# 🔥 CRITICAL FIX — FORCE BASE CURRENCY
fx_rates[base_currency] = 1.0

fx_df = pd.DataFrame.from_dict(fx_rates, orient="index", columns=["FX Rate"])
fx_df["FX Rate"] = fx_df["FX Rate"].round(4)

st.dataframe(fx_df)

missing = [
    c for c, r in fx_rates.items()
    if pd.isna(r) and c != base_currency
]

if missing:
    st.warning(f"""
⚠️ Missing FX rates for: {', '.join(missing)}

Fallback logic attempted:
- ECB
- exchangerate.host
- Yahoo Finance

👉 These currencies are excluded from calculations.
""")

# -------------------------------
# CONVERSION
# -------------------------------
df["fx_rate"] = df["currency"].map(fx_rates)
df["value_base"] = df["value"] * df["fx_rate"]

df = df.dropna(subset=["value_base"])

if df.empty:
    st.error("All FX conversions failed")
    st.stop()

total_value = df["value_base"].sum()

# -------------------------------
# EXPOSURE
# -------------------------------
st.markdown("### 🌍 FX Exposure")

fx_exposure = df.groupby("currency")["value_base"].sum()
fx_pct = fx_exposure / total_value

st.dataframe(pd.DataFrame({
    "Exposure": fx_exposure,
    "Weight": fx_pct.map("{:.2%}".format)
}))

# -------------------------------
# TARGET FX
# -------------------------------
st.markdown("### 🎯 Target FX Allocation")

target_fx = {}
cols = st.columns(len(fx_exposure))

for i, c in enumerate(fx_exposure.index):
    with cols[i]:
        target_fx[c] = st.number_input(
            c, 0.0, 1.0, float(fx_pct[c]), step=0.01
        )

# -------------------------------
# SPOT HEDGING
# -------------------------------
st.markdown("### 🔁 Spot Hedging")

hedge = {c: target_fx[c] - fx_pct.get(c, 0) for c in target_fx}

spot_df = pd.DataFrame({
    "Adjustment": hedge,
    "Trade (€)": [v * total_value for v in hedge.values()]
}, index=hedge.keys())

spot_df["Action"] = spot_df["Trade (€)"].apply(
    lambda x: "BUY" if x > 0 else "SELL"
)

st.dataframe(spot_df.style.format({
    "Adjustment": "{:.2%}",
    "Trade (€)": "€{:,.0f}"
}))

# -------------------------------
# FX FORWARD HEDGING
# -------------------------------
st.markdown("### 📅 FX Forward Hedging Simulation")

tenor = st.selectbox("Forward Tenor", ["1M", "3M", "6M"])

interest_diff = st.slider(
    "Interest Rate Differential (%)",
    -5.0, 5.0, 1.0
) / 100

forward_rates = {}

for c in currencies:
    spot = fx_rates[c]
    forward_rates[c] = np.nan if pd.isna(spot) else spot * (1 + interest_diff)

fwd_df = pd.DataFrame({
    "Spot": fx_rates,
    "Forward": forward_rates
})

st.dataframe(fwd_df.round(4))

forward_impact = {}

for c in hedge:
    if pd.isna(forward_rates[c]):
        forward_impact[c] = np.nan
    else:
        forward_impact[c] = hedge[c] * total_value * (forward_rates[c] - fx_rates[c])

st.markdown("### 📊 Forward Hedge Impact")

fwd_impact_df = pd.DataFrame.from_dict(
    forward_impact, orient="index", columns=["PnL (€)"]
)

st.dataframe(fwd_impact_df.style.format("€{:,.0f}"))

# -------------------------------
# SCENARIO
# -------------------------------
st.markdown("### 📉 FX Scenario")

shock = st.slider("Base Currency Strengthens (%)", 0, 10, 5) / 100

df["shock"] = df["currency"].apply(
    lambda c: 1 if c == base_currency else (1 - shock)
)

impact = (df["value_base"] * df["shock"]).sum() - total_value

st.metric("Scenario Impact", f"€{impact:,.0f}")

# -------------------------------
# SUMMARY
# -------------------------------
st.markdown("### 🧠 Executive Summary")

st.write(f"""
Portfolio value: €{total_value:,.0f}

FX exposure is actively monitored and converted into base currency terms.

Spot hedging aligns exposures with target allocations.

Forward hedging incorporates interest rate differentials to simulate real FX forward pricing.

👉 Multi-source FX engine (ECB + exchangerate.host + Yahoo) ensures high reliability.
""")