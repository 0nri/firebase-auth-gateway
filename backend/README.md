# Auth Gateway Backend Service

A FastAPI-based authentication service that verifies Firebase ID tokens and enforces domain restrictions.

## Features

- Firebase ID token verification
- Domain restriction enforcement
- Stateless JWT-based authentication
- CORS configuration for client applications

## Prerequisites

- Python 3.10+
- Firebase project with Google Sign-In enabled
- Google Cloud service account with Firebase Admin SDK permissions

## Setup

1. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Copy the `.env.example` file to `.env` and update the values:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration:

```
GCP_PROJECT_ID=your-gcp-project-id
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_APP_ID=your-app-id
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
ALLOWED_EMAIL_DOMAIN_REGEX=^.+@yourdomain\.com$
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://your-app.com
```

4. **Set up Firebase credentials**

There are several ways to provide Firebase credentials:

- Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your service account JSON file
- Use Google Cloud default credentials
- Deploy to Google Cloud Run, which will use the service account assigned to the service

## Running the Service

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The service will be available at http://localhost:8000

## API Endpoints

### Health Check

```
GET /
```

Returns a simple status message to confirm the service is running.

### Verify Token

```
POST /verify-token
```

**Headers:**
- `Authorization: Bearer <firebase_id_token>`

**Response:**
```json
{
  "uid": "string",
  "email": "string",
  "display_name": "string",
  "photo_url": "string"
}
```

**Error Responses:**
- 401 Unauthorized: Invalid or expired token
- 403 Forbidden: Email domain not allowed

### Login

```
POST /auth/login
```

**Request Body:**
```json
{
  "redirect_uri": "string (optional)"
}
```

**Response:**
```json
{
  "url": "string"
}
```

**Error Responses:**
- 400 Bad Request: Redirect URI not provided and no default configured
- 500 Internal Server Error: Firebase configuration missing

### Authentication Callback

```
POST /auth/callback
```

**Request Body:**
```json
{
  "code": "string",
  "state": "string (optional)"
}
```

**Response:**
```json
{
  "token": "string",
  "user": {
    "uid": "string",
    "email": "string",
    "display_name": "string",
    "photo_url": "string"
  }
}
```

**Error Responses:**
- 401 Unauthorized: Invalid or expired token
- 403 Forbidden: Email domain not allowed
- 500 Internal Server Error: Failed to exchange code for token

### Logout

```
POST /auth/logout
```

**Response:**
```json
{
  "status": "ok"
}
```

## Deployment

### Cloud Run Deployment Files

The service includes the following files for Cloud Run deployment:

- **Dockerfile**: Specifies how to build the container image for Cloud Run.
- **main.py**: A root-level entry point for Cloud Run to locate the application.
- **deploy-to-cloud-run.sh**: Script to automate the deployment process.

### Using the Deployment Script

The service includes a deployment script for Google Cloud Run that handles environment variables and secrets:

1. **Create a deployment environment file**

```bash
cp .env.deploy.example .env.deploy
```

Edit the `.env.deploy` file with your production configuration.

2. **Run the deployment script**

```bash
./deploy-to-cloud-run.sh --project your-gcp-project-id
```

Additional options:
```
  -n, --name NAME       Service name (default: auth-gateway-backend)
  -r, --region REGION   GCP region (default: us-central1)
  -p, --project ID      GCP project ID (required)
  -h, --help            Show this help message
```

The script will:
- Create/update a Secret Manager secret for your Google Client Secret
- Deploy the service to Cloud Run with the appropriate environment variables
- Display the deployed service URL

### Manual Deployment

You can also deploy manually to Google Cloud Run:

```bash
gcloud run deploy auth-gateway-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="FIREBASE_PROJECT_ID=your-project-id,FIREBASE_API_KEY=your-api-key,FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com,GOOGLE_CLIENT_ID=your-client-id,ALLOWED_EMAIL_DOMAIN_REGEX=^.+@yourdomain\.com$,CORS_ALLOWED_ORIGINS=https://your-app.com"
```

For sensitive environment variables like `GOOGLE_CLIENT_SECRET`, use Secret Manager:

```bash
# First, create the secret
gcloud secrets create auth-gateway-google-client-secret --replication-policy="automatic"
echo -n "your-client-secret" | gcloud secrets versions add auth-gateway-google-client-secret --data-file=-

# Then reference it in your deployment
gcloud run deploy auth-gateway-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="FIREBASE_PROJECT_ID=your-project-id,..." \
  --set-secrets="GOOGLE_CLIENT_SECRET=auth-gateway-google-client-secret:latest"
```

## Authentication Flow

The Auth Gateway implements a server-side authentication flow:

1. Client requests a login URL from `/auth/login`
2. User is redirected to Google for authentication
3. Google redirects back to Auth Gateway's `/auth/callback` with an authorization code
4. Auth Gateway exchanges the authorization code for a Google ID token
5. Auth Gateway exchanges the Google ID token for a Firebase token
6. Auth Gateway verifies the Firebase token and validates the email domain
7. Auth Gateway returns the Firebase token and user data to the client

## Testing

Run the tests:

```bash
pytest
```

## Troubleshooting

### Common Issues

1. **"Google Client Secret missing" error**
   - Ensure the `GOOGLE_CLIENT_SECRET` environment variable is set in your `.env` file
   - For deployment, make sure it's included in your `.env.deploy` file or set as a secret

2. **"Invalid IdP response/credential" error**
   - This typically occurs when the callback URL doesn't match what's configured in Google Cloud Console
   - Ensure the redirect URI used in the initial request matches what's registered in Google Cloud Console

3. **CORS errors**
   - Add the client application's origin to the `CORS_ALLOWED_ORIGINS` environment variable
   - Make sure to include the protocol (http/https) and port if applicable

4. **"No module named 'main'" error in Cloud Run**
   - This happens when Cloud Run can't find the application entry point
   - Make sure you have a `main.py` file at the root of your backend directory
   - Use the provided `deploy-to-cloud-run.sh` script which correctly configures the deployment
