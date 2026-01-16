
import argparse
import logging
import os
import joblib
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, recall_score, precision_score
from google.cloud import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model(train_file, test_file, model_output_gcs_path):
    """
    Trains an XGBoost model and uploads it to GCS.
    """
    logger.info(f"Loading data from {train_file} and {test_file}")
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)

    X_train = train_df.drop('Churn', axis=1)
    y_train = train_df['Churn']
    X_test = test_df.drop('Churn', axis=1)
    y_test = test_df['Churn']

    logger.info("Starting training...")
    model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    rec = recall_score(y_test, preds)
    prec = precision_score(y_test, preds)
    
    logger.info(f"Metrics: Accuracy={acc}, Recall={rec}, Precision={prec}")
    
    # Save model locally
    model_filename = 'model.joblib'
    joblib.dump(model, model_filename)

    # Upload to GCS
    # model_output_gcs_path should be a folder, e.g., gs://bucket/model/
    if not model_output_gcs_path.endswith('/'):
         model_output_gcs_path += '/'
    
    bucket_name = model_output_gcs_path.split('/')[2]
    blob_path = '/'.join(model_output_gcs_path.split('/')[3:]) + model_filename

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.upload_from_filename(model_filename)
    
    logger.info(f"Model saved to gs://{bucket_name}/{blob_path}")

    # Use Vertex AI SDK to log metrics (Optional but recommended, not included here to keep it simple script-wise, 
    # but in real MLOps we would call aiplatform.log_metrics)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_file", type=str, required=True)
    parser.add_argument("--test_file", type=str, required=True)
    parser.add_argument("--model_output", type=str, required=True)
    
    args = parser.parse_args()
    
    train_model(args.train_file, args.test_file, args.model_output)
