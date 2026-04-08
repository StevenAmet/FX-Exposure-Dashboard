# 🌍 FX Exposure & Hedging Dashboard

A professional Streamlit dashboard designed to simulate a **Currency Management / FX Risk function** within an investment firm.

This tool monitors foreign exchange exposure, converts portfolios into a base currency using live FX rates, and generates hedging recommendations.

Author:Steven Amet
---

## 🚀 Features

### 📊 Portfolio Input
- Manual entry (dynamic table)
- CSV upload support
- Multi-currency portfolios

### 💱 Live FX Rates
- Real-time FX rates via Yahoo Finance
- Automatic conversion into base currency

### 🌍 FX Exposure Monitoring
- Currency breakdown (absolute + %)
- Base vs non-base currency exposure
- Visual charts (pie + tables)

### ⚠️ Risk Monitoring
- Configurable FX exposure limits
- Automatic breach alerts

### 🎯 Hedging Engine
- User-defined target FX allocation
- Dynamic hedge calculation
- Suggested BUY / SELL trades

### 📉 Scenario Analysis
- Simulate base currency appreciation
- Portfolio impact calculation
- Contribution by currency

### 🧠 Executive Summary
- Auto-generated insights
- Clear explanation of FX risk

---

## 🏗️ How It Works

1. Input a portfolio with currency exposures
2. Convert all assets into a base currency using live FX rates
3. Calculate true FX exposure
4. Compare against target allocation
5. Generate hedging actions
6. Simulate FX shocks

---

## 📁 Example CSV Format

```csv
asset_name,currency,value
US Equity,USD,500000
EU Bonds,EUR,300000
UK Equity,GBP,200000
Cash USD,USD,100000