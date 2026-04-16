output "amazon_ami" {
  value = module.live_go_launch_template.amazon_ami.image_id
  sensitive = false
}