import pandas as pd
import mlflow
import mlflow.sklearn
from data.db_connection import get_connection
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score,classification_report
from sklearn.linear_model import LogisticRegression
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
