---
title: VocabSieve Setup
layout: default
nav_order: 4
---

# VocabSieve Setup 

## Installation

There are three components you need to install to start using VocabSieve.

### Main Desktop Application

#### GNU/Linux

Gentoo: `app-misc/vocabsieve::guru`

Arch Linux AUR: `vocabsieve`

If you use other distributions, you should run it from an AppImage distributed on the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases).

##### Advanced users
If you prefer to install it anyways, you can use `pip3 install vocabsieve`  (add `-–user` if appropriate). (**Note**: Newer versions of Python will stop you from installing into your global Python environment by default. You may need to create a virtual environment). This will install a desktop file which you should be able to see from your launcher menu. If you do not use a desktop environment, you can launch it through the command line `vocabsieve`.

If you want to test the latest features, you can go to [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master) page to obtain the latest builds, but they are not guaranteed to run. If you notice anything wrong from those builds, open an issue on GitHub. Note: ensure you are using the latest nightly build before reporting anything.


#### Windows

Go to the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases) for standalone versions. You may have to dismiss some warnings from the browser or Windows to install it, as it is unsigned.

Only 64 bit Windows 7+ is supported. (**Note**: There has been reports of it not working on Windows 8 due to a dependency on Windows 10's API. In any case, Windows 10 is routinely tested to work)

#### MacOS

(MacOS support is often broken due to the me not being able to test it. If you discovered an issue and can help test or fix it, please reach out by opening a Github issue or using the chatroom)

Go to the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases) for standalone versions. You may have to dismiss some warnings from the browser or Windows to install it, as it is unsigned.

**Attention MacOS users**: The build is unsigned because I do not want to pay Apple US$100 a year just to distribute a free program. This will result in a warning that "The app is damaged and can't be opened.", which is not true. Do the following to open it:

Open a new terminal window and type the following command
`xattr -d com.apple.quarantine /path/to/app.app` (replacing "/path/to/app.app" with path to VocabSieve app). 

#### Advanced users

If you want to test the latest features, you can go to [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master) page to obtain the latest builds, but they are not guaranteed to run. If you notice anything wrong from those builds, open an issue on GitHub. Note: ensure you are using the latest nightly build before reporting anything.

### AnkiConnect (Required for card creation)

Download and install [Anki desktop](https://apps.ankiweb.net/) (Not mobile or Anki Universal). Skip if you already installed it.

Then, install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon. You do not have to change any settings for it.

**Mac users**: You must have Anki open on the foreground (i.e. visible on your desktop), or otherwise [disable the App Nap feature](https://github.com/FooSoft/anki-connect#notes-for-macos-users). If you do not do this, AnkiConnect will not respond and will cause this program to be very slow and/or unresponsive.

### Browser (Optional)

(Note: The browser extension should work as is, but is mostly unmaintained)

Install the extension for your browser: 

[Firefox](https://addons.mozilla.org/en-GB/firefox/addon/click-copy-sentence/)

[Chromium](https://chrome.google.com/webstore/detail/click-copy-sentence/klhlkoabjmofmjkhbmelmfnhkbjaohdj) (incl. derivatives such as Edge, Brave, etc.)

Note that if you have local ebook files to read, you can use the built-in reader too, accessible by the "Reader" button on the menu bar. When using the reader, you do not need the browser extension.


## Configuration

VocabSieve is meant to have sane defaults, so that only minimal configuration is required to start using it, but a few things are still necessary. The configuration window will pop up when you first open it. 

Before opening VocabSieve for the first time, it is recommended to have Anki with AnkiConnect installed open so you can access all settings at first, though you can always change the settings later. 

You need to first select a target language from the list. Then, you can select a dictionary. We recommend using Google translation only if the other two are not available, because translations are always less detailed than dictionary definitions and may not provide the full range of meanings needed. You are recommended to leave lemmatization on as it is by default. It can greatly boost dictionary coverage for many languages.

Optionally, you can add frequency lists and local dictionary files via the bottom option of "Manage local dictionaries". Consult the [Resources]({{site.baseurl}}/resources.html) page for compatible files. You can always do this later.

Next, on the Anki tab, you will see a number of settings. You usually do not have to change the first one, which is the API endpoint, unless you configured a different endpoint in AnkiConnect, but in that case you will know how to do this. You should then select a deck to add your notes to. By default, VocabSieve will generate a new note type for you to be used with the tool to minimize required setup, so the fields should be populated by default. But if you would like to use your own, match the note type and data fields into note fields. To do this you must have a note type with at least three fields, one each for Sentence, Word, and Definition. 

You're done! Now you are ready to mine sentences.

## Usage

For sample workflows, check the [Workflows]({{site.baseurl}}/workflows.html) page.

