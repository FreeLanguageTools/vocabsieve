# Simple Sentence Mining
![https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true](https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true)
![https://img.shields.io/pypi/v/ssmtool.svg](https://img.shields.io/pypi/v/ssmtool.svg)
[![Downloads](https://pepy.tech/badge/ssmtool)](https://pepy.tech/project/ssmtool)

Simple Sentence Mining (`ssmtool`) is a program for sentence mining, in which sentences with target vocabulary words are collected and added into a spaced repetition system (SRS) for language learning.

This program monitors your clipboard at all times and when a change is detected, the contents gets copied onto the "Sentence" field. From there, you can double click any word, and the program will send a query to Wiktionary, and display the result on the "Definition" field, while simultaneously filling in the "word" field for you. You may also double click from words in the "Definition" field to get definition, because Wiktionary sometimes simply lists the base forms of inflected words.

![Demo](https://imgur.com/rUlVWwe.gif)

For a detailed list of features and language support data, please consult the [page](https://freelanguagetools.org/posts/ssmtool-full-tutorial/) on my blog

## Tutorials
[Video tutorial (Basic)](https://www.youtube.com/watch?v=y79_q08Zu8k&pp=sAQA)

[Detailed text tutorial](https://freelanguagetools.org/posts/ssmtool-full-tutorial/)
(The text originally on this document has since been moved there.)

**USERS**: If you want to install it, go to [Releases](https://github.com/FreeLanguageTools/ssmtool/releases/) and from the latest release, download the appropriate file for your operating system. 

## Linux distro packages
[![Packaging status](https://repology.org/badge/vertical-allrepos/ssmtool.svg)](https://repology.org/project/ssmtool/versions)

## API documentation
If you want to leverage ssmtool to build your own plugins, you can refer to the [API Documentation](API.md)

## Future plans
This program is still at an early stage. More features will be added soon.

Current plans include:
- Chinese word segmentation
- Auto-selecting the most difficult words
- Usage graphs

## Feedback
You are welcome to report bugs, suggest features/enhancements, or ask for clarifications by opening a GitHub issue.

## Credits
All the definitions provided by the program come from the English Wiktionary, without which this program would never have been created.

Google dictionary API comes from [here](https://dictionaryapi.dev/).

Support for Google Translate without the use of an API key comes from the [py-googletrans project](https://github.com/ssut/py-googletrans)

App icon is made from icons by Freepik available on Flaticon.
