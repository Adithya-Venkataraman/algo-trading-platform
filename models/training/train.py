import pandas as pd
import optuna
import shap
import mlflow
import random
import mlflow.sklearn
import xgboost as xgb
import matplotlib.pyplot as plt
from collections import Counter
from data.db_connection import get_connection
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score,classification_report
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

conn=get_connection()
query="SELECT * from stock_features order by time ASC"
df=pd.read_sql(query,conn)
print(df.shape)
print(df.columns.tolist())
print(df.head())
# fetch close prices from stock_prices table
price_query = "SELECT time, symbol, close FROM stock_prices ORDER BY time ASC"
prices_df = pd.read_sql(price_query, conn)

# calculate next day return per ticker
prices_df['next_return'] = prices_df.groupby('symbol')['close'].pct_change(1).shift(-1)

# create label
def create_label(return_val):
    if return_val > 0.002:    # >1% return
        return 1             # BUY
    elif return_val < -0.002: # <-1% return
        return -1            # SELL
    else:
        return 0             # FLAT

prices_df['label'] = prices_df['next_return'].apply(create_label)
print(prices_df['label'].value_counts())
# merging two dataframes in pandas
merged_df = pd.merge(df, prices_df[['time', 'symbol', 'label']], 
                     on=['time', 'symbol'], 
                     how='inner')

# drop NaN rows
merged_df = merged_df.dropna()
# remove FLAT class - binary classification only
merged_df = merged_df[merged_df['label'] != 0]

print("After removing FLAT:")
print(merged_df['label'].value_counts())

print(merged_df.shape)
print(merged_df['label'].value_counts())
feature_cols=[col for col in merged_df.columns
              if col not in ['time','symbol','label']]
X=merged_df[feature_cols]
y=merged_df['label']
print(X.shape)
print(y.shape)
print(feature_cols)
X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=0.2,train_size=0.8,random_state=42,shuffle=False)
print("Training samples:",X_train.shape)
print("Testing samples:",X_test.shape)

scaler=StandardScaler()
X_train_scaled=scaler.fit_transform(X_train)
X_test_scaled=scaler.transform(X_test)

#import model
model=LogisticRegression(class_weight='balanced',max_iter=1000,random_state=42)
model.fit(X_train_scaled,y_train)
print("Model training completed ✅")
y_pred=model.predict(X_test_scaled)
accuracy=accuracy_score(y_test,y_pred)
print(f"Accuracy:{accuracy:.4f}")
print(classification_report(y_test,y_pred))

#mlflow logging
mlflow.set_experiment("drift-trading")

with mlflow.start_run(run_name="logistic_regression"):
    # log parameters
    mlflow.log_param("model", "LogisticRegression")
    mlflow.log_param("threshold", 0.002)
    mlflow.log_param("test_size", 0.2)
    
    # train model (your existing code)
    model = LogisticRegression(
        class_weight='balanced',
        max_iter=1000,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)
    
    # evaluate
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    # log metrics
    mlflow.log_metric("accuracy", accuracy)
    
    # log model
    mlflow.sklearn.log_model(model, "model")
    
    print(f"Accuracy: {accuracy:.4f}")
    print(classification_report(y_test, y_pred))
    print("Run logged to MLflow! ✅")

with mlflow.start_run(run_name="xgboost"):
    mlflow.log_param("model", "XGBoost")
    mlflow.log_param("threshold", 0.002)
    
    # encode labels
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    y_test_encoded = le.transform(y_test)
    
    # train model
    model_xgb = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss',
        scale_pos_weight=3
    )
    sample_weights = compute_sample_weight(
    class_weight='balanced',
    y=y_train_encoded
    )

    model_xgb.fit(X_train_scaled, y_train_encoded, 
              sample_weight=sample_weights)
    # check class distribution
    print(Counter(y_train_encoded))
    
    # predict + decode
    y_pred_xgb = model_xgb.predict(X_test_scaled)
    y_pred_xgb_decoded = le.inverse_transform(y_pred_xgb)
    
    # evaluate
    accuracy_xgb = accuracy_score(y_test, y_pred_xgb_decoded)
    mlflow.log_metric("accuracy", accuracy_xgb)
    mlflow.xgboost.log_model(model_xgb, "model")
    
    print(f"XGBoost Accuracy: {accuracy_xgb:.4f}")
    print(classification_report(y_test, y_pred_xgb_decoded))



def objective(trial):
    # define search space
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'eval_metric': 'mlogloss',
        'random_state': 42
    }
    
    model = xgb.XGBClassifier(**params)
    
    sample_weights = compute_sample_weight(
        class_weight='balanced',
        y=y_train_encoded
    )
    
    model.fit(X_train_scaled, y_train_encoded,
              sample_weight=sample_weights)
    
    y_pred = model.predict(X_test_scaled)
    y_pred_decoded = le.inverse_transform(y_pred)
    
    return accuracy_score(y_test, y_pred_decoded)

# run optimization
study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)

print("Best params:", study.best_params)
print("Best accuracy:", study.best_value)

