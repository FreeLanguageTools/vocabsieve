from typing import TextIO
from readmdict import MDX
from bidict import bidict
import os
import re
import lzma
import gzip
import bz2
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
    "tsv": "TSV (Tabfile)",
    "cognates": "Cognate data"
})

supported_dict_extensions = [
    ".json", ".ifo", ".mdx", ".dsl", ".dz", ".csv", ".tsv", ".xz", ".bz2", ".gz"
]


def zopen(path) -> TextIO:
    if path.endswith('.xz'):
        return lzma.open(path, 'rt', encoding='utf-8') # type:ignore
    elif path.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8') # type:ignore
    elif path.endswith('.bz2'):
        return bz2.open(path, 'rt', encoding='utf-8') # type:ignore
    else:
        return open(path, 'rt', encoding='utf-8') # type:ignore
    
def dslopen(path) -> TextIO:
    "Open dsl. Can be .dsl or .dsl.dz. Can be UTF-8 or UTF-16"
    correct_encoding = ""
    for testEncoding in ["utf-8", "utf-16"]:
        if path.endswith(".dsl.dz"):
            with gzip.open(path, mode="rt", encoding=testEncoding) as f:
                try:
                    for _ in range(50):
                        f.readline()
                except UnicodeDecodeError:
                    continue
                else:
                    correct_encoding = testEncoding
                    break
        elif path.endswith(".dsl"):
            with open(path, mode="rt", encoding=testEncoding) as f:
                try:
                    for _ in range(50):
                        f.readline()
                except UnicodeDecodeError:
                    continue
                else:
                    correct_encoding = testEncoding
                    break
    else:
        raise ValueError("Failed to detect encoding")
    if path.endswith(".dsl.dz"):
        return gzip.open(path, mode="rt", encoding=correct_encoding) # type:ignore
    elif path.endswith(".dsl"):
        return open(path, mode="rt", encoding=correct_encoding)
    else:
        raise ValueError("Not a DSL file")

def dictinfo(path) -> dict[str, str]:
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
                else:
                    return {
                        "type": "migaku",
                        "basename": basename,
                        "path": path}
            elif isinstance(d, dict):
                return {"type": "json", "basename": basename, "path": path}
            else:
                raise NotImplementedError("Unsupported format")
    elif ext == ".ifo":
        return {"type": "stardict", "basename": basename, "path": path}
    elif ext == ".mdx":
        return {"type": "mdx", "basename": basename, "path": path}
    elif ext == ".dsl":
        return {"type": "dsl", "basename": basename, "path": path}
    elif ext == ".dz":
        if basename.endswith(".dsl"):
            return {"type": "dsl", "basename": basename.rstrip(".dsl"), "path": path}
        else:
            raise NotImplementedError("Unsupported format")
    elif ext == ".tsv":
        return {"type": "tsv", "basename": basename, "path": path}
    elif ext == ".csv":
        return {"type": "csv", "basename": basename, "path": path}
    elif ext == ".xz" or ext == ".bz2" or ext == ".gz":
        if basename.endswith(".json"):
            with zopen(path) as f:
                basename = basename.removesuffix(".json")
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
                    if isinstance(d[next(iter(d))], dict):
                        return {
                            "type": "cognates",
                            "basename": basename,
                            "path": path}
                    elif isinstance(d[next(iter(d))], str):
                        return {
                            "type": "json",
                            "basename": basename,
                            "path": path
                        }
                    else:
                        raise NotImplementedError("Unsupported format")
                else:
                    raise NotImplementedError("Unsupported format")
        else:
            raise NotImplementedError("Unsupported format")
    else:
        raise NotImplementedError("Unsupported format" + basename + ext)

def parseMDX(path) -> dict[str, str]:
    mdx = MDX(path)
    stylesheet_lines = mdx.header[b'StyleSheet'].decode().splitlines()
    stylesheet_map: dict[int, str] = {}
    for line in stylesheet_lines:
        if line.isnumeric():
            number = int(line)
            stylesheet_map[number] = stylesheet_map.get(number, "") + line
    newdict: dict[str, str] = {}  # This temporarily stores the new entries
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
                lambda g: stylesheet_map.get(int(g.group().strip('`'))), # type:ignore
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


def parseDSL(path) -> dict[str, str]:
    """Parse Lingvo DSL dictionary
    This produces much simpler markup than the pyglossary implementation
    """
    with dslopen(path) as f: # type:ignore
        lines: list[str] = f.readlines() # type:ignore
    allLines = "".join(lines[5:])
    allLines = allLines.replace("[", "<")
    allLines = allLines.replace("]", ">")
    allLines = allLines.replace("{{", "<")
    allLines = allLines.replace("}}", ">")
    allLines = allLines.replace("<m0>", "")
    allLines = allLines.replace("<m1>", "  ")
    allLines = allLines.replace("<m2>", "    ")
    allLines = allLines.replace("<m3>", "      ")
    allLines = allLines.replace("\\", "/")

    allLines = re.sub('<[^<]+?>', '', allLines)
    allLines = allLines.replace("&quot;", '"')
    allLines = allLines.replace("{}", "")

    current_term = ""
    current_defi = ""
    data = {}
    items = []
    for item in allLines.splitlines():
        if not item.startswith("#") and not item.startswith("\t"):
            data[current_term] = re.sub(r'(\d+\.)<br>\s*(\D+)', r'\1 \2', current_defi)\
                                   .removesuffix("<br>").strip()

            current_defi = ""
            current_term = item
        if item.startswith("\t"):
            items.append(item)
            if item.endswith(".wav"): # Don't include audio file names
                continue
            current_defi += item.removeprefix("\t").replace("~", current_term) + "<br>"

    return data

def xdxf2text(xdxf_string: str) -> str:
    """Transform an XDXF stardict entry into plain text
    This largely follows the implementation in sdcv without the color"""
    # Remove content in <k> tags
    s = re.sub(r"<k>\w+</k>", "", xdxf_string, flags=re.IGNORECASE)
    # Convert <tr> into [ ]
    s = s.replace("<tr>", "[").replace("</tr>", "]").replace("<TR>", "[").replace("</TR>", "]")
    # Remove blockquotes because they start with b
    s = re.sub(r"</?blockquote>", "", s, flags=re.IGNORECASE)
    # Convert kref to bolds just like in sdcv
    s = s.replace("<kref>", "<b>").replace("</kref>", "</b>").replace("<KREF>", "<b>").replace("</KREF>", "</b>")
    # Remove all other tags than i and b
    s = re.sub(r"<(?!i|/i|b|/b).*?>", "", s, flags=re.IGNORECASE)
    # Substitute back in some symbols
    s = s.replace("&gt;", ">").replace("&lt;", "<")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&")
    s = s.replace("&apos;", "'")
    return s.strip()

def parseCSV(path) -> dict[str, str]:
    newdict = {}
    with open(path, newline="") as csvfile:
        data = csv.reader(csvfile)
        for row in data:
            newdict[row[0]] = row[1]
    return newdict


def parseTSV(path) -> dict[str, str]:
    newdict = {}
    with open(path, newline="") as csvfile:
        data = csv.reader(csvfile, delimiter="\t")
        for row in data:
            newdict[row[0]] = row[1]
    return newdict

