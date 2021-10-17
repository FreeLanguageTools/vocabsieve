import bs4
import requests
from playsound import PlaysoundException, playsound
from os import path
import re
import base64
from PyQt5.QtCore import QStandardPaths, QCoreApplication
from pathlib import Path

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
datapath = QStandardPaths.writableLocation(QStandardPaths.DataLocation)
Path(path.join(datapath, "forvo")).mkdir(parents=True, exist_ok=True)

def get_forvo_url(word, lang):
    url = "https://forvo.com/word/%s/" % word
    html = bs4.BeautifulSoup(requests.get(url, headers=HEADERS, timeout=3).text, "lxml")
    available_langs_el = html.find_all(id=re.compile(r"language-container-\w{2,4}"))
    available_langs = [re.findall(r"language-container-(\w{2,4})", el.attrs["id"])[0] for el in available_langs_el]
    lang_container = [l for l in available_langs_el if
        re.findall(r"language-container-(\w{2,4})", l.attrs["id"])[0] == lang][0]
    pronunciations = lang_container.find_all(class_="pronunciations")[0].find_all(class_="show-all-pronunciations")[0].find_all("li")
    for pronunciation in pronunciations:
        if len(pronunciation.find_all(class_="more")) == 0:
            continue

        vote_count = pronunciation.find_all(class_="more")[0].find_all(
            class_="main_actions")[0].find_all(
            id=re.compile(r"word_rate_\d+"))[0].find_all(class_="num_votes")[0]

        vote_count_inner_span = vote_count.find_all("span")
        if len(vote_count_inner_span) == 0:
            vote_count = 0
        else:
            vote_count = int(str(re.findall(r"(-?\d+).*", vote_count_inner_span[0].contents[0])[0]))

        pronunciation_dls = re.findall(r"Play\(\d+,'.+','.+',\w+,'([^']+)", pronunciation.find_all(id=re.compile(r"play_\d+"))[0].attrs["onclick"])

        is_ogg = False

        pronunciation_dl = pronunciation_dls[0]
        dl_url = "https://audio00.forvo.com/audios/mp3/" + str(base64.b64decode(pronunciation_dl), "utf-8")

    username = pronunciation.find_all(class_="ofLink", recursive=False)
    if len(username) == 0:
        username = re.findall("Pronunciation by(.*)", pronunciation.contents[2], re.S)[0].strip()
    else:
        username = username[0].contents[0]
    return dl_url
    

def dl_file(url, fname):
    r = requests.get(url, headers=HEADERS, timeout=3)
    f = open(fname, 'wb')
    for chunk in r.iter_content(chunk_size=512 * 1024): 
        if chunk: # filter out keep-alive new chunks
            f.write(chunk)
    f.close()
    return 

def play_forvo(word, lang):
    file = path.join(datapath, "forvo", f"{lang}_{word}.mp3")
    try:
        playsound(file)
        return file
    except PlaysoundException:
        try:
            dl_file(get_forvo_url(word, lang), file)
            play_forvo(word, lang)
            return file
        except:
            return None
