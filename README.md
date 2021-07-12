# Simple Sentence Mining
Simple Sentence Mining (`ssmtool`) is a program for sentence mining, in which sentences with target vocabulary words are collected and added into a spaced repetition system (SRS) for language learning.

This program monitors your clipboard at all times and when a change is detected, the contents gets copied onto the "Sentence" field. From there, you can double click any word, and the program will send a query to Wiktionary, and display the result on the "Definition" field, while simultaneously filling in the "word" field for you. You may also double click from words in the "Definition" field to get definition, because Wiktionary sometimes simply lists the base forms of inflected words.

![Demo](demo.gif)

## Prerequisites

| Name | Note |
------ | ------
|Anki with AnkiConnect | Needed for exporting notes|
|PyQt5 | Needed when using pip. Will install automatically.|

It has not been thoroughly tested on all platforms, but it should work on Linux, MacOS, and Microsoft Windows, or any platforms supporting Python and PyQt.

## Installation
### Linux
Install with pip: `pip install ssmtool`
### Windows, macOS
Standalone version available in the [Releases](https://github.com/FreeLanguageTools/ssmtool/releases) tab.

Alternatively, you can also install with pip: `pip install ssmtool`

([Instructions on setting up PIP on Windows](https://nitratine.net/blog/post/how-to-setup-pythons-pip/))

([Instructions on setting up PIP on macOS](https://www.geeksforgeeks.org/how-to-install-pip-in-macos/))

**Important**: On macOS it is important to have Anki open on the foreground, otherwise the API will respond very slowly, causing lags in the application.

## How to use
0. Configure it by pressing the "Configure.." button at the bottom. (only once)
1. Open any website, ebook, or text document.
2. Select a sentence (or any segment of text)
3. Copy it to clipboard (Ctrl + C)
4. Double click on a word in the "Sentence" field to look it up.
5. If needed, double click on a word in the "Definition" field to look it up.
6. Click on the "Add note" button.
## Recommended tools
*Disclaimer: These projects are not affiliated with `ssmtool`*
| Service | Plugin | Note |
--------- | ------ | ------
| Netflix | Subadub ([Firefox](https://addons.mozilla.org/en-US/firefox/addon/subadub/), [Chrome](https://chrome.google.com/webstore/detail/subadub/jamiekdimmhnnemaaimmdahnahfmfdfk)) | Chrome extension to make subtitles selectable (also copy-able) |
| Youtube  | [youtube-dl](https://github.com/ytdl-org/youtube-dl) | Download videos from youtube (videos can be played locally with subtitles, which are then copy-able with mpv). |
| mpv | [mpvacious](https://github.com/Ajatt-Tools/mpvacious) | Automatically copies subtitles to clipboard (which will show up on this tool) |
| Anki | [AwesomeTTS](https://ankiweb.net/shared/info/814349176) | Automatically generates TTS for cards generated from this tool. You can configure it to produce TTS on demand for the note type used by `ssmtool`, complementing your flashcards.



## Future plans
This program is still at an early stage. More features will be added soon.

Current plans include:
- Tags
- Audio
- Other dictionaries
- Lemmatization step and auto-selecting the most difficult words

## Credits
App icon is made from icons by Freepik available on Flaticon.