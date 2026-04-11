locals {
  config     = yamldecode(file("${path.module}/config/${terraform.workspace}.yaml"))
  identifier = "${local.config.identifier}-${terraform.workspace}"
  tags = merge(local.config.tags, {})

  sg_groups_names = local.config.networking_config.enable ? [for n in local.config.networking_config.security_groups: n.name  ] : []
  sg_groups_val   = local.config.networking_config.enable ? [for n in local.config.networking_config.security_groups: n] : []

  sg_groups_info = zipmap(local.sg_groups_names, local.sg_groups_val)
}