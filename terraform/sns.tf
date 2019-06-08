# Create SNS topic for mailhub alerts/notifications

resource "aws_sns_topic" "mailhub_system" {
    name = "mailhub-system-alerts"
}