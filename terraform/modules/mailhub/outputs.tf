output "id" {
  description = "ID of instance"
  value       = aws_instance.mailhub.id
}

output "arn" {
  description = "ARN of instance"
  value       = aws_instance.mailhub.arn
}

output "availability_zone" {
  description = "Availability zones of instance"
  value       = aws_instance.mailhub.availability_zone
}

output "key_name" {
  description = "Key names of instance"
  value       = aws_instance.mailhub.key_name
}

output "public_dns" {
  description = "Public DNS names assigned to the instance"
  value       = aws_instance.mailhub.public_dns
}

output "private_ip" {
  description = "Private IP address assigned to the instance"
  value       = aws_instance.mailhub.private_ip
}

output "security_groups" {
  description = "List of associated security groups of instance"
  value       = aws_instance.mailhub.security_groups
}