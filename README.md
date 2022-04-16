# VocabSieve - a simple sentence mining tool
![https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true](https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true)
![https://img.shields.io/pypi/v/vocabsieve.svg](https://img.shields.io/pypi/v/vocabsieve.svg)
[![Downloads](https://pepy.tech/badge/ssmtool)](https://pepy.tech/project/ssmtool)

Join our chat on [Matrix](https://webchat.kde.org/#/room/#flt:midov.pl) or [Telegram](https://t.me/fltchat)

VocabSieve (formerly Simple Sentence Mining, `ssmtool`) is a program for sentence mining, in which sentences with target vocabulary words are collected and added into a spaced repetition system (SRS, e.g. Anki) for language learning.

![Demo](https://i.postimg.cc/vTc8dcZ0/out.gif)

## Features
- Double-click lookups from copied sentences and even faster lookups from integrated applications
- Lemmatization of words on lookup
- No internet is required at all if you use downloaded resources
- Online and local dictionaries in multiple formats (StarDict, Migaku, plain JSON)
- Frequency lists and pronunciations
- Web reader for ebooks and long articles (epub, fb2, plaintext), allowing one-click lookup
- Kindle highlights to Anki sentence cards (KOReader support is planned)

For a detailed list of features and language support data, please consult the [blog post](https://freelanguagetools.org/2021/07/simple-sentence-mining-ssmtool-full-tutorial/) on my blog

## Tutorials
[Text tutorial](https://freelanguagetools.org/2021/07/simple-sentence-mining-ssmtool-full-tutorial/)
(The text originally on this document has since been moved there.)

[New video tutorial](https://www.youtube.com/watch?v=EHW-kBLmuHU)

**Windows and Mac users**: If you want to install this program, go to [Releases](https://github.com/FreeLanguageTools/vocabsieve/releases/) and from the latest release, download the appropriate file for your operating system. 


## Linux distro packages
[![Packaging status](https://repology.org/badge/vertical-allrepos/vocabsieve.svg)](https://repology.org/project/vocabsieve/versions)

### Gentoo

First, you need to add the ::guru overlay. Skip this section if you already had done so.
```
# eselect repository enable guru
# emaint -r guru sync
```
Install the package:
`# emerge -av app-misc/vocabsieve`

### Arch

Use your favorite AUR helper (or manually) to install the pacakge `vocabsieve`

### Other distros

At this time, there are no packages for other distributions. If you are able to create packages for them, please tell me!

In the meantime, users should simply use `pip3` to install VocabSieve: `pip3 install --user vocabsieve`.

This should install an executable and a desktop icon and behave like any other GUI application you may have.

## Development
To run from source, simply use `pip3 -r requirements.txt` and then `python3 vocabsieve.py`.

Alternatively, you can also install a live version to your python package library with `pip3 install .` (Add --user if there is a permission error)

For debugging purposes, set the environmental variable `VOCABSIEVE_DEBUG` to any value. This will create a separate profile (settings and databases for records and dictionaries) so you may perform tests without affecting your normal profile. For each different value of `VOCABSIEVE_DEBUG`, a separate profile is generated. This can be any number or string.

Note that VocabSieve is unable to delete old profiles. You must do so yourself based on your operating system's locations.  

## API documentation
If you want to leverage VocabSieve to build your own plugins/apps, you can refer to the [API Documentation](API.md)

Note that VocabSieve is still alpha software. API is not guaranteed to be stable at this point.

## Feedback
You are welcome to report bugs, suggest features/enhancements, or ask for clarifications by opening a GitHub issue.

## Donations
Send me some Monero to support this work!

XMR Address: `89AZiqM7LD66XE9s5G7iBu4CU3i6qUu2ieCq4g3JKacn7e1xKuwe2tvWApLFvhaMR47kwNzjC4B5VL3N32MCokE2U9tGXzX`

Monero is a private, censorship-resistant cryptocurrency. Transactions are anonymous and essentially impossible to track by authorities or third-party analytics companies.

[Learn more about Monero](https://www.getmonero.org/)

If you do not have any Monero, a good way to get it is through [ChangeNow](https://changenow.io/) or [SimpleSwap](https://simpleswap.io/).


## Credits
The definitions provided by the program by default come from English Wiktionary, without which this program would never have been created.

App icon is made from icons by Freepik available on Flaticon.
