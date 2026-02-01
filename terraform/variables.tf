variable "project_id" {
    type = string
    description = "The id of the GCP project in which you will work"
}

variable "region" {
    type = string
    description = "The region where you will deploy your compute engine"
}

variable "zone" {
    type = string
    description = "The zone where you will work on GCP"
}