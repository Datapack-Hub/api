"""
This code does some weird ass stuff which should probably upload files to the cloudflare... don't ask me
"""

import requests
import config
import base64
from zipfile import ZipFile
import os

def upload_file(file: str, file_name: str, uploader: str, squash: bool = False):
    file = file.encode("unicode_escape")
    decoded = base64.b64decode(file[41:])

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
        timeout=300,
    )
    
    if put.ok:
        return "https://files.datapackhub.net/" + file_name
    else:
        print(put.text)
    return False


if __name__ == "__main__":
    upload_file(
        open("D:\Datapack Hub testing zips\Datapack.zip", "rb"),
        "Datapack.zip",
        "Silabear",
    )
