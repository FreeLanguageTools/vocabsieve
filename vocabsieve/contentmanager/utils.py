import os
from typing import Dict
from ebooklib import epub
import ebooklib
from lxml import etree
from charset_normalizer import from_bytes

supported_extensions = {".fb2", ".epub", ".srt", ".vtt", ".ass"}


def tostr(s):
    return str(
        from_bytes(
            etree.tostring(
                s,
                encoding='utf8',
                method='text')).best()).strip()

def remove_ns(s: str) -> str: return str(s).split("}")[-1]

def ebook2text(path):
    basename, ext = os.path.splitext(path)
    if ext == '.epub':
        book = epub.read_epub(path)
        chapters = []
        for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            tree = etree.fromstring(doc.get_content())
            notags = etree.tostring(tree, encoding='utf8', method="text")
            data = str(from_bytes(notags).best()).strip()
            if len(data.splitlines()) < 2:
                continue
            content = "\n".join(data.splitlines())
            chapters.append(content)
        return "\n\n\n\n".join(chapters)
    elif ext == '.fb2':
        with open(path, 'rb') as f:
            data = f.read()
            tree = etree.fromstring(data)
        chapters = []
        already_seen = False
        for el in tree:
            tag_nons = remove_ns(el.tag)
            if tag_nons == "body" and not already_seen:
                already_seen = True
                for section in el:
                    current_chapter = ""
                    for item in section:
                        if remove_ns(item.tag) == "title":
                            current_chapter = tostr(item) + "\n\n"
                        else:
                            current_chapter += tostr(item) + "\n"
                    chapters.append(current_chapter)
        return "\n\n\n\n".join(chapters)
