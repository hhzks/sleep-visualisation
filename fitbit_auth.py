"""
Fitbit OAuth2 Authentication Module
Handles the OAuth2 flow for Fitbit API access.
"""

import base64
import hashlib
import secrets
import webbrowser
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
import requests

from config import (
    CLIENT_ID, CLIENT_SECRET, REDIRECT_URI,
    AUTHORIZATION_URL, TOKEN_URL, SCOPE
)

TOKEN_FILE = "fitbit_tokens.json"


def generate_code_verifier():
    """Generate a code verifier for PKCE."""
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(verifier):
    """Generate a code challenge from the verifier."""
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth2 callback."""
    
    def do_GET(self):
        """Handle GET request from OAuth2 callback."""
        query = parse_qs(urlparse(self.path).query)
        
        if 'code' in query:
            self.server.auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>Authorization Successful!</h1>
                    <p>You can close this window and return to the application.</p>
                </body>
                </html>
            """)
        else:
            self.server.auth_code = None
            error = query.get('error', ['Unknown error'])[0]
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <html>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1>Authorization Failed</h1>
                    <p>Error: {error}</p>
                </body>
                </html>
            """.encode())
    
    def log_message(self, format, *args):
        """Suppress logging."""
        pass


def get_authorization_url(code_challenge):
    """Build the authorization URL."""
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }
    return f"{AUTHORIZATION_URL}?{urlencode(params)}"


def exchange_code_for_tokens(auth_code, code_verifier):
    """Exchange authorization code for access tokens."""
    # Create Basic Auth header
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'client_id': CLIENT_ID,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'code_verifier': code_verifier,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Token exchange failed: {response.text}")


def refresh_access_token(refresh_token):
    """Refresh the access token using the refresh token."""
    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Token refresh failed: {response.text}")


def save_tokens(tokens):
    """Save tokens to a file."""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)


def load_tokens():
    """Load tokens from file if they exist."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None


def authenticate():
    """
    Perform OAuth2 authentication flow.
    Returns access token or None if authentication fails.
    """
    # Check for existing tokens
    tokens = load_tokens()
    
    if tokens:
        # Try to use existing token, refresh if needed
        try:
            print("Found existing tokens, attempting to refresh...")
            new_tokens = refresh_access_token(tokens['refresh_token'])
            save_tokens(new_tokens)
            print("Tokens refreshed successfully!")
            return new_tokens['access_token']
        except Exception as e:
            print(f"Token refresh failed: {e}")
            print("Starting new authentication flow...")
    
    # Generate PKCE codes
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # Build authorization URL
    auth_url = get_authorization_url(code_challenge)
    
    print("\n" + "="*60)
    print("FITBIT AUTHENTICATION")
    print("="*60)
    print("\nOpening browser for Fitbit authorization...")
    print("If the browser doesn't open, visit this URL manually:\n")
    print(auth_url)
    print("\n" + "="*60)
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to capture callback
    parsed_uri = urlparse(REDIRECT_URI)
    port = parsed_uri.port or 8080
    
    server = HTTPServer(('localhost', port), CallbackHandler)
    server.auth_code = None
    
    print(f"\nWaiting for authorization callback on port {port}...")
    
    # Wait for callback
    server.handle_request()
    
    if server.auth_code:
        print("\nAuthorization code received! Exchanging for tokens...")
        
        # Exchange code for tokens
        tokens = exchange_code_for_tokens(server.auth_code, code_verifier)
        save_tokens(tokens)
        
        print("Authentication successful!")
        return tokens['access_token']
    else:
        print("\nAuthentication failed!")
        return None


if __name__ == "__main__":
    token = authenticate()
    if token:
        print(f"\nAccess Token: {token[:20]}...")
