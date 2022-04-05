from bs4 import BeautifulSoup
import requests
from playsound import PlaysoundException, playsound
from os import path
import os
import re
import base64
from PyQt5.QtCore import QStandardPaths, QCoreApplication
from pathlib import Path
from urllib.parse import quote,unquote
from dataclasses import dataclass

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
datapath = QStandardPaths.writableLocation(QStandardPaths.DataLocation)
Path(path.join(datapath, "_forvo")).mkdir(parents=True, exist_ok=True)




def fetch_audio_all(word, lang):
    sounds = Forvo(word, lang).get_pronunciations().pronunciations
    if len(sounds) == 0:
        return {}
    result = {}
    for item in sounds:
        result[item.origin + "/" + item.headword] = item.download_url
    return result

def fetch_audio_best(word, lang):
    sounds = Forvo(word, lang).get_pronunciations().pronunciations
    if len(sounds) == 0:
        return {}
    sounds = sorted(sounds, key=lambda x: x.votes, reverse=True)
    return {sounds[0].origin + "/" + sounds[0].headword: sounds[0].download_url}

@dataclass
class Pronunciation:
    language: str
    headword: str
    query_word: str
    votes: int
    origin: str
    download_url: str
    is_ogg: bool
    id: int

    def download_pronunciation(self, session, number: str):
        folder = f'{path.join(datapath, "_forvo")}/{self.language}/{unquote(self.origin)}'
        os.makedirs(folder, exist_ok=True)
        dl_path = os.path.join(self.headword + "_" + number + (
            ".ogg" if self.is_ogg else ".mp3"))
        with open(f'{folder}/{dl_path}', "wb") as f:
            r = fetch(session, self.download_url)
            f.write(r.content)


class Forvo:
    def __init__(self, word, lang):
        self.url = "https://forvo.com/word/" + quote(word)
        self.pronunciations: List[Pronunciation] = []
        self.session = requests.Session()
        self.language = lang

    def get_pronunciations(self):
        res = requests.get(self.url, headers=HEADERS)
        if res.status_code == 200:
            page = res.text
        else:
            raise Exception("failed to fetch forvo page")
        html = BeautifulSoup(page, "lxml")
        available_langs_els = html.find_all(id=re.compile(r"language-container-\w{2,4}"))
        available_langs = [re.findall(r"language-container-(\w{2,4})", el.attrs["id"])[0] for el in available_langs_els]
        if self.language not in available_langs:
            return

        lang_container = [lang for lang in available_langs_els if
                        re.findall(r"language-container-(\w{2,4})", lang.attrs["id"])[0] == self.language][0]
        pronunciations_els = lang_container.find_all(class_="pronunciations")
        pronunciation_items: Tag = pronunciations_els[0].find_all(class_="show-all-pronunciations")[0].find_all("li")
        word = self.url.rsplit('/', 2)[-2]
        headword_el = pronunciation_items[0].find_all('span')[0]
        headword = re.findall("(.*)pronunciation$", headword_el.contents[0], re.S)[0].strip().replace("/", "[SLASH]")
        if not headword:
            headword = '--ERROR--'
        for pronunciation_item in pronunciation_items:
            if len(pronunciation_item.find_all(class_="more")) == 0:
                continue
            pronunciation_dls = re.findall(r"Play\(\d+,'.+','.+',\w+,'([^']+)",
                                        pronunciation_item.find_all(id=re.compile(r"play_\d+"))[0].attrs["onclick"])
            vote_count = pronunciation_item.find_all(class_="more")[0].find_all(
                class_="main_actions")[0].find_all(
                id=re.compile(r"word_rate_\d+"))[0].find_all(class_="num_votes")[0]
            vote_count_inner_span = vote_count.find_all("span")
            if len(vote_count_inner_span) == 0:
                vote_count = 0
            else:
                vote_count = int(str(re.findall(r"(-?\d+).*", vote_count_inner_span[0].contents[0])[0]))
            pronunciation_dls = re.findall(r"Play\(\d+,'.+','.+',\w+,'([^']+)",
                                        pronunciation_item.find_all(id=re.compile(r"play_\d+"))[0].attrs["onclick"])
            is_ogg = False
            if len(pronunciation_dls) == 0:
                pronunciation_dl = re.findall(r"Play\(\d+,'[^']+','([^']+)",
                                            pronunciation_item.find_all(id=re.compile(r"play_\d+"))[0].attrs[
                                                "onclick"])[0]
                dl_url = "https://audio00.forvo.com/ogg/" + str(base64.b64decode(pronunciation_dl), "utf-8")
                is_ogg = True
            else:
                pronunciation_dl = pronunciation_dls[0]
                dl_url = "https://audio00.forvo.com/audios/mp3/" + str(base64.b64decode(pronunciation_dl), "utf-8")
            data_id = int(pronunciation_item.find_all(class_="more")[0].find_all(class_="main_actions")[0].find_all(
                class_="share")[0].attrs["data-id"])
            username = pronunciation_item.find_all(class_="ofLink", recursive=False)
            if len(username) == 0:
                username = re.findall("Pronunciation by(.*)", pronunciation_item.contents[2], re.S)[0].strip()
            else:
                username = username[0].contents[0]
            origin = username
            pronunciation_object = Pronunciation(self.language,
                                                headword,
                                                word,
                                                vote_count,
                                                origin,
                                                dl_url,
                                                is_ogg,
                                                data_id,
                                                )

            self.pronunciations.append(pronunciation_object)
        print(self.pronunciations)
        return self

if __name__ == "__main__":
    print(fetch_audio_all("what", "en"))
    print(fetch_audio_best("goodbye", "en"))