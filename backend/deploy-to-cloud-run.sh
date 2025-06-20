#!/bin/bash
# Auth Gateway - Google Cloud Run Deployment Script

# Exit on error
set -e

# Default values
SERVICE_NAME="auth-gateway"
REGION="asia-east2"
ALLOW_UNAUTHENTICATED=true

# Display help message
function show_help {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -n, --name NAME       Service name (default: auth-gateway)"
  echo "  -r, --region REGION   GCP region (default: asia-east2)"
  echo "  -p, --project ID      GCP project ID (required)"
  echo "  -h, --help            Show this help message"
  echo ""
  echo "Environment variables must be provided in a .env.deploy file"
  echo "See .env.example for required variables"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -n|--name)
      SERVICE_NAME="$2"
      shift
      shift
      ;;
    -r|--region)
      REGION="$2"
      shift
      shift
      ;;
    -p|--project)
      PROJECT_ID="$2"
      shift
      shift
      ;;
    -h|--help)
      show_help
      ;;
    *)
      echo "Unknown option: $1"
      show_help
      ;;
  esac
done

# Check for required arguments
if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP project ID is required"
  show_help
fi

# Check for .env.deploy file
if [ ! -f .env.deploy ]; then
  echo "Error: .env.deploy file not found"
  echo "Create a .env.deploy file with your environment variables"
  echo "See .env.example for required variables"
  exit 1
fi

# Load environment variables from .env.deploy
source .env.deploy

# Check for required environment variables
REQUIRED_VARS=(
  "FIREBASE_PROJECT_ID"
  "FIREBASE_API_KEY"
  "FIREBASE_AUTH_DOMAIN"
  "FIREBASE_APP_ID"
  "GOOGLE_CLIENT_ID"
  "GOOGLE_CLIENT_SECRET"
  "ALLOWED_EMAIL_DOMAIN_REGEX"
  "CORS_ALLOWED_ORIGINS"
  "GATEWAY_PUBLIC_URL" # Added: Public URL of the deployed gateway service
)

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: $var is required in .env.deploy"
    exit 1
  fi
done

echo "Deploying Auth Gateway backend to Google Cloud Run..."
echo "Service name: $SERVICE_NAME"
echo "Region: $REGION"
echo "Project ID: $PROJECT_ID"

# Set the GCP project
gcloud config set project "$PROJECT_ID"

# Create a secret for GOOGLE_CLIENT_SECRET if it doesn't exist
SECRET_NAME="auth-gateway-google-client-secret"
if ! gcloud secrets describe "$SECRET_NAME" &>/dev/null; then
  echo "Creating secret for GOOGLE_CLIENT_SECRET..."
  echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets create "$SECRET_NAME" --replication-policy="automatic" --data-file=-
else
  echo "Updating secret for GOOGLE_CLIENT_SECRET..."
  echo -n "$GOOGLE_CLIENT_SECRET" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
fi

# Create a temporary YAML file for environment variables
ENV_YAML_FILE=$(mktemp)
cat > "$ENV_YAML_FILE" << EOF
FIREBASE_PROJECT_ID: $FIREBASE_PROJECT_ID
FIREBASE_API_KEY: $FIREBASE_API_KEY
FIREBASE_AUTH_DOMAIN: $FIREBASE_AUTH_DOMAIN
FIREBASE_APP_ID: $FIREBASE_APP_ID
GOOGLE_CLIENT_ID: $GOOGLE_CLIENT_ID
ALLOWED_EMAIL_DOMAIN_REGEX: $ALLOWED_EMAIL_DOMAIN_REGEX
CORS_ALLOWED_ORIGINS: $CORS_ALLOWED_ORIGINS
GATEWAY_PUBLIC_URL: $GATEWAY_PUBLIC_URL
EOF

# Build and deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --env-vars-file="$ENV_YAML_FILE" \
  --set-secrets="GOOGLE_CLIENT_SECRET=$SECRET_NAME:latest"

# Clean up the temporary file
rm "$ENV_YAML_FILE"

# Get the deployed service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")

echo "Deployment complete!"
echo "Auth Gateway backend is available at: $SERVICE_URL"
echo ""
echo "Next steps:"
echo "1. Update your client applications to use this URL"
echo "2. Test the authentication flow"
