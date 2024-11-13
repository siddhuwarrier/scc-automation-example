resource "cdo_ftd_device" "ftds" {
  provider           = cdo.msp_managed_tenant
  count = length(var.ftds)
  access_policy_name = fmc_access_policies.msp_access_policy.name
  licenses           = var.ftds[count.index].licenses
  name               = var.ftds[count.index].name
  virtual            = var.ftds[count.index].virtual
  performance_tier   = var.ftds[count.index].virtual ? var.ftds[count.index].performance_tier : null
  lifecycle {
    ignore_changes = [access_policy_name]
  }
}

resource "null_resource" "ssh_into_ftds" {
  count = length(cdo_ftd_device.ftds)

  provisioner "local-exec" {
    command = <<EOT
      sshpass -p ${var.ftds[count.index].password} ssh -o StrictHostKeyChecking=no
-p ${var.ftds[count.index].ssh_port} ${var.ftds[count.index].username}@${var.ftds[count.index].ssh_address}
"${cdo_ftd_device.ftds[count.index].generated_command}"
    EOT
  }
}

resource "cdo_ftd_device_onboarding" "ftds" {
  provider = cdo.msp_managed_tenant
  count = length(var.ftds)
  ftd_uid  = cdo_ftd_device.ftds[count.index].id
  depends_on = [null_resource.ssh_into_ftds]
}