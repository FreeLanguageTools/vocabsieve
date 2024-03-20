# mypy: ignore-errors
from ..cached_get import cached_get
from ..models import AudioSource, LemmaPolicy, AudioLookupResult

from bs4 import BeautifulSoup
from typing import List, Dict
import requests
from os import path
import os
import re
import base64
from urllib.parse import quote, unquote
from dataclasses import dataclass
from ..global_names import settings
from loguru import logger


@dataclass
class Pronunciation:
    language: str
    accent: str
    headword: str
    query_word: str
    votes: int
    origin: str
    download_url: str
    id: int


@dataclass
class PronunciationList:
    language: str
    accent: str
    pronunciation_list: dict


class Forvo:
    def __init__(self, word, lang, accent=""):
        self.url = "https://forvo.com/word/" + quote(word)
        self.pronunciations = []
        self.session = requests.Session()
        self.language = lang
        self.accent = accent

    def get_pronunciations(self):
        res = cached_get(self.url, forvo_headers=True)
        if res.status_code == 200:
            page = res.text
        else:
            raise Exception("failed to fetch forvo page")
        html = BeautifulSoup(page, "lxml")
        pronunciations_list_regex = re.compile(r"^pronunciations-list-([a-z]+)(?:_([a-z]+))?")
        available_pronunciations_lists = []

        for pronunciations_list in html.find_all(id=pronunciations_list_regex):
            match = pronunciations_list_regex.match(pronunciations_list["id"])
            if match:
                available_pronunciations_lists.extend(
                    PronunciationList(match.group(1), match.group(2), li)
                    for li in pronunciations_list.find_all("li")
                )

        available_pronunciations_lists = list(
            filter(
                lambda el: el.language == self.language,
                available_pronunciations_lists))
        if self.accent:
            available_pronunciations_lists = list(
                filter(
                    lambda el: el.accent == self.accent,
                    available_pronunciations_lists))

        for l in available_pronunciations_lists:
            pronunciation_item = l.pronunciation_list
            if len(pronunciation_item.find_all(class_="more")) == 0:
                continue
            vote_count = pronunciation_item.find_all(class_="more")[0].find_all(
                class_="main_actions")[0].find_all(
                id=re.compile(r"word_rate_\d+"))[0].find_all(class_="num_votes")[0]
            vote_count_inner_span = vote_count.find_all("span")
            if len(vote_count_inner_span) == 0:
                vote_count = 0
            else:
                vote_count = int(
                    str(re.findall(r"(-?\d+).*", vote_count_inner_span[0].contents[0])[0]))
            pronunciation_dls = re.findall(
                r"Play\(\d+,'.+','.+',\w+,'([^']+)",
                pronunciation_item.find_all(
                    id=re.compile(r"play_\d+"))[0].attrs["onclick"])
            audio_extension = settings.value("audio_format", "mp3")
            if len(pronunciation_dls) == 0:
                pronunciation_dl = re.findall(
                    r"Play\(\d+,'[^']+','([^']+)",
                    pronunciation_item.find_all(
                        id=re.compile(r"play_\d+"))[0].attrs["onclick"])[0]
                dl_url = "https://audio00.forvo.com/" + audio_extension + "/" + \
                    str(base64.b64decode(pronunciation_dl), "utf-8")
            else:
                pronunciation_dl = pronunciation_dls[0]
                dl_url = "https://audio00.forvo.com/audios/" + audio_extension + "/" + \
                    str(base64.b64decode(pronunciation_dl), "utf-8")
            # forvo URL is interchangeable - replace all instances of mp3 with ogg and it'll provide a different format
            dl_url = dl_url.rsplit(".", 1)[0] + "." + audio_extension

            #data_id = int(
            #    pronunciation_item.find_all(
            #        class_="more")[0].find_all(
            #        class_="main_actions")[0].find_all(
            #        class_="share")[0].attrs["data-id"])
            username = pronunciation_item.find_all(
                class_="info", recursive=False)[0].find_all(
                    class_="ofLink")
            origin = ""
            if len(username) == 0:
                for pronunciation_item_content in pronunciation_item.contents:
                    if not hasattr(pronunciation_item_content, "contents"):
                        continue

                    tempOrigin = re.findall(
                        "Pronunciation by(.*)",
                        pronunciation_item_content.contents[0],
                        re.S)

                    if len(tempOrigin) != 0:
                        origin = tempOrigin[0].strip()
                        break
                    continue
            else:
                origin = username[0].contents[0]
            word = unquote(self.url.rsplit('/', 2)[-1])
            pronunciation_object = Pronunciation(self.language,
                                                 l.accent,
                                                 word.strip(),
                                                 word.strip(),
                                                 vote_count,
                                                 origin.strip(),
                                                 dl_url,
                                                 -1,  # data_id, can't obtain anymore
                                                 )

            self.pronunciations.append(pronunciation_object)
        self.pronunciations = sorted(self.pronunciations, key=lambda x: x.votes, reverse=True)
        return self


def fetch_audio_all(word: str, lang: str) -> dict[str, str]:
    sounds = Forvo(word, lang).get_pronunciations().pronunciations
    result: dict[str, str] = {}
    if len(sounds) == 0:
        return result
    for item in sounds:
        file_extension = item.download_url.rsplit(".", 1)[-1]
        accent = f"({item.accent})" if item.accent else ""
        result[f"{item.origin}{accent}/{item.headword}.{file_extension}"] = item.download_url
    return result


def fetch_audio_best(word: str, lang: str) -> Dict[str, str]:
    sounds = Forvo(word, lang).get_pronunciations().pronunciations
    if len(sounds) == 0:
        return {}
    return {
        sounds[0].origin +
        "/" +
        sounds[0].headword: sounds[0].download_url}


class ForvoAudioSource(AudioSource):
    def __init__(self, langcode: str, lemma_policy: LemmaPolicy) -> None:
        super().__init__("Forvo", langcode, lemma_policy)

    def _lookup(self, word: str) -> AudioLookupResult:
        logger.info(f"Forvo lookup {word}")
        try:
            return AudioLookupResult(audios=fetch_audio_all(word, self.langcode))
        except Exception as e:
            return AudioLookupResult(error=repr(e))
