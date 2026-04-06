import httpx
import os
from dotenv import load_dotenv

load_dotenv()

TENANT_ID     = os.getenv("AZURE_TENANT_ID")
CLIENT_ID     = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")

def get_access_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }
    resp = httpx.post(url, data=data)
    resp.raise_for_status()
    token = resp.json().get("access_token")
    print("✅ Token obtenu avec succès")
    return token

def list_users(token: str):
    url = "https://graph.microsoft.com/v1.0/users"
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.get(url, headers=headers)
    resp.raise_for_status()
    users = resp.json().get("value", [])
    print(f"✅ {len(users)} utilisateur(s) trouvé(s) dans le tenant :")
    for u in users:
        print(f"   - {u.get('displayName')} | {u.get('mail') or u.get('userPrincipalName')}")

if __name__ == "__main__":
    token = get_access_token()
    list_users(token)