# DRIFT — Algorithmic Trading Platform 🚀
A production-grade algorithmic trading platform with real-time data streaming, ML-powered signal generation, automated backtesting, and cloud deployment.

📌 Overview
DRIFT is a self-running algorithmic trading system that:

Ingests real-time and historical market data for 5 tickers
Engineers 14 technical indicators as ML features
Streams live prices via Apache Kafka pipeline
Trains XGBoost + LSTM models to predict buy/sell signals (in progress)
Validates strategies via automated backtesting (upcoming)
Executes paper trades via Alpaca API (upcoming)
Monitors model health with Evidently AI + Grafana (upcoming)
Deploys on AWS EC2 with full CI/CD (upcoming)

🏗️ Architecture
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
   RSI │ MACD │ Bollinger Bands
   SMA │ EMA  │ Volume Signals
            │
            ▼
    ML Models (XGBoost + LSTM)     ← in progress
            │
            ▼
       Backtesting Engine           ← upcoming
       (Backtrader + Pyfolio)
            │
            ▼
    Paper Trading (Alpaca API)      ← upcoming
            │
            ▼
  Monitoring (Evidently + Grafana)  ← upcoming
            │
            ▼
     AWS EC2 + CI/CD Pipeline       ← upcoming


🗂️ Project Structure
drift/
├── data/
│   ├── ingestion/
│   │   └── fetcher.py          # yfinance data ingestion pipeline
│   ├── features/
│   │   └── indicators.py       # RSI, MACD, Bollinger Bands, SMA, EMA
│   ├── feast/                  # Feature store config (upcoming)
│   └── db_connection.py        # Reusable TimescaleDB connection
│
├── models/
│   ├── training/               # XGBoost + LSTM training (upcoming)
│   ├── evaluation/             # Walk-forward validation (upcoming)
│   └── registry/               # MLflow model promotion (upcoming)
│
├── streaming/
│   ├── producer.py             # Kafka producer (live price → Kafka)
│   └── consumer.py             # Kafka consumer (Kafka → TimescaleDB)
│
├── backtesting/                # Backtrader integration (upcoming)
├── trading/
│   └── execution/              # Alpaca paper trading (upcoming)
├── api/                        # FastAPI signal serving (upcoming)
├── monitoring/                 # Evidently AI + Grafana (upcoming)
├── orchestration/
│   └── prefect_flows/          # Automated pipelines (upcoming)
├── tests/
├── docs/
├── docker-compose.yml          # TimescaleDB + Redpanda containers
├── requirements.txt
└── README.md

⚙️ Tech Stack
| Layer | Technology |
|---|---|
| Market Data | yfinance, Alpaca API |
| Database | TimescaleDB (PostgreSQL hypertable) |
| Streaming | Apache Kafka (Redpanda) |
| Feature Store | Feast *(upcoming)* |
| ML Models | XGBoost, LSTM *(upcoming)* |
| Experiment Tracking | MLflow *(upcoming)* |
| Backtesting | Backtrader + Pyfolio *(upcoming)* |
| Model Serving | FastAPI *(upcoming)* |
| Orchestration | Prefect *(upcoming)* |
| Monitoring | Evidently AI + Grafana *(upcoming)* |
| Containerization | Docker + Docker Compose |
| Cloud | AWS EC2 *(upcoming)* |
| CI/CD | GitHub Actions *(upcoming)* |
| Language | Python 3.12, SQL |

📊 Data Pipeline
Tickers Tracked:
AAPL  →  Apple Inc
MSFT  →  Microsoft
GOOG  →  Google (Alphabet)
AMZN  →  Amazon
BTC-USD → Bitcoin

Database Schema:
stock_prices (hypertable):
time      TIMESTAMPTZ NOT NULL
symbol    VARCHAR(10) NOT NULL
open      DOUBLE PRECISION
high      DOUBLE PRECISION
low       DOUBLE PRECISION
close     DOUBLE PRECISION
volume    BIGINT

