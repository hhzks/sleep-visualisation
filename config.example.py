# Fitbit API Configuration
# Copy this file to config.py and fill in your credentials.
# Get your credentials from https://dev.fitbit.com/apps

CLIENT_ID = "your_client_id_here"
CLIENT_SECRET = "your_client_secret_here"

# OAuth2 settings
REDIRECT_URI = "http://localhost:8080/callback"
AUTHORIZATION_URL = "https://www.fitbit.com/oauth2/authorize"
TOKEN_URL = "https://api.fitbit.com/oauth2/token"

# API settings
API_BASE_URL = "https://api.fitbit.com"
SCOPE = "sleep"
