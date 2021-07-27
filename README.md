# Simple Sentence Mining
Simple Sentence Mining (`ssmtool`) is a program for sentence mining, in which sentences with target vocabulary words are collected and added into a spaced repetition system (SRS) for language learning.

This program monitors your clipboard at all times and when a change is detected, the contents gets copied onto the "Sentence" field. From there, you can double click any word, and the program will send a query to Wiktionary, and display the result on the "Definition" field, while simultaneously filling in the "word" field for you. You may also double click from words in the "Definition" field to get definition, because Wiktionary sometimes simply lists the base forms of inflected words.

![Demo](https://imgur.com/aF34qax.gif)

## Prerequisites

| Name | Note |
------ | ------
|Anki with AnkiConnect | Needed for exporting notes|


## Installation
### Linux
Install with pip: `pip install ssmtool`

Packages on Gentoo GURU and Arch Linux AUR will be soon available.

### Windows, macOS
Standalone version available in the [Releases](https://github.com/FreeLanguageTools/ssmtool/releases) tab.

Alternatively, you can also install with pip: `pip install ssmtool`

([Instructions on setting up PIP on Windows](https://nitratine.net/blog/post/how-to-setup-pythons-pip/))

([Instructions on setting up PIP on macOS](https://www.geeksforgeeks.org/how-to-install-pip-in-macos/))

**Important**: On macOS it is important to have Anki open on the foreground, otherwise the API will respond very slowly, causing lags in the application.

## How to use
First, you need to configure it by pressing the "Configure.." button at the bottom. You only need to do it once.

### With Click-Copy-Sentence
1. Open any website
2. Click on a word
3. Check if the definition makes sense, if not, double-click on one of the words in the Sentence field.
4. Click on the "Add note" button.

### General use
1. Copy any text to clipboard
2. Click on a word in the Sentence field
3. Check if the definition makes sense. You can also look up any word in the Definition field.
4. Click on the "Add note" button.


## Recommended tools
*Disclaimer: Except for the companion web extension, these projects are not affiliated with the author of `ssmtool`*
| Service/Application | Plugin | Note |
--------- | ------ | ------
| Netflix | Subadub ([Firefox](https://addons.mozilla.org/en-US/firefox/addon/subadub/), [Chrome](https://chrome.google.com/webstore/detail/subadub/jamiekdimmhnnemaaimmdahnahfmfdfk)) | Chrome extension to make subtitles selectable (also copy-able) |
| Youtube  | [youtube-dl](https://github.com/ytdl-org/youtube-dl) | Download videos from youtube (videos can be played locally with subtitles, which are then copy-able with mpv). |
| mpv | [mpvacious](https://github.com/Ajatt-Tools/mpvacious) | Automatically copies subtitles to clipboard (which will show up on this tool) |
| Anki | [AwesomeTTS](https://ankiweb.net/shared/info/814349176) | Automatically generates TTS for cards generated from this tool. You can configure it to produce TTS on demand for the note type used by `ssmtool`, complementing your flashcards.
| Browser | Click Copy Sentence ([Firefox](https://addons.mozilla.org/en-GB/firefox/addon/click-copy-sentence/), Chrome version coming soon.) | Companion browser extension for ssmtool. Enables single-click note creation. | 



## Future plans
This program is still at an early stage. More features will be added soon.

Current plans include:
- Auto-selecting the most difficult words

## Credits
All the definitions provided by the program come from the English Wiktionary, without which this program would never have been created.

App icon is made from icons by Freepik available on Flaticon.