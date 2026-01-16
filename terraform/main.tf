terraform {
  required_version = ">= 1.0"
  # backend "gcs" {
  #   bucket  = "projectss-luis-tf-state"
  #   prefix  = "churn-predictor/state"
  # }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

# 0. Terraform State Bucket (Chicken & Egg problem solution)
resource "google_storage_bucket" "tf_state_bucket" {
  name          = "${var.project_id}-tf-state"
  location      = var.region
  force_destroy = true
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com"
  ])
  service = each.key
  disable_on_destroy = false
}

# 2. Artifact Registry for Docker Images
resource "google_artifact_registry_repository" "churn_repo" {
  location      = var.region
  repository_id = "churn-predictor-repo"
  description   = "Docker repository for Churn Prediction Pipeline"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# 3. BigQuery Dataset
resource "google_bigquery_dataset" "churn_dataset" {
  dataset_id                  = "churn_production"
  friendly_name               = "Churn Prediction Production"
  description                 = "Production dataset for Churn Prediction metadata and tables"
  location                    = var.region
  default_table_expiration_ms = null

  labels = {
    env = "production"
  }
  depends_on = [google_project_service.apis]
}

# 4. GCS Bucket for Vertex AI Artifacts (staging)
resource "google_storage_bucket" "vertex_bucket" {
  name          = "${var.project_id}-vertex-staging"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
  depends_on = [google_project_service.apis]
}

# 5. Service Account for Pipelines
resource "google_service_account" "pipeline_sa" {
  account_id   = "churn-pipeline-sa"
  display_name = "Vertex AI Pipeline Service Account"
}

# Grant necessary roles to the Service Account
resource "google_project_iam_member" "pipeline_sa_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/storage.objectAdmin",
    "roles/artifactregistry.reader"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.pipeline_sa.email}"
}
