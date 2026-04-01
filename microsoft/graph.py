import requests

from .types import GraphDriveItem, GraphHeaders


def get_site_id(site_hostname: str, site_path: str, headers: GraphHeaders) -> str:
    url = f"https://graph.microsoft.com/v1.0/sites/{site_hostname}:{site_path}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    site_data = resp.json()
    return site_data["id"]


def get_drive_id(site_id: str, drive_name: str, headers: GraphHeaders) -> str:
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    drives_data = resp.json()
    for drive in drives_data["value"]:
        if drive["name"] == drive_name:
            return drive["id"]
    raise ValueError("Drive not found")


def get_all_pptx_files(
    drive_id: str, headers: GraphHeaders, item_id: str = ""
) -> list[GraphDriveItem]:
    item_path = f"items/{item_id}" if item_id else "root"
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/{item_path}/children"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    items: list[GraphDriveItem] = resp.json()["value"]

    subfolders = [x for x in items if "folder" in x]
    subfolder_pptx_files = [
        get_all_pptx_files(drive_id, headers, x["id"]) for x in subfolders
    ]
    pptx_files = [x for x in items if x["name"].lower().endswith(".pptx")]
    return [f for f in pptx_files] + [
        f for subfolder_files in subfolder_pptx_files for f in subfolder_files
    ]


def get_pptx_file(
    drive_id: str, item_id: str, headers: GraphHeaders
) -> GraphDriveItem:
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def download_pptx_file_content(
    drive_id: str, item_id: str, headers: GraphHeaders
) -> bytes:
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.content
