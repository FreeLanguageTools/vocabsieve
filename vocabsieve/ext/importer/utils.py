from ...constants import LookUpResults
from datetime import datetime as dt

def get_uniques(l: list):
    return list(set(l) - set([""]))


def uniq_preserve_order(l: list) -> list:
    return sorted(set(l), key=lambda x: l.index(x))

def truncate_middle(s, n):
    if len(s) <= n:
        return s
    n_2 = int(n / 2 - 3)
    n_1 = int(n - n_2 - 3)
    return '{0}...{1}'.format(s[:n_1], s[-n_2:])

def genPreviewHTML(sentence: str, item: LookUpResults, word_original: str = "") -> str:
    result = f'''<center>{sentence.replace(word_original, f"<b>{word_original}</b>")}</center>
        <hr>
        <center>
            <b>{item.get('word', '')}</b>:
            <br>{item.get('definition', '').strip()}</center>'''
    if item.get('definition2', ''):
        result += f"<hr><center>{item.get('definition2', '')}</center>"
    return result

def date_to_timestamp(datestr: str):
    return dt.strptime(datestr, "%Y-%m-%d %H:%M:%S").timestamp()