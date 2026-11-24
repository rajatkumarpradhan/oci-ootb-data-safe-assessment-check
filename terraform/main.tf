# TEMPLATE ONLY - NOT plan/apply validated against a live tenancy.
# Wiring: OCI Data Safe assesses the target database; an OCI Events rule
# matches the assessment-end event and publishes to OCI Notifications.
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

variable "compartment_ocid" {
  type        = string
  description = "OCID of the compartment that owns the target and topic"
}

variable "database_ocid" {
  type        = string
  description = "OCID of the target database (Autonomous DB or DB system)"
}

variable "alert_email" {
  type        = string
  description = "Email address subscribed to assessment completion notices"
}

# 1. Built-in service: OCI Data Safe target registration.
resource "oci_data_safe_target_database" "target" {
  compartment_id = var.compartment_ocid
  display_name   = "adb-prod-orders"
  database_details {
    database_type = "AUTONOMOUS_DATABASE"
    # autonomous_database_id = var.database_ocid  # field name per provider docs
  }
  description = "Weekly security assessment target"
}

# 2. Built-in service: OCI Notifications topic + subscription.
resource "oci_ons_notification_topic" "data_safe" {
  compartment_id = var.compartment_ocid
  name           = "data-safe-assessment-events"
}

resource "oci_ons_subscription" "email" {
  compartment_id = var.compartment_ocid
  topic_id       = oci_ons_notification_topic.data_safe.id
  protocol       = "EMAIL"
  endpoint       = var.alert_email
}

# 3. Built-in service: OCI Events rule matching Data Safe assessment-end.
resource "oci_events_rule" "assessment_end" {
  compartment_id = var.compartment_ocid
  display_name   = "data-safe-assessment-end"
  condition      = "{\"eventType\": [\"com.oraclecloud.datasafe.securityassessmentend\"]}"
  is_enabled     = true

  actions {
    actions {
      action_type = "ONS"
      is_enabled  = true
      topic_id    = oci_ons_notification_topic.data_safe.id
    }
  }
}
