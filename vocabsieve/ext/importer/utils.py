from ...constants import LookUpResults
from datetime import datetime as dt
from itertools import zip_longest

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

def grouper(iterable, n, *, incomplete='fill', fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, fillvalue='x') --> ABC DEF Gxx
    # grouper('ABCDEFG', 3, incomplete='strict') --> ABC DEF ValueError
    # grouper('ABCDEFG', 3, incomplete='ignore') --> ABC DEF
    args = [iter(iterable)] * n
    if incomplete == 'fill':
        return zip_longest(*args, fillvalue=fillvalue)
    if incomplete == 'strict':
        return zip(*args, strict=True)
    if incomplete == 'ignore':
        return zip(*args)
    else:
        raise ValueError('Expected fill, strict, or ignore')
