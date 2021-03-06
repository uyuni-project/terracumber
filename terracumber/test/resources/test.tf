// Mandatory variables for terracumber
variable "URL_PREFIX" {
  type = "string"
  default = "https://ci.suse.de/view/Manager/view/Uyuni/job/uyuni-master-cucumber-pipeline-NUE"
}

variable "CUCUMBER_COMMAND" {
  type = "string"
  default = "export PRODUCT='Uyuni' && cd /root/spacewalk/testsuite && rake cucumber:testsuite"
}

variable "CUCUMBER_BRANCH" {
  type = "string"
  default = "master"
}

variable "CUCUMBER_RESULTS" {
  type = "string"
  default = "/root/spacewalk/testsuite"
}

variable "MAIL_SUBJECT" {
  type = "string"
  default = "Results Uyuni-Master $status: $tests scenarios ($failures failed, $errors errors, $skipped skipped, $passed passed)"
}

variable "MAIL_TEMPLATE" {
  type = "string"
  default = "test/resources/templates/mail-template-jenkins.txt"
}

variable "MAIL_SUBJECT_ENV_FAIL" {
  type = "string"
  default = "Results Uyuni-Master: Environment setup failed"
}

variable "MAIL_TEMPLATE_ENV_FAIL" {
  type = "string"
  default = "test/resources/templates/mail-template-jenkins-env-fail.txt"
}

variable "MAIL_FROM" {
  type = "string"
  default = "galaxy-ci@suse.de"
}

variable "MAIL_TO" {
  type = "string"
  default = "juliogonzalez@localhost"
}

// sumaform specific variables
variable "SCC_USER" {
  type = "string"
}

variable "SCC_PASSWORD" {
  type = "string"
}

variable "GIT_USER" {
  type = "string"
  default = null // Not needed for master, as it is public
}

variable "GIT_PASSWORD" {
  type = "string"
  default = null // Not needed for master, as it is public
}

provider "libvirt" {
  uri = "qemu:///system"
}

module "cucumber_testsuite" {
  source = "./modules/cucumber_testsuite"

  product_version = "uyuni-master"
  branch          = var.CUCUMBER_BRANCH

  cc_username = var.SCC_USER
  cc_password = var.SCC_PASSWORD

  images = ["centos7", "opensuse150", "opensuse151", "sles15sp1", "ubuntu1804"]

  use_avahi    = false
  name_prefix  = "uyuni-master-"
  domain       = "tf.local"
  from_email   = "root@suse.inet"
  git_repo     = "https://github.com/uyuni-project/uyuni.git"
  git_username = var.GIT_USER
  git_password = var.GIT_PASSWORD

  // portus_uri      = "portus.mgr.suse.de:5000/cucutest"
  // portus_username = "cucutest"
  // portus_password = "cucusecret"

  // server_http_proxy = "galaxy-proxy.mgr.suse.de:3128"

  provider_settings = {
    bridge = null
    pool = "default"
    network_name = "default"
    additional_network = null
  }

  host_settings = {
    ctl = {
        name = "ctl"
    }
    srv = {
        name = "srv"
    }
    pxy = {
        name = "pxy"
    }
    cli-sles12sp4 = {
        image = "sles15sp1"
        name = "cli-sles15"
    }
    min-sles12sp4 = {
        image = "sles15sp1"
        name = "min-sles15"
    }
    minssh-sles12sp4 = {
        image = "sles15sp1"
        name = "minssh-sles15"
    }
    min-centos7 = {
        name = "min-centos7"
    }
    min-ubuntu1804 = {
        name = "min-ubuntu1804"
    }
    min-pxeboot = {
        name = "min-pxeboot"
        present = true
        image = "sles15sp1"
    }
    min-kvm = {
        name = "min-kvm"
        image = "opensuse151"
    }
  }
}
output "configuration" {
  value = module.cucumber_testsuite.configuration
}
