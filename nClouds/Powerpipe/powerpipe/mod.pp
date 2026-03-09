variable "mandatory_tags" {
  type        = list(string)
  description = "A list of mandatory tags to check for."
  default     = ["Environment", "Owner"]
}

mod "local" {
  title = "dashboards"
  require {
    mod "github.com/turbot/steampipe-mod-aws-tags" {
      version = "*"
      args = {
        mandatory_tags = var.mandatory_tags
      }
    }

    mod "github.com/turbot/steampipe-mod-aws-insights" {
      version = "*"
    }
  }
}