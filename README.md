# DRIFT — Algorithmic Trading Platform 🚀

> An end-to-end algorithmic trading platform with real-time data streaming, ML-powered signal generation, backtesting, paper trading, drift monitoring and automated pipelines.

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-Streaming-red)
![TimescaleDB](https://img.shields.io/badge/TimescaleDB-Time%20Series-orange)

---

## 📌 Overview

DRIFT is an automated trading research system that:

- Ingests **historical (5 years) and real-time** market data for 5 tickers
- Engineers **14 technical indicators** as ML features
- Streams live prices via an **Apache Kafka (Redpanda)** pipeline into TimescaleDB
- Trains and compares **Logistic Regression, XGBoost (Optuna-tuned) and LSTM** models for binary BUY/SELL prediction, tracked with **MLflow** and explained with **SHAP**
- Generates signals with a confidence filter and **Kelly Criterion** position sizing
- Validates strategies with **Backtrader** backtesting
- Places **paper trades** through the Alpaca API
- Monitors feature drift with **Evidently AI** and visualises data in **Grafana** and **Streamlit**
- Automates daily and weekly workflows with **Prefect**
- Serves signals through a **FastAPI** service
- Cloud deployment and CI/CD are still in progress *(see Roadmap)*

---

## 🏗️ Architecture

```
Data Sources (yfinance / Alpaca API)
            │
            ▼
      Apache Kafka (Redpanda)
      [Real-Time Streaming]
            │
            ▼
       TimescaleDB
   [stock_prices hypertable]
            │
            ▼
   Feature Engineering Pipeline
   [stock_features hypertable]
   RSI | MACD | Bollinger Bands
   SMA | EMA
            │
            ▼
   ML Models (LogReg | XGBoost + Optuna | LSTM)
   tracked with MLflow, explained with SHAP
            │
            ▼
   Signal Generator
   confidence filter + Kelly position sizing
            │
      ┌─────┴─────────────┐
      ▼                   ▼
 Backtesting          Paper Trading
 (Backtrader)         (Alpaca API)

 Monitoring:    Evidently AI (drift) | Grafana
 Serving/UI:    FastAPI | Streamlit
 Automation:    Prefect (daily pipeline, weekly maintenance)
```

---

## 🗂️ Project Structure

```
drift/
├── data/
│   ├── ingestion/
│   │   └── fetcher.py            # yfinance ingestion pipeline
│   ├── features/
│   │   ├── indicators.py         # RSI, MACD, Bollinger Bands, SMA, EMA
│   │   └── feature_pipeline.py   # stock_prices -> stock_features
│   └── db_connection.py          # Reusable TimescaleDB connection
│
├── models/
│   └── training/
│       └── train.py              # LogReg, XGBoost, Optuna, SHAP, LSTM, MLflow
│
├── streaming/
│   ├── producer.py               # Kafka producer (live price -> Kafka)
│   └── consumer.py               # Kafka consumer (Kafka -> TimescaleDB)
│
├── trading/
│   ├── signal_generator.py       # BUY/SELL/FLAT signals + Kelly sizing
│   └── paper_trader.py           # Alpaca paper trading
│
├── backtesting/
│   └── backtest.py               # Backtrader strategy + metrics
│
├── monitoring/
│   └── drift_detector.py         # Evidently drift report
│
├── orchestration/
│   └── prefect_flows/
│       └── trading_pipeline.py   # Daily + weekly Prefect flows
│
├── api/
│   ├── main.py                   # FastAPI endpoints
│   └── streamlit_app.py          # Streamlit dashboard
│
├── docker-compose.yml            # TimescaleDB, Redpanda, Grafana
├── requirements.txt
└── README.md
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Market Data | yfinance, Alpaca API |
| Database | TimescaleDB (PostgreSQL hypertables) |
| Streaming | Apache Kafka (Redpanda) |
| ML Models | scikit-learn, XGBoost, TensorFlow (LSTM) |
| Tuning / Explainability | Optuna, SHAP |
| Experiment Tracking | MLflow |
| Backtesting | Backtrader |
| Paper Trading | Alpaca API |
| Monitoring | Evidently AI, Grafana |
| Orchestration | Prefect |
| Serving / UI | FastAPI, Streamlit |
| Containerization | Docker + Docker Compose |
| Cloud / CI/CD | In progress |
| Language | Python 3.12, SQL |

---

## 📊 Data Pipeline

### Tickers Tracked

```
AAPL    →  Apple Inc
MSFT    →  Microsoft
GOOG    →  Google (Alphabet)
AMZN    →  Amazon
BTC-USD →  Bitcoin
```

### Dataset

- Source: Yahoo Finance via yfinance, daily OHLCV bars, about 5 years (2021 to 2026)
- Stocks have roughly 3,000 rows each; BTC-USD has roughly 4,400 because it trades every day
- Model inputs: 12 features (RSI, MACD, MACD signal, MACD histogram, Bollinger upper/middle/lower, SMA 20/50/200, EMA 12/26)
- Label: next-day return thresholded at +/-0.2%; FLAT samples are dropped, so the task is binary BUY (1) vs SELL (-1)
- Train/test split: chronological 80/20 with no shuffling, to avoid lookahead bias

### Database Schema

**stock_prices** (hypertable):

```sql
time      TIMESTAMPTZ NOT NULL
symbol    VARCHAR(10) NOT NULL
open      DOUBLE PRECISION
high      DOUBLE PRECISION
low       DOUBLE PRECISION
close     DOUBLE PRECISION
volume    BIGINT
```

**stock_features** (hypertable):

```sql
time        TIMESTAMPTZ NOT NULL
symbol      VARCHAR(10) NOT NULL
rsi         DOUBLE PRECISION   -- Relative Strength Index (14)
macd        DOUBLE PRECISION   -- MACD Line
macd_signal DOUBLE PRECISION   -- Signal Line (9)
macd_hist   DOUBLE PRECISION   -- MACD Histogram
bb_upper    DOUBLE PRECISION   -- Bollinger Band Upper
bb_middle   DOUBLE PRECISION   -- Bollinger Band Middle (SMA 20)
bb_lower    DOUBLE PRECISION   -- Bollinger Band Lower
sma_20      DOUBLE PRECISION   -- Simple Moving Average 20
sma_50      DOUBLE PRECISION   -- Simple Moving Average 50
sma_200     DOUBLE PRECISION   -- Simple Moving Average 200
ema_12      DOUBLE PRECISION   -- Exponential Moving Average 12
ema_26      DOUBLE PRECISION   -- Exponential Moving Average 26
```

---

## 🔄 Real-Time Streaming Pipeline

```
Live price source
      ↓
producer.py (fetches live prices every second)
      ↓
Apache Kafka / Redpanda (topic: stock-prices)
      ↓
consumer.py (reads from Kafka)
      ↓
TimescaleDB (stock_prices hypertable)
```

---

## 📈 Features Engineered

| Indicator | Type | Description |
|---|---|---|
| RSI (14) | Momentum | Overbought/oversold signal (0-100) |
| MACD Line | Trend | 12 EMA - 26 EMA |
| MACD Signal | Trend | 9 EMA of MACD line |
| MACD Histogram | Trend | MACD - Signal line |
| Bollinger Upper | Volatility | SMA20 + 2σ |
| Bollinger Middle | Volatility | SMA 20 |
| Bollinger Lower | Volatility | SMA20 - 2σ |
| SMA 20 | Trend | 20-day simple moving average |
| SMA 50 | Trend | 50-day simple moving average |
| SMA 200 | Trend | 200-day simple moving average |
| EMA 12 | Trend | 12-day exponential moving average |
| EMA 26 | Trend | 26-day exponential moving average |

---

## 🧪 Results

### Model comparison (about 5 years of data, binary BUY/SELL)

| Model | Accuracy |
|---|---|
| Logistic Regression | 51% |
| XGBoost (basic) | 57% |
| **XGBoost (Optuna-tuned, 50 trials)** | **58%** (production model) |
| LSTM (60 timesteps) | 53% |
| Ensemble (XGBoost + LSTM) | 54% |

Random guessing on a binary task is 50%, so these are modest edges, which is typical for noisy market data. SHAP analysis showed the MACD family (especially MACD signal) as the most influential features.

### Backtest (BTC-USD, about 5 years, $10,000 starting capital)

| Metric | Value |
|---|---|
| Total return | 21.81% |
| Sharpe ratio | 0.42 |
| Max drawdown | 9.54% |
| Win rate | 51.91% |
| Total trades | 262 |

Settings: 57% confidence threshold, 15% position size, stop loss -2%, take profit +3%, 0.1% commission.

### Drift monitoring

Evidently compared 2021-2024 (reference) against 2024-2026 (current) AAPL features. 11 of 12 features drifted, which is expected for price-level features such as SMAs and Bollinger Bands. Drift detection is the trigger for weekly retraining in the Prefect maintenance flow.

---

## 🛡️ Risk Management

- Trade only when model confidence exceeds the threshold
- Position size from Kelly Criterion, capped per trade
- Stop loss and take profit on open positions
- Stop trading on large portfolio drawdown; limit concurrent positions

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker Desktop
- Git
- WSL2 (Windows users)

### Setup

1. Clone the repository:
```
git clone https://github.com/Adithya-Venkataraman/algo-trading-platform.git
cd algo-trading-platform
```
2. Create a virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Start Docker containers (TimescaleDB, Redpanda, Grafana):
```
docker-compose up -d
docker ps
```
5. Create a `.env` file for paper trading (never commit this file):
```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```
6. Load historical data and compute features:
```
python -m data.ingestion.fetcher
python -m data.features.feature_pipeline
```
7. Train models (logged to MLflow):
```
python -m models.training.train
mlflow ui
```
8. Backtest, generate signals, paper trade:
```
python -m backtesting.backtest
python -m trading.signal_generator
python -m trading.paper_trader
```
9. Drift detection and automation:
```
python -m monitoring.drift_detector
python -m orchestration.prefect_flows.trading_pipeline
```
10. Real-time streaming (two terminals):

Terminal 1 - Producer:
```
python -m streaming.producer
```
Terminal 2 - Consumer:
```
python -m streaming.consumer
```
11. API and dashboard:
```
uvicorn api.main:app --port 8000
streamlit run api/streamlit_app.py
```

Grafana runs via docker-compose at http://localhost:3000, and the API docs are at http://localhost:8000/docs.

---

## 🗓️ Build Progress

| Phase | Status | Description |
|---|---|---|
| Data Foundation | ✅ | Docker, TimescaleDB hypertable, multi-ticker ingestion |
| Feature Engineering | ✅ | RSI, MACD, Bollinger Bands, SMA, EMA |
| Kafka Streaming | ✅ | Producer/Consumer pipeline, real-time data flow |
| ML Models | ✅ | LogReg, XGBoost, Optuna tuning, SHAP, MLflow tracking |
| LSTM + Ensemble | ✅ | Sequence model and weighted ensemble (XGBoost remains best) |
| Signal Generation | ✅ | Confidence filter, Kelly sizing, risk rules |
| Backtesting | ✅ | Backtrader, performance metrics |
| Paper Trading | ✅ | Alpaca API order execution |
| Monitoring | ✅ | Evidently AI drift detection, Grafana dashboards |
| Orchestration | ✅ | Prefect daily and weekly flows |
| FastAPI + Streamlit | ✅ | Runs locally |
| Public cloud deployment | 🔨 | Hosted database + Streamlit Cloud in progress |
| CI/CD | ⏳ | Planned |

---

## ⚠️ Limitations

- About 5 years of daily data; results are sensitive to the market regime
- The backtest uses signals over the full period, which includes the data the model was trained on, so it is optimistic. A true out-of-sample test and live paper-trading results are the real validation
- The strategy did not beat buy-and-hold on raw return for BTC-USD; its advantage is lower drawdown
- Commission is modelled but slippage is simplified
- For research and education only; not financial advice

---

## 👨‍💻 Author

**Adithya Venkataraman**
- GitHub: [@Adithya-Venkataraman](https://github.com/Adithya-Venkataraman)

---

*DRIFT — Because markets drift, and so do models. We track both.* 🌊
