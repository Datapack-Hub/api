"""
This code does some weird ass stuff which should probably upload files to the cloudflare... dont ask me
"""

import requests
import config
import base64

def upload_file(file: str, file_name:str, uploader:str):
    print(file[41:44])
    file = file.encode("unicode_escape")
    decoded = base64.b64decode(file[41:])
    
    with open(config.DATA + "Temporary.zip", "w") as out:
        out.write(decoded.decode("ISO-8859-1"))
    
    put = requests.put("https://files.datapackhub.net/" + file_name, open(config.DATA + "Temporary.zip", "rb"), headers={
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