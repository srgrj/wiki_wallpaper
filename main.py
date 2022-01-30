import requests
import os
import ctypes
import subprocess
from datetime import date
from dateutil import relativedelta

SESSION = requests.Session()
ENDPOINT = "https://en.wikipedia.org/w/api.php"
SPI_SETDESKWALLPAPER = 20


def fetch_potd(cur_date):
    date_iso = cur_date.isoformat()
    title = "Template:POTD_protected/" + date_iso

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "images",
        "titles": title
    }

    response = SESSION.get(url=ENDPOINT, params=params)
    data = response.json()
    filename = data["query"]["pages"][0]["images"][0]["title"]
    image_page_url = "https://en.wikipedia.org/wiki/" + title

    image_data = {
        "filename": filename,
        "image_page_url": image_page_url,
        "image_src": fetch_image_src(filename),
        "date": date_iso
    }

    return image_data


def fetch_image_src(filename):
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url",
        "titles": filename
    }

    response = SESSION.get(url=ENDPOINT, params=params)
    data = response.json()
    page = next(iter(data["query"]["pages"].values()))
    image_info = page["imageinfo"][0]
    image_url = image_info["url"]

    return image_url


def set_background(date_obj):
    image_data = fetch_potd(date_obj)
    if os.name == "nt":
        storage = os.path.join(os.environ['TEMP'], 'wiki_background')
    elif os.name == "posix":
        storage = "/tmp/wiki_background/"
    image_path = os.path.join(storage, image_data['filename'].strip('File:'))
    if not os.path.isdir(storage):
        os.mkdir(storage)
    with open(image_path, 'wb') as handle:
        response = requests.get(image_data['image_src'], stream=True)

        if not response.ok:
            print(response)

        for block in response.iter_content(1024):
            if not block:
                break
            handle.write(block)
    if os.name == "nt":
        ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, image_path, 0)
    elif os.name == "posix":
        script = f"""/usr/bin/osascript<<END
       tell application "Finder"
       set desktop picture to POSIX file "{image_path}"
       end tell
       END"""
        subprocess.Popen(script, shell=True)


if __name__ == '__main__':
    set_background(date.today() - relativedelta.relativedelta(days=0))
