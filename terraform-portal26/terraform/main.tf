# Portal 26 OTEL Injection Only (No Deployment)
# This injects OTEL into agents without deploying to Vertex AI

terraform {
  required_version = ">= 1.5"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Inject OTEL into agents (no deployment)
resource "null_resource" "inject_otel_only" {
  for_each = var.agents

  triggers = {
    portal26_endpoint = var.portal26_endpoint
    service_name      = var.portal26_service_name
    otel_module_hash  = filemd5("${path.module}/../otel_portal26.py")
    agent_source_hash = filemd5("${each.value.source_dir}/agent.py")
    timestamp         = timestamp()
  }

  provisioner "local-exec" {
    command     = "python3 ../scripts/inject_otel_only.py --agent-name ${each.key} --source-dir ${each.value.source_dir} --portal26-endpoint ${var.portal26_endpoint} --service-name ${var.portal26_service_name}"
    working_dir = path.module
  }
}

# Outputs
output "injected_agents" {
  value = {
    for name, agent in var.agents : name => {
      display_name  = agent.display_name
      source_dir    = agent.source_dir
      injection_dir = "${agent.source_dir}_injected"
    }
  }
  description = "Agents with OTEL injection applied"
}

output "portal26_config" {
  value = {
    endpoint     = var.portal26_endpoint
    service_name = var.portal26_service_name
  }
  description = "Portal 26 configuration"
}

output "next_steps" {
  value = <<-EOT
  ✅ OTEL injection complete!

  Injected agents are in: *_injected directories

  To test locally:
    cd ${path.module}/../../empty_agent_portal26_injected
    export $(cat .env | xargs)
    python3 -c "import agent; print('OTEL initialized!')"

  To verify telemetry:
    cd ${path.module}/../../portal26_otel_agent
    python3 pull_agent_logs.py
    grep "empty-agent-portal26" portal26_otel_agent_logs_*.jsonl
  EOT
  description = "Next steps after injection"
}
