"""
Google Health API OAuth2 Authentication Module
Handles the Google OAuth2 flow for Google Health API access.
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

TOKEN_FILE = "google_health_tokens.json"


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
            self.server.auth_state = query.get('state', [None])[0]
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


def get_authorization_url(code_challenge, state):
    """Build the Google authorization URL."""
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': state,
        # Ask Google for a refresh token so later runs do not need the browser.
        'access_type': 'offline',
        # Force the consent screen so Google issues a new refresh token.
        # This flow runs only when no usable refresh token exists.
        'prompt': 'consent',
    }
    return f"{AUTHORIZATION_URL}?{urlencode(params)}"


def exchange_code_for_tokens(auth_code, code_verifier):
    """Exchange authorization code for access tokens."""
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': auth_code,
        'code_verifier': code_verifier,
        'redirect_uri': REDIRECT_URI,
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Token exchange failed: {response.text}")


def refresh_access_token(refresh_token):
    """Refresh the access token using the refresh token."""
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        new_tokens = response.json()
        # Google usually does not send the refresh token again. Keep the old one.
        new_tokens.setdefault('refresh_token', refresh_token)
        return new_tokens
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

    if tokens and tokens.get('refresh_token'):
        try:
            print("Found existing tokens, attempting to refresh...")
            new_tokens = refresh_access_token(tokens['refresh_token'])
            save_tokens(new_tokens)
            print("Tokens refreshed successfully!")
            return new_tokens['access_token']
        except Exception as e:
            print(f"Token refresh failed: {e}")
            print("Starting new authentication flow...")

    # Generate PKCE codes and CSRF state
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(32)

    auth_url = get_authorization_url(code_challenge, state)

    print("\n" + "="*60)
    print("GOOGLE HEALTH AUTHENTICATION")
    print("="*60)
    print("\nOpening browser for Google authorization...")
    print("If the browser doesn't open, visit this URL manually:\n")
    print(auth_url)
    print("\n" + "="*60)

    webbrowser.open(auth_url)

    # Start local server to capture callback
    parsed_uri = urlparse(REDIRECT_URI)
    port = parsed_uri.port or 8080

    server = HTTPServer(('localhost', port), CallbackHandler)
    server.auth_code = None
    server.auth_state = None

    print(f"\nWaiting for authorization callback on port {port}...")

    server.handle_request()

    if server.auth_code:
        if server.auth_state != state:
            print("\nAuthentication failed: state mismatch in callback.")
            return None

        print("\nAuthorization code received! Exchanging for tokens...")
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
