import json
import requests
from datetime import datetime, timezone
from dateutil import parser

SERVER_URL = 'https://email-auth.45d.io/'
TOKEN_PATH = '/etc/45drives/msmtp_auth_token.json'

def normalize_to_utc(expiry):
    return datetime.fromtimestamp(int(expiry), tz=timezone.utc)

def load_token_data():
    with open(TOKEN_PATH, 'r') as f:
        return json.load(f)

def save_token_data(token_data):
    with open(TOKEN_PATH, 'w') as f:
        json.dump(token_data, f, indent=4)
    print(f"Token file updated at {TOKEN_PATH}")


def refresh_token_via_server(token_data):
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        raise ValueError("No refresh token found in token data.")

    response = requests.post(
        f"{SERVER_URL}/auth/refresh-token/gmail",
        json={"refreshToken": refresh_token}
    )
    if response.status_code == 200:
        new_data = response.json()
        token_data["access_token"] = new_data["accessToken"]
        token_data["expiry"] = new_data["expiry"]
        save_token_data(token_data)
        print("Token refreshed via server.")
    else:
        raise Exception(f"Failed to refresh token: {response.text}")

def validate_and_refresh_token():
    token_data = load_token_data()
    refresh_token_via_server(token_data)

if __name__ == "__main__":
    validate_and_refresh_token()
