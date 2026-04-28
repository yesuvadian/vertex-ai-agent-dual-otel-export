# How to Distribute to Clients

## What Clients Need

Clients will deploy in **their own GCP project** using their own credentials.

You send them:
1. The `client_package/` folder (Terraform files + scripts)
2. AWS Lambda URL (same for all clients)
3. Their Reasoning Engine IDs

## 1. Package the Client Files

```bash
cd terraform/
zip -r client-setup.zip client_package/
```

Or send the `client_package/` folder directly.

**Note:** The `appengine-sa-key.json` in the package is an EXAMPLE. Clients will replace it with their own service account key from their own GCP project (see Step 1 in CLIENT_GUIDE.md).

## 2. What Clients Will Do

Clients follow CLIENT_GUIDE.md (3 simple steps):
1. Download service account key from their GCP Console  
2. Configure `terraform.tfvars` (project ID + Engine IDs)
3. Run `deploy.sh` (Linux/Mac) or `deploy.ps1` (Windows)

Done. Everything automated in the scripts.

## Security Notes

- Clients use their own service account keys (not yours)
- Each client deploys to their own GCP project
- All clients send logs to the same Lambda URL
- Recommend clients rotate keys every 90 days
