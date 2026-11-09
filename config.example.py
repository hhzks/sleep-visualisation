# Google Health API Configuration
# Copy this file to config.py and fill in your credentials.
# Create an OAuth 2.0 client ("Web application") at
# https://console.cloud.google.com/apis/credentials
# and enable the Google Health API (health.googleapis.com) for the project.

CLIENT_ID = "your_client_id_here.apps.googleusercontent.com"
CLIENT_SECRET = "your_client_secret_here"

# OAuth2 settings
# Add this exact URI to "Authorized redirect URIs" on the OAuth client.
REDIRECT_URI = "http://localhost:8080/callback"
AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# API settings
API_BASE_URL = "https://health.googleapis.com/v4"
SCOPE = "https://www.googleapis.com/auth/googlehealth.sleep.readonly"
