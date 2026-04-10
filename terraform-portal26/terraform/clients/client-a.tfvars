# Client A - Portal 26 Configuration
# Deploy with: terraform apply -var-file="clients/client-a.tfvars"

project_id = "client-a-project-id"
region     = "us-central1"

# Client A's Portal 26 endpoint (unique namespace)
portal26_endpoint     = "https://portal26.example.com/client-a"
portal26_service_name = "client-a-agents"

# Client A's agents
agents = {
  "support-agent" = {
    source_dir   = "/path/to/client-a/support_agent"
    display_name = "Client A - Customer Support"
  }

  "sales-agent" = {
    source_dir   = "/path/to/client-a/sales_agent"
    display_name = "Client A - Sales Assistant"
  }

  "tech-support" = {
    source_dir   = "/path/to/client-a/tech_agent"
    display_name = "Client A - Technical Support"
  }
}
