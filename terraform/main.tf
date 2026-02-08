resource "google_firestore_database" "firestore_db" {
    project     = var.project_id
    name        = "(default)"
    location_id = "eur3"
    type = "FIRESTORE_NATIVE"
}

resource "google_pubsub_topic" "pubsub_topic" {
    name = "radar-topic"
    project = var.project_id
}

resource "google_pubsub_subscription" "pubsub_subscription" {
    name = "${google_pubsub_topic.pubsub_topic.name}-sub"
    topic = google_pubsub_topic.pubsub_topic.name
    project = var.project_id
}

resource "google_bigquery_dataset" "bq_dataset" {
    dataset_id = "radar_dataset"
    project = var.project_id
}

resource "google_bigquery_table" "bq_table" {
    dataset_id = google_bigquery_dataset.bq_dataset.dataset_id
    table_id = "speed_violations"
    project = var.project_id
    schema = <<EOF
[
    {
    "name": "license_plate",
    "type": "STRING",
    "mode": "REQUIRED"
    },
    {
    "name": "speed",
    "type": "FLOAT",
    "mode": "REQUIRED"
    },
    {
    "name": "limit",
    "type": "FLOAT",
    "mode": "REQUIRED"
    },
    {
    "name": "excess_percentage",
    "type": "FLOAT",
    "mode": "REQUIRED"
    },
    {
    "name": "fine_amount",
    "type": "FLOAT",
    "mode": "REQUIRED"
    },
    {
    "name": "points_lost",
    "type": "FLOAT",
    "mode": "REQUIRED"
    },
    {
    "name": "severity",
    "type": "STRING",
    "mode": "REQUIRED"
    }
]
EOF
}

resource "google_pubsub_topic" "pubsub_topic_notifications" {
    name = "driver-notifications-topic"
    project = var.project_id
}

resource "google_pubsub_subscription" "pubsub_subscription_notifications" {
    name = "${google_pubsub_topic.pubsub_topic_notifications.name}-sub"
    topic = google_pubsub_topic.pubsub_topic_notifications.name
    project = var.project_id
}

resource "google_storage_bucket" "bucket_function" {
    name = "bucket-for-function-${var.project_id}"
    location = var.region
}

resource "google_storage_bucket_object" "upload_zip" {
    name = "function.zip"
    source = "../function/function.zip"
    bucket = google_storage_bucket.bucket_function.name
}

resource "google_cloudfunctions2_function" "send_notification_function" {
    name = "send-notification-function"
    location = var.region
    build_config {
        runtime = "python310"
        entry_point = "driver_notification" 
        source {
        storage_source {
            bucket = google_storage_bucket.bucket_function.name
            object = google_storage_bucket_object.upload_zip.name
        }
        }
    }
    service_config {
        max_instance_count = 1
        available_memory = "256M"
        timeout_seconds = 60
    }
    event_trigger {
        trigger_region = var.region
        event_type = "google.cloud.pubsub.topic.v1.messagePublished"
        pubsub_topic = "projects/${var.project_id}/topics/${google_pubsub_topic.pubsub_topic_notifications.name}"
        retry_policy = "RETRY_POLICY_DO_NOT_RETRY"
    }
    }