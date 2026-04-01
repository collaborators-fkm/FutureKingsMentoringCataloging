import os

import msal

from .graph import get_drive_id, get_site_id
from .types import GraphHeaders


def excel_setup() -> tuple[GraphHeaders, str]:
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET_VALUE")
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scopes = ["https://graph.microsoft.com/.default"]
    site_hostname = os.getenv("SITE_HOSTNAME")
    site_path = os.getenv("SITE_PATH")
    drive_name = os.getenv("DRIVE_NAME")

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )

    token = app.acquire_token_for_client(scopes=scopes)
    access_token = token["access_token"]
    headers: GraphHeaders = {"Authorization": f"Bearer {access_token}"}
    site_id = get_site_id(site_hostname, site_path, headers)
    library_drive_id = get_drive_id(site_id, drive_name, headers)

    return headers, library_drive_id
