# Infrastructure as Code: the test lab (network + instrument + dashboard)
# described in code. `terraform apply` creates it, `terraform destroy`
# removes it. Runs against local Docker - no cloud account needed.

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

variable "sim_fault" {
  description = "Fault to inject in the simulator (empty = healthy)"
  type        = string
  default     = ""
}

resource "docker_image" "lab" {
  name = "rf-test-lab:latest"
  build {
    context = "${path.module}/.."
  }
}

resource "docker_network" "lab" {
  name = "rf-lab-net"
}

resource "docker_container" "instrument" {
  name    = "instrument"
  image   = docker_image.lab.image_id
  command = ["python", "-m", "instrument_sim.simulator"]
  env     = ["SIM_FAULT=${var.sim_fault}"]

  networks_advanced {
    name = docker_network.lab.name
  }
  ports {
    internal = 5025
    external = 5025
  }
}

resource "docker_container" "dashboard" {
  name    = "dashboard"
  image   = docker_image.lab.image_id
  command = ["python", "-m", "dashboard.app"]
  env     = ["INSTRUMENT_HOST=instrument"]

  networks_advanced {
    name = docker_network.lab.name
  }
  ports {
    internal = 8080
    external = 8080
  }
  depends_on = [docker_container.instrument]
}

output "dashboard_url" {
  value = "http://localhost:8080"
}
