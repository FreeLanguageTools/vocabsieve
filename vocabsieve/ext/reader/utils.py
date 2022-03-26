import ebooklib
from ebooklib import epub
from charset_normalizer import from_bytes
from lxml import etree
import os

remove_ns = lambda s: str(s).split("}")[-1]
tostr = lambda s: str(from_bytes(etree.tostring(s, encoding='utf8', method='text')).best()).strip()
tohtml = lambda s: str(from_bytes(etree.tostring(s, encoding='utf8')).best()).strip()


def parseEpub(path):
    book = epub.read_epub(path)
    title = book.get_metadata('DC', 'title') or ""
    author = book.get_metadata('DC', 'creator') or ""
    chapters = []
    for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        tree = etree.fromstring(doc.get_content())
        notags = etree.tostring(tree, encoding='utf8', method='text')
        data = str(from_bytes(notags).best()).strip()
        if len(data.splitlines()) < 2:
            continue
        ch_name = data.splitlines()[0]
        content = "\n".join(data.splitlines()[1:])
        chapters.append(f"######{ch_name}\n"+content)
    return {"title": title[0][0], "author": author[0][0], "chapters": chapters}

def parseFb2(path):
    with open(path, 'rb') as f:
        data = bytes(f.read())
        tree = etree.fromstring(data)
    chapters = [] 
    already_seen = False
    authors = []
    title = ""
    for el in tree:
        tag_nons = remove_ns(el.tag)
        if tag_nons == "description":
            for item in el:
                if remove_ns(item.tag) == "title-info":
                    for subitem in item:
                        if remove_ns(subitem.tag) == "author":
                            authors.append(" ".join(tostr(subitem).split("\n")))
                        if remove_ns(subitem.tag) == "book-title":
                            title = tostr(subitem)
        if tag_nons == "body" and not already_seen:
            already_seen = True
            for section in el:
                current_chapter = ""
                for item in section:
                    if remove_ns(item.tag) == "title":
                        current_chapter = "######" + tostr(item) + "\n"
                    else:
                        current_chapter += tostr(item) + "\n"
                chapters.append(current_chapter)
    return {
        "author": ", ".join(authors),
        "title": title,
        "chapters": chapters
    }

def parseBook(path):
    if os.path.splitext(path)[1] == ".epub":
        return parseEpub(path)
    elif os.path.splitext(path)[1] == ".fb2":
        return parseFb2(path)
    elif os.path.splitext(path)[1] == ".txt":
        return parseTxt(path)
    else:
        raise Exception("Filetype unknown")

ALLOWED_EXTENSIONS = {'txt', 'epub', 'fb2'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS