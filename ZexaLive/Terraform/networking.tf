data "aws_availability_zones" "available" {
  state = "available"
}

module "vpc" {
  count   = local.config.networking_config.enable ? 1 : 0
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.6.1"

  name = local.identifier
  cidr = local.config.networking_config.cidr

  azs              = slice(data.aws_availability_zones.available.names, 0, 4)
  private_subnets  = local.config.networking_config.private_subnet_cidrs
  public_subnets   = local.config.networking_config.public_subnet_cidrs

  one_nat_gateway_per_az = false
  single_nat_gateway     = false

  enable_nat_gateway = false
  enable_vpn_gateway = false

  map_public_ip_on_launch = true

  public_subnet_tags = merge({
    "layer"                  = "public"
  }, local.tags)

  private_subnet_tags = merge({
    "layer"                  = "private"
  }, local.tags)

  tags = local.tags
}

module "vpc_endpoints" {
  count   = local.config.networking_config.enable ? 1 : 0
  source  = "terraform-aws-modules/vpc/aws//modules/vpc-endpoints"
  version = "6.6.1"

  vpc_id = module.vpc[0].vpc_id

  endpoints = {
    s3 = {
      service      = "s3"
      service_type = "Gateway"
      
      route_table_ids = module.vpc[0].private_route_table_ids
      
      tags = merge({
        Name = "${local.identifier}-s3-gateway"
      }, local.tags)
    }
  }
}

module "vpc_sgs" {
  for_each = local.config.networking_config.enable ? toset(local.sg_groups_names) : toset([])
  source = "terraform-aws-modules/security-group/aws"
  version = "5.3.1"

  name        = "${local.identifier}-${each.value}"
  description = local.sg_groups_info[each.value].description
  vpc_id      = module.vpc[0].vpc_id

  ingress_with_cidr_blocks = local.sg_groups_info[each.value].ingres

  ingress_with_self = lookup(local.sg_groups_info[each.value], "ingress_self", [])

  egress_with_cidr_blocks = local.sg_groups_info[each.value].egress

  tags = local.tags
}