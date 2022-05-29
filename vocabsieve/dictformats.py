from readmdict import MDX
from .dsl import Reader
from bidict import bidict
from typing import Dict
import os
import re
import csv
import json

supported_dict_formats = bidict({
    "stardict": "StarDict",
    "json": "Simple JSON",
    "migaku": "Migaku Dictionary",
    "freq": "Frequency list",
    "audiolib": "Audio Library",
    "mdx": "MDX",
    "dsl": "Lingvo DSL",
    "csv": "CSV",
    "tsv": "TSV (Tabfile)"
})

supported_dict_extensions = [
    ".json", ".ifo", ".mdx", ".dsl", ".dz", ".csv", ".tsv"
]


def dictinfo(path) -> Dict[str, str]:
    "Get information about dictionary from file path"
    basename, ext = os.path.splitext(path)
    basename = os.path.basename(basename)
    if os.path.isdir(path):
        return {"type": "audiolib", "basename": basename, "path": path}
    if ext not in supported_dict_extensions:
        raise NotImplementedError("Unsupported format")
    elif ext == ".json":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, list):
                if isinstance(d[0], str):
                    return {
                        "type": "freq",
                        "basename": basename,
                        "path": path}
                return {
                    "type": "migaku",
                    "basename": basename,
                    "path": path}
            elif isinstance(d, dict):
                return {"type": "json", "basename": basename, "path": path}
    elif ext == ".ifo":
        return {"type": "stardict", "basename": basename, "path": path}
    elif ext == ".mdx":
        return {"type": "mdx", "basename": basename, "path": path}
    elif ext == ".dsl":
        return {"type": "dsl", "basename": basename, "path": path}
    elif ext == ".dz":
        if basename.endswith(".dsl"):
            return {"type": "dsl", "basename": basename.rstrip(".dsl"), "path": path}
    elif ext == ".tsv":
        return {"type": "tsv", "basename": basename, "path": path}
    elif ext == ".csv":
        return {"type": "csv", "basename": basename, "path": path}


def parseMDX(path) -> Dict[str, str]:
    mdx = MDX(path)
    stylesheet_lines = mdx.header[b'StyleSheet'].decode().splitlines()
    stylesheet_map = {}
    for line in stylesheet_lines:
        if line.isnumeric():
            number = int(line)
        else:
            stylesheet_map[number] = stylesheet_map.get(number, "") + line
    newdict = {}  # This temporarily stores the new entries
    i = 0
    prev_headword = ""
    for item in mdx.items():
        headword, entry = item
        headword = headword.decode()
        entry = entry.decode()
        # The following applies the stylesheet
        if stylesheet_map:
            entry = re.sub(
                r'`(\d+)`',
                lambda g: stylesheet_map.get(g.group().strip('`')),
                entry
            )
        entry = entry.replace("\n", "").replace("\r", "")
        # Using newdict.get would become incredibly slow,
        # here we exploit the fact that they are alphabetically ordered
        if prev_headword == headword:
            newdict[headword] = newdict[headword] + entry
        else:
            newdict[headword] = entry
        prev_headword = headword
    return newdict


def parseDSL(path) -> Dict[str, str]:
    r = Reader()
    r.open(path)
    newdict = {}
    for headwords, definition in iter(r):
        for headword in headwords:
            if "{" in headword:
                headword = re.sub(r'\{[^}]+\}', "", headword)
            definition = re.sub(r'(\<b\>\d+\.\</b\>)\s+\<br>', r'\1 ', definition)
            newdict[headword] = removeprefix(definition, "<br>")
    return newdict


# There is a str.removeprefix function, but it is implemented
# only in python 3.9. Copying the implementation here
def removeprefix(self: str, prefix: str, /) -> str:
    if self.startswith(prefix):
        return self[len(prefix):]
    else:
        return self[:]


def parseCSV(path) -> Dict[str, str]:
    newdict = {}
    with open(path, newline="") as csvfile:
        data = csv.reader(csvfile)
        for row in data:
            newdict[row[0]] = row[1]
    return newdict


def parseTSV(path) -> Dict[str, str]:
    newdict = {}
    with open(path, newline="") as csvfile:
        data = csv.reader(csvfile, delimiter="\t")
        for row in data:
            newdict[row[0]] = row[1]
    return newdict
