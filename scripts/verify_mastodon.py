import httpx

from app.config import load_mastodon_settings


def main():
    try:
        settings = load_mastodon_settings()
    except ValueError as error:
        raise SystemExit(str(error)) from None

    try:
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            response = client.get(
                f"{settings.base_url}/api/v1/accounts/verify_credentials",
                headers={
                    "Authorization": f"Bearer {settings.access_token}",
                },
            )
    except httpx.RequestError:
        raise SystemExit(
            "Could not connect to Mastodon. Check the server URL and connection."
        ) from None

    if response.status_code != 200:
        raise SystemExit(
            f"Credential verification failed with HTTP {response.status_code}. "
            "Check account approval, token, and read:accounts permission."
        )

    try:
        account = response.json()
    except ValueError:
        raise SystemExit("Mastodon returned invalid JSON.") from None

    if not isinstance(account, dict) or not account.get("acct"):
        raise SystemExit("Mastodon response is missing account details.")

    print(f"Credentials verified for @{account['acct']}.")
    print(f"Server: {settings.base_url}")


if __name__ == "__main__":
    main()