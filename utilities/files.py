"""
This code does some weird ass stuff which should probably upload files to the cloudflare... don't ask me
"""
import base64
import shutil

# yes bandit I consider the security implications of subprocess
import subprocess  # nosec
from pathlib import Path
from urllib.parse import quote
from zipfile import ZipFile

# ignore because pillow is weird
import pillow_avif  # noqa: F401
import requests
from PIL import Image

import config
from utilities import util


def upload_zipfile(file: str, file_name: str, uploader: str, squash: bool = False):
    decoded = base64.b64decode(file.split(",")[1].encode("unicode_escape"))
    zip_path = Path(config.DATA + "Temporary.zip")
    folder_path = Path(config.DATA + "Temporary")

    zip_path.write_bytes(decoded)

    if folder_path.exists():
        shutil.rmtree(config.DATA + "Temporary")
    folder_path.mkdir(parents=True, exist_ok=True)

    if squash:
        bad_exts = [".zip", ".gz", ".7z", ".rar", ".br", ".zx", ".apk", ".car", ".dmg"]

        with ZipFile(zip_path.absolute(), "r") as zipf:
            filenames = zipf.namelist()

            for zipped in zipf.filelist:
                if zipped.file_size > 4 * 1024 * 1024:
                    return False

            extensions = [Path(filename).suffix for filename in filenames]

            util.log("bad extensions detected!")
            for ext in bad_exts:
                if ext in extensions:
                    return False

            zipf.extractall(config.DATA + "Temporary")

        temp_path = Path(config.DATA + "Temporary")
        mac_folder = temp_path / "__MACOSX"
        shutil.rmtree(str(mac_folder))
        dirs = list(temp_path.iterdir())
        if ".DS_Store" in dirs:
            dirs.remove(".DS_Store")

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


def upload_file(file: str, file_name: str, uploader: str, is_icon: bool = False):
    decoded = base64.b64decode(file.split(",")[1].encode("unicode_escape"))
    path = Path(config.DATA + "tempfile")

    path.touch()

    if path.stat().st_size > 255999:
        return "File too big."

    path.write_bytes(decoded)

    if is_icon:
        path = optimize_img(path)

    put = requests.put(
        "https://files.datapackhub.net/" + quote(file_name),
        path.read_bytes(),
        headers={"Authorization": config.FILES_TOKEN, "Author": uploader},
        timeout=300,
    )

    if put.ok:
        return "https://files.datapackhub.net/" + quote(file_name)
    return "Error Uploading", 500


def optimize_img(path: Path) -> Path:
    new_path = path.with_suffix(".avif")
    img = Image.open(path)
    img.resize((128, 128))
    img.save(new_path)
    util.log("Done!")
    return new_path
