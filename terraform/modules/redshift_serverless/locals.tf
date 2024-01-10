locals {
  rc_tags = {
    env      = var.env
    profile  = var.profile
    author   = "rapid-cloud"
    fqn      = var.fqn
    cmd_id   = var.cmd_id
    workload = var.workload
  }
}
