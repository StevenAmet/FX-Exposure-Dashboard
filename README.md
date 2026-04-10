# 🌍 FX Exposure & Hedging Dashboard

🔗 https://fx-exposure-dashboard-sa.streamlit.app/

A professional Streamlit dashboard designed to simulate a **Currency Management / FX Risk function** within an investment firm.

This tool monitors foreign exchange exposure, converts portfolios into a base currency using live FX rates, and generates spot and forward hedging recommendations.

Author:Steven Amet

---

## 🚀 Features

### 📊 Portfolio Input
- Manual entry (dynamic table)
- CSV upload support
- Multi-currency portfolios
- Automatic data validation and cleaning

### 💱 Live FX Rates
- ECB FX rates via Frankfurter API (EUR base)
- Fallback to Yahoo Finance market data
- Cross-currency conversion via EUR
- Debug FX rates table for transparency

### 🌍 FX Exposure Monitoring
- Currency breakdown (absolute + %)
- Portfolio fully converted into base currency
- Aggregated exposure by currency
- Clear tabular output for analysis

### ⚠️ Risk Monitoring
- Identification of concentrated FX exposures
- Missing FX rate detection and alerts
- Built-in data validation safeguards

### 🎯 Hedging Engine
- User-defined target FX allocation
- Dynamic hedge calculation
- Suggested BUY / SELL trades
- Trade sizing in base currency (€)

### 🔁 Spot Hedging
- Aligns portfolio exposure with target allocation
- Identifies over/underweight currency positions
- Generates actionable rebalancing trades

### 📅 Forward Hedging Simulation
- Forward FX pricing using interest rate differentials
- Adjustable tenor (1M, 3M, 6M)
- Simulated forward rates:
  Forward = Spot × (1 + interest differential)

### 📊 Forward Hedge Impact
- Estimated PnL from forward hedging
- Currency-level contribution analysis
- Visibility into hedging cost vs benefit

### 📉 Scenario Analysis
- Simulate base currency appreciation
- Portfolio impact calculation
- Sensitivity of foreign currency exposure

### 🧠 Executive Summary
- Auto-generated insights
- Total portfolio valuation in base currency
- Clear explanation of FX exposure and hedging strategy

---

## 🏗️ How It Works
- Input a portfolio with currency exposures
- Select a base currency
- Fetch live FX rates (ECB + fallback sources)
- Convert all assets into a base currency
- Calculate true FX exposure
- Compare against target allocation
- Generate spot hedging actions
- Simulate forward hedging using interest rate differentials
- Analyse portfolio impact under FX scenarios

---

## 📁 Example CSV Format
asset_name,currency,value
US Equity,USD,500000
EU Bonds,EUR,300000
UK Equity,GBP,200000
Cash USD,USD,100000