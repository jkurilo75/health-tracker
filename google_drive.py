import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


SCOPES = [
    "https://www.googleapis.com/auth/drive.file"
]


TOKEN_FILE = "token.json"


def get_drive_service():

    creds = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )


    if creds.expired and creds.refresh_token:

        creds.refresh(Request())

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())


    return build(
        "drive",
        "v3",
        credentials=creds
    )



def upload_to_drive(
        filename,
        filepath,
        mimetype
):

    drive = get_drive_service()


    file_metadata = {
        "name": filename,
        "parents": [
            os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        ]
    }


    media = MediaFileUpload(
        filepath,
        mimetype=mimetype
    )


    result = drive.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()


    return result["id"]