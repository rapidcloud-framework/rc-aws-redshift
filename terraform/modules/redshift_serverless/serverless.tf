resource "aws_redshiftserverless_namespace" "serverless" {
  namespace_name      = var.namespace_name
  admin_username      = var.admin_username
  admin_user_password = var.admin_password
  db_name             = var.database_name
  iam_roles           = concat([aws_iam_role.serverless.arn], var.iam_roles)
  kms_key_id          = var.kms_key_id
  log_exports         = var.log_exports
  tags                = merge({ "Name" = var.namespace_name }, local.rc_tags, var.tags)
  lifecycle {
    ignore_changes = [
      iam_roles
    ]
  }
}

resource "aws_redshiftserverless_workgroup" "serverless" {
  namespace_name       = aws_redshiftserverless_namespace.serverless.id
  workgroup_name       = var.workgroup_name
  base_capacity        = var.base_capacity
  enhanced_vpc_routing = true
  security_group_ids   = [aws_security_group.serverless.id]
  subnet_ids           = var.subnets
  # tags                 = merge(local.rc_tags, var.tags)
  tags = merge({ "Name" = var.workgroup_name }, local.rc_tags, var.tags)

  # needs newer provider
  # config_parameter {
  #   parameter_key   = "datestyle"
  #   parameter_value = var.config_param_datestyle
  # }
  # config_parameter {
  #   parameter_key   = "enable_user_activity_logging"
  #   parameter_value = var.config_param_enable_user_activity_logging
  # }
  # config_parameter {
  #   parameter_key   = "query_group"
  #   parameter_value = var.config_param_query_group
  # }
  # config_parameter {
  #   parameter_key   = "search_path"
  #   parameter_value = var.config_param_search_path
  # }
  # config_parameter {
  #   parameter_key   = "max_query_execution_time"
  #   parameter_value = var.config_param_max_query_execution_time
  # }
  # config_parameter {
  #   parameter_key   = "auto_mv"
  #   parameter_value = var.config_param_auto_mv
  # }
  # config_parameter {
  #   parameter_key   = "enable_case_sensitive_identifier"
  #   parameter_value = var.config_param_enable_case_sensitive_identifier
  # }
}


resource "aws_redshiftserverless_usage_limit" "serverless" {
  count         = var.set_usage_limit == "true" ? 1 : 0
  resource_arn  = aws_redshiftserverless_workgroup.serverless.arn
  usage_type    = var.usage_type
  amount        = var.max_capacity
  period        = var.usage_period
  breach_action = var.breach_action
}

# resource "aws_redshiftserverless_endpoint_access" "serverless" {
#   endpoint_name          = var.namespace_name
#   workgroup_name         = aws_redshiftserverless_workgroup.serverless.id
#   vpc_security_group_ids = [aws_security_group.serverless.id]
#   subnet_ids             = var.subnets
# }
# 
