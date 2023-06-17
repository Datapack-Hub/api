"""
This code does some weird ass stuff which should probably upload files to the cloudflare... don't ask me
"""

import requests
import config
import base64
from zipfile import ZipFile
import os


def upload_zipfile(file: str, file_name: str, uploader: str, squash: bool = False):
    print("Base64 File: " + file.split(",")[1])
    file = file.split(",")[1]
    file = file.encode("unicode_escape")
    decoded = base64.b64decode(file)

    with open(config.DATA + "Temporary.zip", "wb") as out:
        out.write(decoded)

    if squash:
        with ZipFile(config.DATA + "Temporary.zip", "r") as zip_ref:
            zip_ref.extractall(config.DATA + "Temporary")
        os.system("packsquash '/var/www/html/api/squash.toml'")

    put = requests.put(
        "https://files.datapackhub.net/" + file_name,
        open(config.DATA + "Temporary.zip", "rb"),
        headers={"Authorization": config.FILES_TOKEN, "Author": uploader},
    )

    if put.ok:
        return "https://files.datapackhub.net/" + file_name
    else:
        print(put.text)
    return False


def upload_file(file: str, file_name: str, uploader: str):
    file = file.split(",")[1]
    file = file.encode("unicode_escape")
    decoded = base64.b64decode(file)

    with open(config.DATA + "tempfile", "wb") as out:
        out.write(decoded)
        if out.tell() > 255999:
            return "File too big."
        out.close()

    put = requests.put(
        "https://files.datapackhub.net/" + file_name,
        open(config.DATA + "tempfile", "rb"),
        headers={"Authorization": config.FILES_TOKEN, "Author": uploader},
        timeout=300,
    )

    if put.ok:
        return "https://files.datapackhub.net/" + file_name
    return "Error Uploading", 500


if __name__ == "__main__":
    upload_zipfile(
        open("D:\Datapack Hub testing zips\Datapack.zip", "rb"),
        "Datapack.zip",
        "Silabear",
    )
