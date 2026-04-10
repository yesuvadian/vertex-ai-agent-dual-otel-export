# Client B - Portal 26 Configuration
# Deploy with: terraform apply -var-file="clients/client-b.tfvars"

project_id = "client-b-project-id"
region     = "europe-west1"

# Client B's Portal 26 endpoint (unique namespace)
portal26_endpoint     = "https://portal26.example.com/client-b"
portal26_service_name = "client-b-agents"

# Client B's agents
agents = {
  "customer-service" = {
    source_dir   = "/path/to/client-b/customer_service"
    display_name = "Client B - Customer Service"
  }

  "technical-support" = {
    source_dir   = "/path/to/client-b/tech_support"
    display_name = "Client B - Technical Support"
  }

  "order-processing" = {
    source_dir   = "/path/to/client-b/order_processing"
    display_name = "Client B - Order Processing"
  }
}
