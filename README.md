# VocabSieve - Anki companion for language learning
![https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true](https://ci.appveyor.com/api/projects/status/32r7s2skrgm9ubva?svg=true)
![https://img.shields.io/pypi/v/vocabsieve.svg](https://img.shields.io/pypi/v/vocabsieve.svg)

## Manual

[New manual](https://docs.freelanguagetools.org/)

## Support

Note: All chat rooms are bridged/mirrored. You won't miss out on anything by choosing one over the other. We recommend you use Matrix if possible.

| Platform                | Address                         | Notes |
|  ---                    |    ----                         | ---   |
| Matrix (Recommended)    | [#general:freelanguagetools.org](https://matrix.to/#/#general:freelanguagetools.org)  |   Requires a Matrix account on any homeserver. A list of homeservers can be found [here](https://tatsumoto-ren.github.io/blog/list-of-matrix-servers.html)    |
| Telegram                | <https://t.me/fltchat>          |       |
| Discord (*proprietary*) | <https://discord.gg/DNSsTtHRxz>              |       |

VocabSieve is a companion program for language learning with Anki. Its primary function is sentence mining, in which sentences with vocabulary words are collected and added into Anki for long term retention. It aims to help intermediate learners gain vocabulary efficiently by allowing card creation with minimal friction. Possible use cases include sentence mining from videos, texts, asynchronously from ereader highlights, and even completely automatically from books or subtitles. See [workflow page](https://docs.freelanguagetools.org/workflows) for more details.

## Screenshots

![](https://github.com/FreeLanguageTools/vocabsieve/blob/04d0b169c66017f5bdce8d0d8dddb3329b6fb971/docs/assets/demo-0.12.gif)
[![out.gif](https://i.postimg.cc/5yj3VjPB/out.gif)](https://postimg.cc/kR38NMPG)
[![20230220-163240.png](https://i.postimg.cc/rwT8HvJ8/20230220-163240.png)](https://postimg.cc/TpkMLNFS)


## Features
- **Quick word lookups and card creation**: Getting definition, pronunciation, and frequency within one or two keypresses/clicks. Only one more click is needed to save the sentence, word, definition and pronunciation as an Anki card.
- **Wide language support**: Supports all languages listed on Google Translate, though it is currently optimized for European languages. Spanish, German, English, and Russian are routinely tested, but all other languages with a similar morphology should work well.
- **Lemmatization**: Automatically remove inflections to enhance dictionary experience (`books` -> `book`, `ran` -> `run`). This works well for most European languages.
- **Local-first**: No internet is required if you use downloaded resources. VocabSieve has no central server, so there are no fees to keep it running, so you will never have to pay a subscription.
- **Sane defaults**: Little configuration is needed other than settings for the Anki deck. It comes with two dictionary sources by default for most languages and one pronunciation source that should cover most needs. There is also an included note type, saving you the effort of finding an appropriate one and/or styling it if you don't want to.
- **Local resource support**: Dictionaries in StarDict, Migaku, plain JSON, MDX, Lingvo (.dsl), CSV; frequency lists; and audio libraries. Cognates data can also be imported for more accurate vocabulary tracking.
- **Web reader**: Read epubs with one-click word lookups and Anki export.
- **eReader integration**: Batch-convert [KOReader](https://github.com/koreader/koreader) and Kindle highlights to Anki sentence cards to build vocabulary efficiently without interrupting your reading.
- **Vocabulary tracking**: Track your learning progress effortlessly when you look up (including from ereader), review your Anki cards, or immerse. The data never leaves your computer, and can easily be exported for your own use.
- **Book analysis**: Not sure what to read? Once VocabSieve gets enough data of what words you know, it can quickly scan books and predict your level of understanding to help you choose books. 

## Tutorials
[Manual](https://docs.freelanguagetools.org/)
(The text originally on the wiki or this document or the blog post has since been moved there, with some updates.)

[New video tutorial](https://www.youtube.com/watch?v=EHW-kBLmuHU)

**Windows and Mac users**: If you want to install this program, go to [Releases](https://github.com/FreeLanguageTools/vocabsieve/releases/) and from the latest release, download the appropriate file for your operating system. 

For a nightly build, please check the [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master). These are not considered ready for release and likely contain bugs. It is recommended to use the debug version to get more details when things go wrong.


## Linux distro packages
[![Packaging status](https://repology.org/badge/vertical-allrepos/vocabsieve.svg)](https://repology.org/project/vocabsieve/versions)
  
## Development
To run from source:
1. Set up a virtual environment `python3 -m venv env`
2. `pip install -r requirements.txt`
3. `python3 vocabsieve.py`

For debugging purposes, set the environmental variable `VOCABSIEVE_DEBUG` to any value. This will create a separate profile (settings and databases for records and dictionaries) so you may perform tests without affecting your normal profile. For each different value of `VOCABSIEVE_DEBUG`, a separate profile is generated. This can be any number or string.

Pull requests are welcome! If you want to implement a significant feature, be sure to first ask by creating an issue so that no effort is wasted on doing the same work twice.

## Status
This is currently beta software. You should not expect it to be completely bug-free, but you may expect that:
- You should not lose data by upgrading to a new release. However, downgrading is not guaranteed to work! When in doubt, back up your data and ask in the chatroom before attempting to downgrade.
    - This does not include your settings, which may need to be reset for a new release. This will be indicated on the release notes.
- Using the `master` branch and only upgrading should *usually* not break things, but this is not guaranteed. You are expected to read commit messages to take proper precaution.
    - Using feature branches may break things!

## Feedback
You are welcome to report bugs, suggest features/enhancements, or ask for clarifications by opening a GitHub issue.

## Donations
If you appreciate this tool, consider making a donation to the [Free Software Foundation](https://www.fsf.org/) or the [Electronic Frontier Foundation](https://www.eff.org/) to protect our digital future and defend our freedom. Do your part to refuse to pay for DRM'd content and devices. 

## Credits
The definitions provided by the program by default come from English Wiktionary, without which this program would never have been created. [LingvaTranslate](https://github.com/thedaviddelta/lingva-translate) is used to obtain Google Translate results. Fоrvо scraping code is inspired by this [repository](https://github.com/Rascalov/Anki-Simple-Forvo-Audio). Lemmatization capabilities come from [simplemma](https://github.com/adbar/simplemma) and [pymorphy3](https://github.com/kmike/pymorphy3).

App icon is made from icons by Freepik available on Flaticon.