stock_features (hypertable):
time        TIMESTAMPTZ NOT NULL
symbol      VARCHAR(10) NOT NULL
rsi         DOUBLE PRECISION      -- Relative Strength Index (14)
macd        DOUBLE PRECISION      -- MACD Line
macd_signal DOUBLE PRECISION      -- Signal Line (9)
macd_hist   DOUBLE PRECISION      -- MACD Histogram
bb_upper    DOUBLE PRECISION      -- Bollinger Band Upper
bb_middle   DOUBLE PRECISION      -- Bollinger Band Middle (SMA 20)
bb_lower    DOUBLE PRECISION      -- Bollinger Band Lower
sma_20      DOUBLE PRECISION      -- Simple Moving Average 20
sma_50      DOUBLE PRECISION      -- Simple Moving Average 50
sma_200     DOUBLE PRECISION      -- Simple Moving Average 200
ema_12      DOUBLE PRECISION      -- Exponential Moving Average 12
ema_26      DOUBLE PRECISION      -- Exponential Moving Average 26

🔄 Real-Time Streaming Pipeline
Alpaca WebSocket
      ↓
producer.py (fetches live price every second)
      ↓
Apache Kafka / Redpanda (topic: stock-prices)
      ↓
consumer.py (reads from Kafka)
      ↓
TimescaleDB (stock_prices hypertable)

🚀 Getting Started
Prerequisites:
Python 3.12+
Docker Desktop
Git
WSL2 (Windows users)

Setup:
1. Clone the repository:
git clone https://github.com/Adithya-Venkataraman/algo-trading-platform.git
cd algo-trading-platform

2. Create virtual environment:
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

3. Install dependencies:
pip install -r requirements.txt

4.Start Docker containers:
docker-compose up -d

5. Verify containers are running:
docker ps
# Should show: timescaledb + redpanda

6. Run historical data ingestion:
python -m data.ingestion.fetcher

7. Start real-time streaming (two terminals):
# Terminal 1 - Producer
python -m streaming.producer

# Terminal 2 - Consumer
python -m streaming.consumer

📈 Features Engineered
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

🗓️Build Progress
Week 1  ✅  Data Foundation
            → Project structure, Docker setup
            → TimescaleDB hypertable
            → Multi-ticker data ingestion
            → Error handling + duplicate prevention

Week 2  ✅  Feature Engineering
            → RSI, MACD, Bollinger Bands
            → SMA (20/50/200), EMA (12/26)
            → stock_features hypertable

Week 3  ✅  Kafka Streaming
            → Redpanda setup in Docker
            → Producer: live prices → Kafka
            → Consumer: Kafka → TimescaleDB
            → Real-time pipeline running

Week 4  ⏳  ML Models
            → XGBoost baseline
            → LSTM sequence model
            → MLflow experiment tracking

Week 5  ⏳  Advanced ML
            → Ensemble (XGBoost + LSTM)
            → Hyperparameter tuning (Optuna)
            → SHAP explainability

Week 6  ⏳  Signal Generation
            → Buy/sell/flat signal logic
            → Kelly Criterion position sizing
            → Risk management rules

Week 7  ⏳  Backtesting
            → Backtrader integration
            → Walk-forward validation
            → Sharpe, Sortino, Max Drawdown

Week 8  ⏳  Paper Trading
            → Alpaca API integration
            → Live order execution
            → P&L tracking

Week 9  ⏳  Monitoring
            → Evidently AI drift detection
            → Grafana dashboards
            → Auto-retraining pipeline

Week 10 ⏳  Orchestration
            → Prefect DAGs
            → Automated scheduling

Week 11 ⏳  Cloud Deployment
            → AWS EC2 deployment
            → Nginx reverse proxy
            → GitHub Actions CI/CD

Week 12 ⏳  Polish
            → Documentation
            → Architecture diagrams
            → End-to-end testing

👨‍💻 Author
Adithya Venkataraman

GitHub: @Adithya-Venkataraman

DRIFT — Because markets drift, and so do models. We track both. 🌊


