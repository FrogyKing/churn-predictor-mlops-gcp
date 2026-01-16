
import argparse
import logging
import pandas as pd
from google.cloud import bigquery
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preprocess_data(project_id, input_dataset, input_table, output_bucket, output_prefix):
    """
    Reads data from BQ, performs preprocessing, and saves train/test sets to GCS.
    """
    client = bigquery.Client(project=project_id)
    query = f"SELECT * FROM `{project_id}.{input_dataset}.{input_table}`"
    
    logger.info("Reading data from BigQuery...")
    df = client.query(query).to_dataframe()
    
    # 1. Basic Cleaning
    # Drop CustomerID as it's not a feature
    if 'customerID' in df.columns:
        df = df.drop(columns=['customerID'])
    
    # TotalCharges is often read as object due to spaces. Force numeric.
    if 'TotalCharges' in df.columns:
        df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
        df['TotalCharges'] = df['TotalCharges'].fillna(0)
    
    # Encode target 'Churn'
    if 'Churn' in df.columns:
        df['Churn'] = df['Churn'].apply(lambda x: 1 if x == 'Yes' else 0)

    # Simple One-Hot Encoding for categorical variables
    df = pd.get_dummies(df, drop_first=True)
    
    # 2. Split
    train, test = train_test_split(df, test_size=0.2, random_state=42)
    
    # 3. Save to GCS
    # Ensure bucket path ends with /
    if not output_prefix.endswith('/'):
        output_prefix += '/'

    train_path = f"gs://{output_bucket}/{output_prefix}train.csv"
    test_path = f"gs://{output_bucket}/{output_prefix}test.csv"
    
    logger.info(f"Saving training data to {train_path}")
    train.to_csv(train_path, index=False)
    
    logger.info(f"Saving test data to {test_path}")
    test.to_csv(test_path, index=False)
    
    print(f"Preprocessing complete. Train: {train.shape}, Test: {test.shape}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project_id", type=str, required=True)
    parser.add_argument("--input_dataset", type=str, required=True)
    parser.add_argument("--input_table", type=str, required=True)
    parser.add_argument("--output_bucket", type=str, required=True)
    parser.add_argument("--output_prefix", type=str, default="data/processed/")
    
    args = parser.parse_args()
    
    preprocess_data(args.project_id, args.input_dataset, args.input_table, args.output_bucket, args.output_prefix)
