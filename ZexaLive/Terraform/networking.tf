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

  public_subnet_tags = merge({
    "layer"                  = "public"
  }, local.tags)

  private_subnet_tags = merge({
    "layer"                  = "private"
  }, local.tags)

  tags = local.tags
}