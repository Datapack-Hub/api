"""
This code does some weird ass stuff which should probably upload files to the cloudflare... dont ask me
"""

import requests
import config

def upload_file(file: str, file_name:str, uploader:str):
    put = requests.put("https://files.datapackhub.net/" + file_name.decode(), file, headers={
        "Authorization":config.FILES_TOKEN,
        "Author":uploader
    })
    if put.ok:
        return "https://files.datapackhub.net/" + file_name
    else:
        print(put.text)
        return False
    
if __name__ == "__main__":
    upload_file(open("D:\Datapack Hub testing zips\Datapack.zip","rb"),"Datapack.zip","Silabear")