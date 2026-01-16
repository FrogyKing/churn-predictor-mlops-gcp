
from kfp import dsl
from kfp.v2 import compiler
from google_cloud_pipeline_components.v1.model import ModelUploadOp
from google_cloud_pipeline_components.v1.custom_job import CustomTrainingJobOp

@dsl.pipeline(
    name="churn-prediction-pipeline",
    description="End-to-end churn prediction pipeline",
    pipeline_root="gs://YOUR_BUCKET_NAME/pipeline_root/" # Placeholder, needs to be dynamic or set at runtime
)
def pipeline(
    project_id: str,
    region: str,
    input_dataset: str,
    input_table: str,
    output_bucket: str,
    container_image_uri: str
):
    # Step 1: Preprocessing
    preprocess_task = CustomTrainingJobOp(
        project=project_id,
        location=region,
        display_name="preprocess-data",
        worker_pool_specs=[{
            "machine_spec": {"machine_type": "n1-standard-4"},
            "replica_count": 1,
            "container_spec": {
                "image_uri": container_image_uri,
                "command": ["python", "src/data/preprocess.py"],
                "args": [
                    "--project_id", project_id,
                    "--input_dataset", input_dataset,
                    "--input_table", input_table,
                    "--output_bucket", output_bucket
                ]
            }
        }]
    )

    # Step 2: Training
    # Depends on Preprocessing (implicitly via order, but explicit dependency if we pass data paths)
    # Here we assume the bucket paths are deterministic based on output_bucket argument
    train_task = CustomTrainingJobOp(
        project=project_id,
        location=region,
        display_name="train-model",
        worker_pool_specs=[{
            "machine_spec": {"machine_type": "n1-standard-4"},
            "replica_count": 1,
            "container_spec": {
                "image_uri": container_image_uri,
                "command": ["python", "src/model/train.py"],
                "args": [
                    "--train_file", f"gs://{output_bucket}/data/processed/train.csv",
                    "--test_file", f"gs://{output_bucket}/data/processed/test.csv",
                    "--model_output", f"gs://{output_bucket}/model_output/"
                ]
            }
        }]
    ).after(preprocess_task)

    # Step 3: Upload Model to Registry
    # This requires the model artifact to be in a specific format (e.g. model.joblib)
    # and the logic to pass the URI. 
    # For simplicity in this demo, we use the pre-built component pointing to the GCS path.
    model_upload = ModelUploadOp(
        project=project_id,
        display_name="churn-prediction-model",
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest",
        artifact_uri=f"gs://{output_bucket}/model_output/"
    ).after(train_task)

if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path="churn_pipeline.json"
    )
