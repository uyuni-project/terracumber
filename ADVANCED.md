# Advanced usage

## Use terraform variable files

To avoid using multiple `main.tf` files having the same deployment and just some variables differences, use the `tfvars` files with a main template to deploy environment.
For this example, we will have four types of files:

### main.tf

Deployment description using variables for environment specific parameters

__Example :__

```hcl
    server = {
      provider_settings = {
        mac = var.ENVIRONMENT_CONFIGURATION[var.ENVIRONMENT].mac["server"]
        vcpu = 8
        memory = 32768
      }
      additional_repos_only = var.ADDITIONAL_REPOS_ONLY
      additional_repos = local.additional_repos["server"]
      image = var.IMAGE
      additional_packages = [ "venv-salt-minion" ]
      install_salt_bundle = true
      server_mounted_mirror = var.MIRROR
    }
```

### variable.tf

Remove all the variables from the `main.tf` file and move it to a specific one.
   __Example :__

```hcl
variable "BRIDGE" {
  type = string
}

variable "ADDITIONAL_REPOS_ONLY" {
  type = bool
}

variable "ENVIRONMENT_CONFIGURATION" {
  type = map
  description = "Collection of  value containing : mac addresses, hypervisor and additional network"
}

variable "DOWNLOAD_ENDPOINT" {
  type = string
  description = "Download endpoint to get build images and set custom_download_endpoint. This value is equal to platform mirror"
}
```

### Custom terraform variable files (XXX.tfvars)

You can have as many as you want. Specify the variables depending on the environment. For example mac addresses depending on NUE or PRV environment

__Example :__

```'hcl'
############ Nuremberg unique variables ###########

DOMAIN            = "mgr.suse.de"
MIRROR            = "minima-mirror-ci-bv.mgr.suse.de"
DOWNLOAD_ENDPOINT = "minima-mirror-ci-bv.mgr.suse.de"
USE_MIRROR_IMAGES = true
GIT_PROFILES_REPO = "https://github.com/uyuni-project/uyuni.git#:testsuite/features/profiles/internal_nue"
BRIDGE            = "br0"
ENVIRONMENT_CONFIGURATION = {
  1 = {
    mac = {
      controller     = "aa:b2:93:01:03:50"
      server         = "aa:b2:93:01:03:51"
      proxy          = "aa:b2:93:01:03:52"
      suse-minion    = "aa:b2:93:01:03:54"
      suse-sshminion = "aa:b2:93:01:03:55"
      rhlike-minion  = "aa:b2:93:01:03:56"
      deblike-minion = "aa:b2:93:01:03:57"
      build-host     = "aa:b2:93:01:03:59"
      kvm-host       = "aa:b2:93:01:03:5a"
      nested-vm      = "aa:b2:93:01:03:5b"
    }
    hypervisor = "suma-08.mgr.suse.de"
    additional_network = "192.168.111.0/24"
  }
}
```

## Deploying environment depending on the product version, environment 

```bash
sh "rm -f ${env.resultdir}/sumaform/terraform.tfvars"
sh "cat ${tfvars_manager43} ${tfvars_nuremberg} >> ${env.resultdir}/sumaform/terraform.tfvars"
sh "echo 'ENVIRONMENT = \'${env_number}\'' >> ${env.resultdir}/sumaform/terraform.tfvars"
sh "cp ${tf_local_variables} ${env.resultdir}/sumaform/"
```
