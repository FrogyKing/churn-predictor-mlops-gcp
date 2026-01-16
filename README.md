# Churn Predictor MLOps on GCP

![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)

An end-to-end MLOps project for predicting customer churn using Vertex AI, BigQuery, and Terraform.

## Project Structure
- `terraform/`: Infrastructure as Code to provision GCP resources.
- `src/`: Source code for data pipelines and model training.
- `.github/workflows/`: CI/CD pipelines.

## Prerequisites
- Google Cloud Platform Account
- Terraform installed
- gcloud CLI installed

## Setup
1. **Infrastructure**:
   ```bash
   cd terraform
   terraform init
   terraform apply -var="project_id=YOUR_PROJECT_ID"
   ```

2. **Data Ingestion**:
   (Instructions to run the ingestion script will be added here)

## Architecture
- **Data Warehouse**: BigQuery
- **ML Platform**: Vertex AI
- **Orchestration**: Vertex AI Pipelines
