---
title: Resources
layout: default
nav_order: 7
---

# Resources for VocabSieve

VocabSieve supports a range of different local resources, which you can use without an internet connection. 
## Supported files
- StarDict, the most commonly available free dictionary format online
- Migaku (.json)
- JSON (.json, plain key-value pairs)
- Kaikki.org Wiktionary data dumps
- CSV
- DSL
- MDX
    > {: .note}
    MDX dictionaries are often in heavy HTML format for style, but VocabSieve can only handle text-based definitions. They are converted into text before being shown, which may not always work well.
- JSON frequency lists (as a simple list of words in json format) 
- Sound libraries (a directory of audio files)

## Dictionaries
Listed in order of preference by author.

### Kaikki Wiktionary dumps

High-quality parsed data of Wiktionary in various languages. Prefer these over the online Wiktionary API as they contain more information. The English and French Wiktionaries (note this is the language the entries are written in) contain a large number of entries in other languages. All the other versions also contain a lot of entries in their own language, which can be useful as monolingual dictionaries.

<https://kaikki.org/>

### Hu Zheng (StarDict author) personal website, over 100 dictionaries

StarDict dictionaries converted by StarDict's author from various formats. They are usually of decent quality and is plaintext, which is suitable for display in VocabSieve and Anki. StarDicts need to be extracted first before importing. Select the .ifo file in the extracted folder.

The website has been dead on a while, but many of the files are archived on Wayback Machine:

<https://web.archive.org/web/20230717122310/https://download.huzheng.org/>

### Lingvo DSL

Rutracker GoldenDict Dictionaries (Russian, English, Ukrainian)

<https://rutracker.org/forum/viewtopic.php?t=3369767> (Page in Russian, click “скачать” to download torrent)

Website with Lingvo dictionaries (Website in Russian; Some free resources but mostly requires payment)

<https://dic.1963.ru/>

Another website with Lingvo dictionaries (Website in Russian, mostly free resources)

<http://lingvodics.com/main/>

A bunch of dictionaries for GoldenDict, organized by language. Avoid MDX format as they usually look worse than DSL.

<https://cloud.freemdict.com/index.php/s/pgKcDcbSDTCzXCs>

### Apple Dictionaries, 41 dictionaries, some bilingual

<https://cloud.freemdict.com/index.php/s/HsC7ybBWsbZ7B4N>

Navigate to "json" folder and download items for your language. Note that the bilingual dictionaries listed include entries in **both** directions. For example, an English-Spanish dictionary contains both English words defined in Spanish as well as Spanish words defined in English. You do not need to extract the files in order to import them.

### Migaku dictionaries

Migaku Official MEGA Folder, 11 languages

<https://mega.nz/folder/eyYwyIgY#3q4XQ3BhdvkFg9KsPe5avw/folder/bz4ywa5A>

## Frequency lists

Lemmatized English frequency list

<https://github.com/FreeLanguageTools/resources/raw/master/freq/freq_en.json.gz>

Lemmatized Russian frequency list

<https://github.com/FreeLanguageTools/resources/raw/master/freq/freq_ru.json.gz>

## Cognate data
CogNet processed data processed for VocabSieve, includes all languages, may take a while to import.

<https://github.com/FreeLanguageTools/resources/raw/master/cognates.json.gz>

## Audio folders
These need to be extracted into a folder first before importing. The containining folder should be selected for import. Do not delete the files as they are not copied.

Lingua Libre sound libraries

<https://lingualibre.org/datasets/>

Forvo dump in various languages (may not be as complete as the online version)

<https://cloud.freemdict.com/index.php/s/pgKcDcbSDTCzXCs?path=%2F0%20Forvo%20audio>