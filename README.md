# Simple Sentence Mining
![https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true](https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true)
![https://img.shields.io/pypi/v/ssmtool.svg](https://img.shields.io/pypi/v/ssmtool.svg)
[![Downloads](https://pepy.tech/badge/ssmtool)](https://pepy.tech/project/ssmtool)

[Join our chat on Matrix](https://webchat.kde.org/#/room/#flt:midov.pl)

[Join our chat on Telegram](https://t.me/fltchat)

Simple Sentence Mining (`ssmtool`) is a program for sentence mining, in which sentences with target vocabulary words are collected and added into a spaced repetition system (SRS) for language learning.

This program monitors your clipboard at all times and when a change is detected, the contents gets copied onto the "Sentence" field. From there, you can double click any word, and the program will send a query to Wiktionary, and display the result on the "Definition" field, while simultaneously filling in the "word" field for you. You may also double click from words in the "Definition" field to get definition, because Wiktionary sometimes simply lists the base forms of inflected words.

![Demo](https://imgur.com/rUlVWwe.gif)

For a detailed list of features and language support data, please consult the [page](https://freelanguagetools.org/posts/simple-sentence-mining-ssmtool-full-tutorial/) on my blog

## Tutorials
[Text tutorial](https://freelanguagetools.org/posts/simple-sentence-mining-ssmtool-full-tutorial/)
(The text originally on this document has since been moved there.)

[Video tutorial (Basic, a bit outdated)](https://www.youtube.com/watch?v=y79_q08Zu8k&pp=sAQA)

**USERS**: If you want to install it, go to [Releases](https://github.com/FreeLanguageTools/ssmtool/releases/) and from the latest release, download the appropriate file for your operating system. 

## Linux distro packages
[![Packaging status](https://repology.org/badge/vertical-allrepos/ssmtool.svg)](https://repology.org/project/ssmtool/versions)

## Development
To run from source, simply use `pip3 -r requirements.txt` and then `python3 ssmtool.py`.

Alternatively, you can also install a live version to your python package library with `pip3 install .`

## API documentation
If you want to leverage ssmtool to build your own plugins, you can refer to the [API Documentation](API.md)

## Feedback
You are welcome to report bugs, suggest features/enhancements, or ask for clarifications by opening a GitHub issue.

## Credits
All the definitions provided by the program come from the English Wiktionary, without which this program would never have been created.

Google dictionary API comes from [here](https://dictionaryapi.dev/).

Support for Google Translate without the use of an API key comes from the [py-googletrans project](https://github.com/ssut/py-googletrans)

App icon is made from icons by Freepik available on Flaticon.
