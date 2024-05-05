from datetime import datetime as dt
import glob
import os
from ..global_names import logger


def get_uniques(l: list):
    return list(set(l) - set([""]))


def uniq_preserve_order(l: list) -> list:
    return sorted(set(l), key=lambda x: l.index(x))


def date_to_timestamp(datestr: str):
    return dt.strptime(datestr, "%Y-%m-%d %H:%M:%S").timestamp()


def findDBpath(path) -> str:
    # KOReader settings may be in a hidden directory
    paths = glob.glob(os.path.join(path, "**/vocabulary_builder.sqlite3"), recursive=True)\
        + glob.glob(os.path.join(path, ".*/**/vocabulary_builder.sqlite3"), recursive=True)
    if paths:
        return paths[0]
    else:
        raise FileNotFoundError("Cannot find vocabulary_builder.sqlite3")


def koreader_scandir(path):
    filelist = []
    for filetype in ["epub", "fb2", "fb2.zip", "pdf"]:
        files = glob.glob(os.path.join(path, "**/*." + filetype), recursive=True)
        for filename in files:
            if os.path.exists(os.path.join(os.path.dirname(filename),
                                           filename.removesuffix(filetype) + "sdr",
                                           "metadata." + filetype.split(".")[-1] + ".lua")):
                filelist.append(filename)
    logger.info(f"Found {len(filelist)} book files in {path}: {filelist}")
    return filelist


def findHistoryPath(path):
    # KOReader settings may be in a hidden directory
    paths = glob.glob(os.path.join(path, "**/lookup_history.lua"), recursive=True)\
        + glob.glob(os.path.join(path, ".*/**/lookup_history.lua"), recursive=True)
    if paths:
        return paths[0]
    else:
        return ""
