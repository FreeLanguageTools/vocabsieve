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

## StarDict


### Hu Zheng (StarDict author) personal website, over 100 dictionaries

The website has been dead on a while, but some of the files are archived on Wayback Machine:

<https://web.archive.org/web/20230717122310/https://download.huzheng.org/>

### GTongue Dictionaries

<https://sites.google.com/site/gtonguedict/home/stardict-dictionaries> 



## Migaku

Migaku Official MEGA Folder, 11 languages

<https://mega.nz/folder/eyYwyIgY#3q4XQ3BhdvkFg9KsPe5avw/folder/bz4ywa5A>

## Simple JSONs

### Apple Dictionaries, 41 dictionaries, some bilingual

<https://cloud.freemdict.com/index.php/s/HsC7ybBWsbZ7B4N>

Navigate to "json" folder and download items for your language. Note that the bilingual dictionaries listed include entries in **both** directions. For example, an English-Spanish dictionary contains both English words defined in Spanish as well as Spanish words defined in English. You do not need to extract the files in order to import them.

## Kaikki Wiktionary dumps

High-quality parsed data of Wiktionary in various languages. Prefer these over the online Wiktionary API as they contain more information.

<https://kaikki.org/>


## Lingvo DSL

Rutracker GoldenDict Dictionaries (Russian, English, Ukrainian)

<https://rutracker.org/forum/viewtopic.php?t=3369767> (Page in Russian, click “скачать” to download torrent)

Website with Lingvo dictionaries (Website in Russian; Some free resources but mostly requires payment)

<https://dic.1963.ru/>

Another website with Lingvo dictionaries (Website in Russian, mostly free resources)

<http://lingvodics.com/main/>

A bunch of dictionaries for GoldenDict, organized by language. Avoid MDX format as they usually look worse than DSL.

<https://cloud.freemdict.com/index.php/s/pgKcDcbSDTCzXCs>

## Frequency lists

Lemmatized English frequency list

<https://github.com/FreeLanguageTools/resources/raw/master/freq/freq_en.json.gz>

Lemmatized Russian frequency list

<https://github.com/FreeLanguageTools/resources/raw/master/freq/freq_ru.json.gz>

## Cognate data
CogNet processed data, includes all languages, may take a while to import.

<https://github.com/FreeLanguageTools/resources/raw/master/cognates.json.gz>