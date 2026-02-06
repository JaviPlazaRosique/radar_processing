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