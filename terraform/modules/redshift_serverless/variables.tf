variable "env" {}
variable "profile" {}
variable "workload" {}
variable "fqn" {}
variable "cmd_id" { default = "" }

variable "admin_username" {}
variable "admin_password" {}
variable "database_name" { default = "dev" }
variable "namespace_name" {}
variable "workgroup_name" {}
variable "base_capacity" { default = 32 }
variable "set_usage_limit" { default = false }
variable "usage_type" { default = "serverless-compute" }
variable "max_capacity" { default = 512 }
variable "usage_period" { default = "monthly" }
variable "breach_action" { default = "log" }

variable "subnets" { type = list(string) }
variable "tags" {
  type    = map(string)
  default = {}
}
variable "iam_roles" {
  type    = list(string)
  default = []
}
variable "vpc_id" {}
variable "allowed_cidr" {
  type    = list(string)
  default = []
}
# variable "availability_zone" {}
variable "kms_key_id" {}
variable "enable_logging" {
  description = "Enables logging"
  type        = bool
  default     = false
}
variable "log_exports" {
  default = []
}
variable "sg_enable_self" {
  default = true
}


# needs newer provider
# variable "config_param_datestyle" {}
# variable "config_param_enable_user_activity_logging" {}
# variable "config_param_query_group" {}
# variable "config_param_search_path" {}
# variable "config_param_max_query_execution_time" {}
# variable "config_param_auto_mv" {}
# variable "config_param_enable_case_sensitive_identifier" {}
