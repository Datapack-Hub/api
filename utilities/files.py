"""
This code does some weird ass stuff which should probably upload files to the cloudflare... don't ask me
"""

import base64
import shutil
from pathlib import Path

# yes bandit I consider the security implications of subprocess
import subprocess  # nosec
from urllib.parse import quote
from zipfile import ZipFile
from utilities import util

import requests

import config


def upload_zipfile(file: str, file_name: str, uploader: str, squash: bool = False):
    decoded = base64.b64decode(file.split(",")[1].encode("unicode_escape"))
    zip_path = Path(config.DATA + "Temporary.zip")
    folder_path = Path(config.DATA + "Temporary")

    zip_path.write_bytes(decoded)

    if folder_path.exists():
        shutil.rmtree(config.DATA + "Temporary")
    folder_path.mkdir(parents=True, exist_ok=True)

    if squash:
        with ZipFile(zip_path.absolute(), "r") as zip_ref:
            zip_ref.extractall(config.DATA + "Temporary")
        # its not like i'm passing user input, its constant
        subprocess.Popen(
            ["packsquash", "'/var/www/html/api/squash.toml'"]
        ).wait()  # nosec

    put = requests.put(
        "https://files.datapackhub.net/" + file_name,
        zip_path.read_bytes(),
        headers={"Authorization": config.FILES_TOKEN, "Author": uploader},
        timeout=300000,
    )

    if put.ok:
        return "https://files.datapackhub.net/" + file_name
    else:
        util.log(put.text)
    return False


def upload_file(file: str, file_name: str, uploader: str):
    decoded = base64.b64decode(file.split(",")[1].encode("unicode_escape"))
    path = Path(config.DATA + "tempfile")

    if path.stat().st_size > 255999:
        return "File too big."

    path.write_bytes(decoded)

    put = requests.put(
        "https://files.datapackhub.net/" + quote(file_name),
        path.read_bytes(),
        headers={"Authorization": config.FILES_TOKEN, "Author": uploader},
        timeout=300,
    )

    if put.ok:
        return "https://files.datapackhub.net/" + quote(file_name)
    return "Error Uploading", 500


# if __name__ == "__main__":
#     upload_zipfile(
#         open("D:\Datapack Hub testing zips\Datapack.zip", "rb"),
#         "Datapack.zip",
#         "Silabear",
#     )
