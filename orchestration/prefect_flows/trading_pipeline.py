import sys
sys.path.append('/home/jingv/algo-trading-platform')

from prefect import flow, task
from prefect.logging import get_run_logger
import subprocess

# ── TASKS ──

@task(retries=3, retry_delay_seconds=60)
def fetch_market_data():
    logger = get_run_logger()
    logger.info("Fetching market data...")
    subprocess.run([
        'python', '-m', 'data.ingestion.fetcher'
    ], check=True)
    logger.info("Market data fetched! ✅")

@task(retries=3, retry_delay_seconds=60)
def calculate_features():
    logger = get_run_logger()
    logger.info("Calculating features...")
    subprocess.run([
        'python', '-m', 'data.features.feature_pipeline'
    ], check=True)
    logger.info("Features calculated! ✅")

@task(retries=2, retry_delay_seconds=30)
def run_drift_detection():
    logger = get_run_logger()
    logger.info("Running drift detection...")
    result = subprocess.run([
        'python', '-m', 'monitoring.drift_detector'
    ], capture_output=True, text=True)
    
    drift_detected = 'DRIFT DETECTED' in result.stdout
    logger.info(f"Drift detected: {drift_detected}")
    return drift_detected

@task(retries=2, retry_delay_seconds=60)
def retrain_model():
    logger = get_run_logger()
    logger.info("Retraining model...")
    subprocess.run([
        'python', '-m', 'models.training.train'
    ], check=True)
    logger.info("Model retrained! ✅")

@task(retries=2, retry_delay_seconds=30)
def run_paper_trading():
    logger = get_run_logger()
    logger.info("Running paper trading...")
    subprocess.run([
        'python', '-m', 'trading.paper_trader'
    ], check=True)
    logger.info("Paper trading complete! ✅")

# ── DAILY FLOW ──

@flow(name="DRIFT Daily Pipeline")
def daily_pipeline():
    logger = get_run_logger()
    logger.info("Starting DRIFT daily pipeline...")
    
    # step 1: fetch data
    fetch_market_data()
    
    # step 2: calculate features
    calculate_features()
    
    # step 3: run paper trading
    run_paper_trading()
    
    logger.info("Daily pipeline complete! ✅")

# ── WEEKLY FLOW ──

@flow(name="DRIFT Weekly Maintenance")
def weekly_maintenance():
    logger = get_run_logger()
    logger.info("Starting weekly maintenance...")
    
    # step 1: check drift
    drift = run_drift_detection()
    
    # step 2: retrain if drift detected
    if drift:
        logger.info("Drift detected! Retraining...")
        retrain_model()
        logger.info("Model retrained and deployed! ✅")
    else:
        logger.info("No drift. Model is healthy! ✅")
    
    logger.info("Weekly maintenance complete! ✅")

if __name__ == "__main__":
    # run daily pipeline
    print("Running daily pipeline...")
    daily_pipeline()
    
    print("\nRunning weekly maintenance...")
    weekly_maintenance()