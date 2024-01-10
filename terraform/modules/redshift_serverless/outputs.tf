output "workgroup_address" {
  value = aws_redshiftserverless_workgroup.serverless.endpoint[0].address
}
output "workgroup_port" {
  value = aws_redshiftserverless_workgroup.serverless.endpoint[0].port
}
output "sg_id" {
  value = aws_security_group.serverless.id
}
