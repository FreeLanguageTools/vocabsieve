---
title: Installation
layout: default
nav_order: 4
---

# Installation

{: .highlight }
There are three components you need to install to start using VocabSieve. Only the main desktop application is required. AnkiConnect is needed for VocabSieve to be able to add cards. Install the browser extension only if you want to use it.

## Main Desktop Application

### GNU/Linux

Gentoo: `app-misc/vocabsieve` in ::guru

Arch Linux AUR: `vocabsieve`

If you use other distributions, you should run it from an AppImage distributed on the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases).

#### Advanced users
If you prefer to install it anyways, you can use `pip3 install vocabsieve`  (add `-–user` if appropriate). (**Note**: Newer versions of Python will stop you from installing into your global Python environment by default. You may need to create a virtual environment). This will install a desktop file which you should be able to see from your launcher menu. If you do not use a desktop environment, you can launch it through the command line `vocabsieve`.

If you want to test the latest features, you can go to [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master) page to obtain the latest builds, but they are not guaranteed to run. If you notice anything wrong from those builds, open an issue on GitHub. Note: ensure you are using the latest nightly build before reporting anything.


### Windows

Go to the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases) for standalone versions. You may have to dismiss some warnings from the browser or Windows to install it, as it is unsigned.

{: .note}
Only 64 bit Windows 7+ is supported. (**Note**: There has been reports of it not working on Windows 8 due to a dependency on Windows 10's API. In any case, Windows 10 is routinely tested to work)

### MacOS

{: .warning }
MacOS support is often broken due to the me not being able to test it. If you discovered an issue and can help test or fix it, please reach out by opening a Github issue or using the chatroom.

Go to the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases) for standalone versions. You may have to dismiss some warnings from the browser or Windows to install it, as it is unsigned.

{: .important }
The build is unsigned because I do not want to pay Apple US$100 a year just to distribute a free program. This will result in a warning that "The app is damaged and can't be opened.", which is not true. Do the following to open it.

Open a new terminal window and type the following command
`xattr -d com.apple.quarantine /path/to/app.app` (replacing "/path/to/app.app" with path to VocabSieve app). This unquarantines the app and allows it to run on your Mac without being certified by Apple.

### Advanced users

If you want to test the latest features, you can go to [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master) page to obtain the latest builds, but they are not guaranteed to run. If you notice anything wrong from those builds, open an issue on GitHub. Note: ensure you are using the latest nightly build before reporting anything.

## AnkiConnect (Required for card creation)

Download and install [Anki desktop](https://apps.ankiweb.net/) (Not mobile or Anki Universal). Skip if you already installed it.

Then, install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon. You do not have to change any settings for it.

{: .important }
**MacOS users**: You must have Anki open on the foreground (i.e. visible on your desktop), or otherwise [disable the App Nap feature](https://github.com/FooSoft/anki-connect#notes-for-macos-users). If you do not do this, AnkiConnect will not respond and will cause this program to be very slow and/or unresponsive.

## Browser extension (Optional)

{: .note}
The browser extension should work as is, but is mostly unmaintained

Install the extension for your browser: 

 - [Firefox](https://addons.mozilla.org/en-GB/firefox/addon/click-copy-sentence/)

 - [Chrome/Chromium](https://chrome.google.com/webstore/detail/click-copy-sentence/klhlkoabjmofmjkhbmelmfnhkbjaohdj) (incl. derivatives such as Edge, Brave, etc.)

Note that if you have local ebook files to read, you can use the built-in reader too, accessible by the "Reader" button on the menu bar. When using the reader, you do not need the browser extension.