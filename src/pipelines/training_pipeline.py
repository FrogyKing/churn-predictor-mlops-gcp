
from kfp import dsl
from kfp import compiler
from google_cloud_pipeline_components.v1.model import ModelUploadOp
from google_cloud_pipeline_components.v1.custom_job import CustomTrainingJobOp
from google_cloud_pipeline_components.types import artifact_types

@dsl.pipeline(
    name="churn-prediction-pipeline",
    description="End-to-end churn prediction pipeline",
    pipeline_root="gs://YOUR_BUCKET_NAME/pipeline_root/" # Placeholder, overridden at runtime
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
    # Create an UnmanagedContainerModel artifact that points to the model location
    # and defines the serving image.
    unmanaged_model_importer = dsl.importer(
        artifact_uri=f"gs://{output_bucket}/model_output/",
        artifact_class=artifact_types.UnmanagedContainerModel,
        metadata={
            "containerSpec": {
                "imageUri": "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"
            }
        }
    ).after(train_task)

    model_upload = ModelUploadOp(
        project=project_id,
        display_name="churn-prediction-model",
        unmanaged_container_model=unmanaged_model_importer.output
    ).after(unmanaged_model_importer)


if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path="churn_pipeline.json"
    )

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Submit the pipeline to Vertex AI")
    parser.add_argument("--project_id", type=str, required=True)
    parser.add_argument("--region", type=str, default="us-central1")
    parser.add_argument("--bucket", type=str, required=True, help="GCS Bucket for pipeline root")
    parser.add_argument("--image_uri", type=str, required=True, help="Docker image URI")
    
    args = parser.parse_args()

    if args.run:
        from google.cloud import aiplatform
        
        aiplatform.init(project=args.project_id, location=args.region)
        
        job = aiplatform.PipelineJob(
            display_name="churn-prediction-pipeline-job",
            template_path="churn_pipeline.json",
            pipeline_root=f"gs://{args.bucket}/pipeline_root/",
            parameter_values={
                "project_id": args.project_id,
                "region": args.region,
                "input_dataset": "churn_production",
                "input_table": "raw_data",
                "output_bucket": args.bucket,
                "container_image_uri": args.image_uri
            }
        )
        
        job.submit()
        print(f"Pipeline submitted. View it here: {job._dashboard_uri()}")
