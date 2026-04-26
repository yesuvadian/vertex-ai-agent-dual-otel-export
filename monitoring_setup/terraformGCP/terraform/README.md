# Admin Reference

## For Distribution

See `DISTRIBUTE.md` for how to send `client_package/` to clients.

## For Testing Locally

If you want to test the deployment yourself:

### 1. Set Credentials
```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/appengine-sa-key.json"
```

### 2. Configure
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with:
- Your Lambda URL
- Your Reasoning Engine IDs

### 3. Deploy
```bash
terraform init
terraform plan
terraform apply
```

### 4. Cleanup
```bash
terraform destroy
```

## Files

- `client_package/` - Ready-to-send client folder
- `DISTRIBUTE.md` - How to distribute to clients
- `main.tf` - Main Terraform configuration
- `gcp_log_sink_pubsub.tf` - GCP resources
- `terraform.tfvars.example` - Configuration template
- `appengine-sa-key.json` - Service account key (keep secure!)
