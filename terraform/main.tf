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