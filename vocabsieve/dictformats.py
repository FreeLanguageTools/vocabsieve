from typing import TextIO
from loguru import logger
from readmdict import MDX
from bidict import bidict
import os
import re
import lzma
import gzip
import bz2
import csv
import json
from itertools import groupby
from operator import itemgetter


supported_dict_formats = bidict({
    "stardict": "StarDict",
    "json": "Simple JSON",
    "migaku": "Migaku Dictionary",
    "wiktdump": "Wiktionary dump",
    "freq": "Frequency list",
    "audiolib": "Audio Library",
    "mdx": "MDX",
    "dsl": "Lingvo DSL",
    "csv": "CSV",
    "tsv": "TSV (Tabfile)",
    "cognates": "Cognate data"
})

supported_dict_extensions = [
    ".json", ".jsonl", ".ifo", ".mdx", ".dsl", ".dz", ".csv", ".tsv", ".xz", ".bz2", ".gz"
]


def zopen(path) -> TextIO:
    if path.endswith('.xz'):
        return lzma.open(path, 'rt', encoding='utf-8')  # type:ignore
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8')  # type:ignore
    if path.endswith('.bz2'):
        return bz2.open(path, 'rt', encoding='utf-8')  # type:ignore
    return open(path, 'rt', encoding='utf-8')  # type:ignore


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
        return gzip.open(path, mode="rt", encoding=correct_encoding)  # type:ignore
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
    if ext in ('.json', '.jsonl', '.xz', '.bz2', '.gz'):
        with zopen(path) as f:
            try:
                d = json.load(f)
                if isinstance(d, list):
                    if isinstance(d[0], str):  # Frequency list is a list of strings
                        return {
                            "type": "freq",
                            "basename": basename,
                            "path": path}
                    elif isinstance(d[0], dict):  # Migaku dictionary is a list of dicts (records)
                        return {
                            "type": "migaku",
                            "basename": basename,
                            "path": path}
                elif isinstance(d, dict):
                    if isinstance(d[next(iter(d))], str):  # Simple JSON is a dict from word to definition
                        return {"type": "json", "basename": basename, "path": path}
                    elif isinstance(d[next(iter(d))], dict):  # Cognates is a dict from language to dict from word to definition
                        return {"type": "cognates", "basename": basename, "path": path}
            except json.decoder.JSONDecodeError:
                f.seek(0)
                first_line = f.readline()
                logger.debug("First line of bad json file: ", first_line)
                logger.debug("Detected Kaikki wiktionary dump")
                if json.loads(first_line):
                    return {"type": "wiktdump", "basename": basename, "path": path}
            raise NotImplementedError(f"File {path} is not a supported json format")
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
    prev_headword = ""
    for item in mdx.items():
        headword_bytes, entry_bytes = item
        headword = headword_bytes.decode()
        entry = entry_bytes.decode()  # type: ignore
        # The following applies the stylesheet
        if stylesheet_map:
            entry = re.sub(
                r'`(\d+)`',
                lambda g: stylesheet_map.get(int(g.group().strip('`'))),  # type:ignore
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
    with dslopen(path) as f:  # type:ignore
        lines: list[str] = f.readlines()  # type:ignore
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
            if item.endswith(".wav"):  # Don't include audio file names
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
    with open(path, newline="", encoding='utf-8') as csvfile:
        data = csv.reader(csvfile)
        for row in data:
            newdict[row[0]] = row[1]
    return newdict


def parseTSV(path) -> dict[str, str]:
    newdict = {}
    with open(path, newline="", encoding='utf-8') as csvfile:
        data = csv.reader(csvfile, delimiter="\t")
        for row in data:
            newdict[row[0]] = row[1]
    return newdict


def parseKaikki(path, lang) -> dict[str, str]:
    '''
    Parse a wiktionary dump from Kaikki/Wikiextract
    (https://github.com/tatuylonen/wiktextract)
    The format is lines of json objects, each containing a word and its definition
    '''
    print("Parsing Kaikki wiktionary dump at " + path)
    items: list[tuple[str, str]] = []

    if path.endswith(".json"):
        logger.warning("Legacy Kaikki JSON dump detected, this may cause issues. New exports have a .jsonl suffix")

    with zopen(path) as f:
        logger.debug("Parsing Kaikki wiktionary dump at " + path)
        logger.debug("Only importing entries in language " + lang)
        for line in f:
            data = json.loads(line)
            # Kaikki dumps may have multiple languages, skip others for now
            if data.get("lang_code") == lang:
                items.append((data['word'], kaikki_line_to_textdef(data)))
        logger.debug(f"Found {len(items)} entries")
    # Combine all definitions for each headword
    res = dict((word, "\n\n".join([item[1] for item in itr]))
               for word, itr in groupby(items, itemgetter(0)))
    logger.debug(f"For {len(res)} headwords")
    return res


def kaikki_line_to_textdef(row: dict) -> str:
    res = ""
    if row.get("pos"):
        res += f"<i>{row['pos'].capitalize()}</i>"
    res += "\n<strong>"
    if row.get("head_templates"):
        res += f"{row['head_templates'][-1]['expansion']}"
    res += "</strong>\n"
    if row.get("sounds"):
        for item in row['sounds']:
            if item.get('ipa'):
                res += f" {item['ipa']} "
                if item.get('tags'):
                    res += f" [{','.join(item['tags'])}]"
    count = 1
    if row.get("senses"):
        for item in row['senses']:
            if item.get("raw_glosses"):
                for defi in item['raw_glosses']:
                    res += "\n" + str(count) + ". " + defi
                    count += 1
            elif item.get("glosses"):
                for defi in item['glosses']:
                    res += "\n" + str(count) + ". " + defi
                    count += 1
    return res