# ── MLflow RUN 3: XGBoost (tuned) ──
with mlflow.start_run(run_name="xgboost_tuned"):
    
    # log best params found by Optuna
    mlflow.log_params(study.best_params)
    mlflow.log_param("model", "XGBoost_tuned")
    
    # train with best params
    model_tuned = xgb.XGBClassifier(
        **study.best_params,        # ← best params from Optuna!
        eval_metric='mlogloss',
        random_state=42
    )
    
    sample_weights = compute_sample_weight(
        class_weight='balanced',
        y=y_train_encoded
    )
    
    model_tuned.fit(X_train_scaled, y_train_encoded,
                    sample_weight=sample_weights)
    
    y_pred_tuned = model_tuned.predict(X_test_scaled)
    y_pred_tuned_decoded = le.inverse_transform(y_pred_tuned)
    
    accuracy_tuned = accuracy_score(y_test, y_pred_tuned_decoded)
    mlflow.log_metric("accuracy", accuracy_tuned)
    mlflow.xgboost.log_model(model_tuned, "model")
    
    print(f"XGBoost Tuned Accuracy: {accuracy_tuned:.4f}")
    print(classification_report(y_test, y_pred_tuned_decoded))

# explain model predictions
explainer = shap.TreeExplainer(model_tuned)
shap_values = explainer.shap_values(
    pd.DataFrame(X_test_scaled, columns=feature_cols)
)
# log feature importance to MLflow
with mlflow.start_run(run_name="shap_analysis"):
    shap.summary_plot(
        shap_values, 
        pd.DataFrame(X_test_scaled, columns=feature_cols),
        show=False
    )
    plt.savefig("shap_summary.png")
    mlflow.log_artifact("shap_summary.png")
    print("SHAP analysis complete! ✅")

# create sequences function
def create_sequences(X, y, timesteps=10):
    Xs, ys = [], []
    for i in range(len(X) - timesteps):
        Xs.append(X[i:i+timesteps])
        ys.append(y[i+timesteps])
    return np.array(Xs), np.array(ys)

# create sequences
X_train_seq, y_train_seq = create_sequences(
    np.array(X_train_scaled), np.array(y_train_encoded),timesteps=60)
X_test_seq, y_test_seq = create_sequences(
    np.array(X_test_scaled), np.array(y_test_encoded),timesteps=60)

print("LSTM input shape:", X_train_seq.shape)
np.random.seed(42)
tf.random.set_seed(42)
random.seed(42)
# build model
model_lstm = Sequential([
    LSTM(64, return_sequences=True,
         input_shape=(10, X_train_seq.shape[2])),
    Dropout(0.2),
    LSTM(32, return_sequences=False),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(2, activation='softmax')
])

model_lstm.compile(
    optimizer='adam',
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# train with MLflow
with mlflow.start_run(run_name="lstm"):
    mlflow.log_param("model", "LSTM")
    mlflow.log_param("timesteps", 60)
    mlflow.log_param("epochs", 150) 
    mlflow.log_param("lstm_units", 64)
    
    history = model_lstm.fit(
        X_train_seq, y_train_seq,
        epochs=150,
        batch_size=32,
        validation_split=0.1,
        verbose=1
    )
    
    y_pred_lstm = np.argmax(
        model_lstm.predict(X_test_seq), axis=1)
    y_pred_decoded = le.inverse_transform(y_pred_lstm)
    y_test_decoded = le.inverse_transform(y_test_seq)
    
    accuracy_lstm = accuracy_score(y_test_decoded, y_pred_decoded)
    mlflow.log_metric("accuracy", accuracy_lstm)
    
    print(f"LSTM Accuracy: {accuracy_lstm:.4f}")
    print(classification_report(y_test_decoded, y_pred_decoded))
with mlflow.start_run(run_name="ensemble"):
    mlflow.log_param("model", "Ensemble_XGB_LSTM")
    
    # get XGBoost probabilities
    xgb_probs = model_tuned.predict_proba(X_test_scaled)
    
    # get LSTM probabilities
    # align test sets (LSTM has fewer rows due to sequences)
    lstm_probs = model_lstm.predict(X_test_seq)
    
    # align XGBoost predictions to match LSTM length
    xgb_probs_aligned = xgb_probs[-len(lstm_probs):]
    y_test_aligned = np.array(y_test_encoded)[-len(lstm_probs):]
    
    # average probabilities
    # XGBoost 60%, LSTM 40%
    ensemble_probs = (0.6 * xgb_probs_aligned + 0.4 * lstm_probs)
    
    # final prediction
    ensemble_pred = np.argmax(ensemble_probs, axis=1)
    ensemble_pred_decoded = le.inverse_transform(ensemble_pred)
    y_test_decoded = le.inverse_transform(y_test_aligned)
    
    accuracy_ensemble = accuracy_score(
        y_test_decoded, ensemble_pred_decoded)
    mlflow.log_metric("accuracy", accuracy_ensemble)
    
    print(f"Ensemble Accuracy: {accuracy_ensemble:.4f}")
    print(classification_report(
    y_test_decoded, ensemble_pred_decoded))

import joblib

# after training model_tuned, add:
joblib.dump(scaler, 'models/training/scaler.pkl')
joblib.dump(le, 'models/training/label_encoder.pkl')
model_tuned.save_model('models/training/xgboost_tuned.json')
print("Scaler, LabelEncoder and XGBoost model saved! ✅")

