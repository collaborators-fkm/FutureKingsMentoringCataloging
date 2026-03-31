import json
import os
from io import BytesIO
from typing import Literal

from dotenv import load_dotenv
import msal
from openai import OpenAI
from pptx import Presentation
from pydantic import BaseModel, Field
import requests

load_dotenv()


class PresentationMetadata(BaseModel):
    theme: list[
        Literal[
            "Confidence & Leadership",
            "Financial Literacy",
            "College & Career Prep",
        ]
    ] = Field(
        description=(
            "One or more applicable themes. Only use multiple themes when necessary."
        )
    )
    description: str = Field(
        description="A concise description of the presentation in one or two sentences."
    )
    duration_estimate_minutes: int = Field(
        description=(
            "Estimated total presentation duration in minutes, rounded to the nearest "
            "15 minutes unless over 120 minutes, in which case round to the nearest hour."
        )
    )
    audience: Literal["Middle school", "High school", "College"]
    activity_length_minutes: int = Field(
        description=(
            "Approximate minutes of activity time in the presentation, using the same "
            "rounding rules as duration_estimate_minutes."
        )
    )


def get_site_id(site_hostname, site_path, headers):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_hostname}:{site_path}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    site_data = resp.json()
    return site_data["id"]


def get_drive_id(site_id, drive_name, headers):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    drives_data = resp.json()
    for drive in drives_data["value"]:
        if drive["name"] == drive_name:
            return drive["id"]
    raise ValueError("Drive not found")


def get_all_pptx_files(drive_id, headers, item_id="") -> list[str]:
    item_path = f"items/{item_id}" if item_id else "root"
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/{item_path}/children"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    items = resp.json()["value"]

    subfolders = [x for x in items if ("folder" in x)]
    subfolder_pptx_files = [
        get_all_pptx_files(drive_id, headers, x["id"]) for x in subfolders
    ]
    pptx_files = [x for x in items if x["name"].lower().endswith(".pptx")]
    return [f for f in pptx_files] + [
        f for subfolder_files in subfolder_pptx_files for f in subfolder_files
    ]


def get_file(drive_id, item_id, headers):
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def download_pptx_file_content(drive_id, item_id, headers):
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.content


def extract_slide_text_from_pptx_bytes(pptx_bytes) -> list[str]:
    presentation = Presentation(BytesIO(pptx_bytes))
    slides = []

    for slide in presentation.slides:
        slide_text = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_text.append(shape.text.strip())
        slides.append("\n".join(slide_text))

    return slides


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing from the environment")
    return OpenAI(api_key=api_key)


def generate_ai_metadata(
    client: OpenAI,
    *,
    name: str,
    slide_texts: list[str],
    number_of_slides: int,
    average_words_per_slide: float,
) -> PresentationMetadata:
    entire_slide_text = "\n\n--- SLIDE BREAK ---\n\n".join(slide_texts)

    response = client.responses.parse(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": (
                    "You classify educational presentation decks. "
                    "Return only schema-valid structured data."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Presentation name: {name}\n"
                    f"Number of slides: {number_of_slides}\n"
                    f"Average words per slide: {average_words_per_slide:.2f}\n"
                    "Entire slide text:\n"
                    f"{entire_slide_text}"
                ),
            },
        ],
        text_format=PresentationMetadata,
    )

    if response.output_parsed is None:
        raise ValueError(f"OpenAI did not return structured metadata for {name}")

    return response.output_parsed


def main():
    TENANT_ID = os.getenv("TENANT_ID")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET_VALUE")  # for confidential/server apps
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    SCOPES = ["https://graph.microsoft.com/.default"]
    SITE_HOSTNAME = os.getenv("SITE_HOSTNAME")
    SITE_PATH = os.getenv("SITE_PATH")
    openai_client = get_openai_client()

    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )

    token = app.acquire_token_for_client(scopes=SCOPES)
    access_token = token["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}

    SITE_ID = get_site_id(SITE_HOSTNAME, SITE_PATH, headers)
    LIBRARY_DRIVE_ID = get_drive_id(SITE_ID, os.getenv("DRIVE_NAME"), headers)

    # pptx_files = get_all_pptx_files(LIBRARY_DRIVE_ID, headers)
    pptx_files = [
        get_file(LIBRARY_DRIVE_ID, item_id, headers)
        for item_id in [
            "01I7HKCO3RVKMEHQRDR5GZJS6QR56L6LCY",
            # "01I7HKCO4N6ZP6BHCCCVBJDSLM4WQMMQ3Q",
            # "01I7HKCO5IQU3OKDVXEJHYBUP7LAFU4UHH",
            # "01I7HKCO4SPWFCOVNN7JAL4QDULH5PPCYJ",
            # "01I7HKCO6FJRJTI7CXJRAISZFRGAYIPMPU",
            # "01I7HKCO7VKOUI5SISPVGITFBOSTIWTI3H",
        ]
    ]

    raw_pptx_slide_data = [
        {
            "id": pptx_file["id"],
            "name": pptx_file["name"],
            "slide_texts": extract_slide_text_from_pptx_bytes(
                download_pptx_file_content(LIBRARY_DRIVE_ID, pptx_file["id"], headers)
            ),
            "last_modified": pptx_file["lastModifiedDateTime"],
        }
        for pptx_file in pptx_files
    ]

    final_pptx_objects = []
    for pptx_file in raw_pptx_slide_data:
        number_of_slides = len(pptx_file["slide_texts"])
        average_words_per_slide = (
            sum(len(slide.split()) for slide in pptx_file["slide_texts"])
            / number_of_slides
        )
        ai_metadata = generate_ai_metadata(
            openai_client,
            name=pptx_file["name"],
            slide_texts=pptx_file["slide_texts"],
            number_of_slides=number_of_slides,
            average_words_per_slide=average_words_per_slide,
        )

        final_pptx_objects.append(
            {
                **pptx_file,
                "number_of_slides": number_of_slides,
                "average_words_per_slide": average_words_per_slide,
                "theme*": ai_metadata.theme,
                "description*": ai_metadata.description,
                "duration_estimate_mins*": ai_metadata.duration_estimate_minutes,
                "audience*": ai_metadata.audience,
                "activity_length_mins*": ai_metadata.activity_length_minutes,
            }
        )

    print(json.dumps(final_pptx_objects, indent=2))


if __name__ == "__main__":
    main()
