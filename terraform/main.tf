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