import sys
sys.path.append('/home/jingv/algo-trading-platform')
import pandas as pd
import json
from evidently import Report
from evidently.presets import DataDriftPreset, DataSummaryPreset
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://trading:trading123@localhost:5432/trading_db'
)

def get_reference_data():
    query = """
        SELECT rsi, macd, macd_signal, macd_hist,
               bb_upper, bb_middle, bb_lower,
               sma_20, sma_50, sma_200, ema_12, ema_26
        FROM stock_features
        WHERE symbol = 'AAPL'
        AND rsi IS NOT NULL
        AND sma_200 IS NOT NULL
        AND time < '2024-01-01'
        ORDER BY time ASC
    """
    return pd.read_sql(query, engine)

def get_current_data():
    query = """
        SELECT rsi, macd, macd_signal, macd_hist,
               bb_upper, bb_middle, bb_lower,
               sma_20, sma_50, sma_200, ema_12, ema_26
        FROM stock_features
        WHERE symbol = 'AAPL'
        AND rsi IS NOT NULL
        AND sma_200 IS NOT NULL
        AND time >= '2024-01-01'
        ORDER BY time ASC
    """
    return pd.read_sql(query, engine)

def run_drift_detection():
    print("Fetching reference data (2021-2024)...")
    reference_data = get_reference_data()

    print("Fetching current data (2024-2026)...")
    current_data = get_current_data()

    print(f"Reference: {len(reference_data)} rows")
    print(f"Current:   {len(current_data)} rows")

    # run report
    report = Report(metrics=[
        DataDriftPreset(),
        DataSummaryPreset()
    ])

    result = report.run(
        reference_data=reference_data,
        current_data=current_data
    )

    # save reports
    result.save_html('monitoring/drift_report.html')
    result.save_json('monitoring/drift_report.json')
    print("Reports saved! ✅")

    # analyze drift
    with open('monitoring/drift_report.json', 'r') as f:
        report_dict = json.load(f)

    print("\n=== DRIFT ANALYSIS ===")
    drift_detected = False

    for metric in report_dict.get('metrics', []):
        metric_name = metric.get('metric_name', '')
        value = metric.get('value', {})

        # check drifted columns count
        if 'DriftedColumnsCount' in metric_name:
            count = value.get('count', 0)
            share = value.get('share', 0)
            print(f"Drifted features: {int(count)}/12 ({share*100:.1f}%)")

            if share > 0.5:
                drift_detected = True
                print("⚠️  SIGNIFICANT DRIFT DETECTED!")
                print("⚠️  Model needs retraining!")
            else:
                print("✅ Drift within acceptable range")

        # check individual feature drift
        if 'ColumnDrift' in metric_name:
            column = metric.get('config', {}).get('column_name', '')
            drifted = value.get('drift_detected', False)
            score = value.get('drift_score', 0)
            status = "⚠️ DRIFT" if drifted else "✅ OK"
            print(f"  {column}: {status} (score={score:.4f})")

    return drift_detected

if __name__ == "__main__":
    drift = run_drift_detection()
    print(f"\nFinal status: {'DRIFT DETECTED ⚠️' if drift else 'HEALTHY ✅'}")