import argparse
import logging
import os
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_csv_to_bq(dataset_id, table_id, file_path, project_id):
    """Loads a CSV file into a BigQuery table."""
    client = bigquery.Client(project=project_id)
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
    )

    with open(file_path, "rb") as source_file:
        job = client.load_table_from_file(source_file, table_ref, job_config=job_config)

    logger.info(f"Starting job {job.job_id}")
    job.result()  # Waits for the job to complete.

    logger.info(f"Loaded {job.output_rows} rows into {dataset_id}.{table_id}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest CSV to BigQuery")
    parser.add_argument("--project_id", required=True, help="GCP Project ID")
    parser.add_argument("--dataset_id", required=True, help="BigQuery Dataset ID")
    parser.add_argument("--table_id", required=True, help="BigQuery Table ID")
    parser.add_argument("--file_path", required=True, help="Path to local CSV file")
    
    args = parser.parse_args()
    
    load_csv_to_bq(args.dataset_id, args.table_id, args.file_path, args.project_id)
