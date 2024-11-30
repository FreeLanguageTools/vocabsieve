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

<details markdown=1>
<summary> Click to open instructions for advanced users </summary>
If you prefer to install it anyways, you can use `pip3 install vocabsieve`  (add `-–user` if appropriate). (**Note**: Newer versions of Python will stop you from installing into your global Python environment by default. You may need to create a virtual environment). This will install a desktop file which you should be able to see from your launcher menu. If you do not use a desktop environment, you can launch it through the command line `vocabsieve`.

If you want to test the latest features, you can go to [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master) page to obtain the latest builds, but they are not guaranteed to run. If you notice anything wrong from those builds, open an issue on GitHub. Ensure you are using the latest nightly build before reporting anything.

</details>

### Windows

Go to the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases) for standalone versions. You may have to dismiss some warnings from the browser or Windows to install it, as it is unsigned.

<details markdown=1>
<summary> Click to open instructions to download test releases </summary>

If you want to test the latest features, you can go to [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master) page to obtain the latest builds, but they are not guaranteed to run. If you notice anything wrong from those builds, open an issue on GitHub. Note: ensure you are using the latest nightly build before reporting anything.

</details>

{: .note}
Only 64 bit Windows 10+ is supported

### MacOS

Go to the [Github releases page](https://github.com/FreeLanguageTools/vocabsieve/releases) for standalone versions. You may have to dismiss some warnings from the browser or Windows to install it, as it is unsigned.

{: .important }
The build is unsigned because I do not want to pay Apple US$100 a year just to distribute a free program. This will result in a warning that "The app is damaged and can't be opened.", which is not true. Do the following to open it.

Open a new terminal window and type the following command
`xattr -d com.apple.quarantine /path/to/app.app` (replacing "/path/to/app.app" with path to VocabSieve app). This unquarantines the app and allows it to run on your Mac without being certified by Apple.

<details markdown=1>
<summary> Click to open instructions to download test releases </summary>

If you want to test the latest features, you can go to [CI artifacts page](https://nightly.link/FreeLanguageTools/vocabsieve/workflows/build-binaries/master) page to obtain the latest builds, but they are not guaranteed to run. If you notice anything wrong from those builds, open an issue on GitHub. Note: ensure you are using the latest nightly build before reporting anything.

</details>

### Running from source (Advanced)

To run from source:

1. Set up a virtual environment `python3 -m venv env`
2. `pip install -r requirements.txt`
3. `python3 vocabsieve.py`

For debugging purposes, set the environmental variable `VOCABSIEVE_DEBUG` to any value. This will create a separate profile (settings and databases for records and dictionaries) so you may perform tests without affecting your normal profile. For each different value of `VOCABSIEVE_DEBUG`, a separate profile is generated. This can be any number or string.

## AnkiConnect (Required for card creation)

Download and install [Anki desktop](https://apps.ankiweb.net/) (Not mobile or Anki Universal). Skip if you already installed it.

Then, install the [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon. You do not have to change any settings for it.

{: .important }
**MacOS users**: You must have Anki open on the foreground (i.e. visible on your desktop), or otherwise [disable the App Nap feature](https://github.com/FooSoft/anki-connect#notes-for-macos-users). If you do not do this, AnkiConnect will not respond and will cause this program to be very slow and/or unresponsive.

## Vocabsieve bookmarklet

This bookmarklet allows you to copy the sentence as well as the word under cursor with one click to the word, without selecting anything (only works for languages that use space to separate words).

### Usage

Select the following code and drag it to the bookmark toolbar. Alternatively, copy the code, create a bookmark, and paste the code into the URL field in the popup window.

```js
javascript:(function()%7Bjavascript%3A(function%20()%20%7B%0A%20%20%2F%2F%20Copy%20text%20to%20clipboard%20using%20modern%20Clipboard%20API%0A%20%20function%20copyTextToClipboard(text)%20%7B%0A%20%20%20%20navigator.clipboard.writeText(text).then(function%20()%20%7B%0A%20%20%20%20%20%20console.log('Copying%20to%20clipboard%20was%20successful!')%3B%0A%20%20%20%20%7D).catch(function%20(err)%20%7B%0A%20%20%20%20%20%20console.error('Could%20not%20copy%20text%3A%20'%2C%20err)%3B%0A%20%20%20%20%7D)%3B%0A%20%20%7D%0A%0A%20%20%2F%2F%20Add%20a%20style%20element%20for%20hover%20effects%0A%20%20const%20style%20%3D%20document.createElement('style')%3B%0A%20%20style.textContent%20%3D%20%60%0A%20%20%20%20span.sentence%3Ahover%20%7B%0A%20%20%20%20%20%20text-decoration%3A%20underline%20%236b7%20solid%203px%3B%0A%20%20%20%20%20%20text-decoration-skip-ink%3A%20none%3B%0A%20%20%20%20%7D%0A%20%20%60%3B%0A%20%20document.head.appendChild(style)%3B%0A%0A%20%20%2F%2F%20Process%20all%20paragraphs%0A%20%20document.querySelectorAll(%22p%22).forEach(function%20(paragraph)%20%7B%0A%20%20%20%20paragraph.innerHTML%20%3D%20paragraph.textContent%0A%20%20%20%20%20%20.split(%2F(%3F%3C%3D%5B%5C.%5C%3F!%5D%20)%2F)%0A%20%20%20%20%20%20.map(v%20%3D%3E%20%60%3Cspan%20class%3D%22sentence%22%3E%24%7Bv.trimEnd()%7D%3C%2Fspan%3E%60)%0A%20%20%20%20%20%20.join(%22%20%22)%3B%0A%20%20%7D)%3B%0A%0A%20%20%2F%2F%20Process%20divs%20without%20nested%20divs%0A%20%20document.querySelectorAll(%22div%22).forEach(function%20(div)%20%7B%0A%20%20%20%20if%20(!div.querySelector(%22div%22))%20%7B%0A%20%20%20%20%20%20div.innerHTML%20%3D%20div.textContent%0A%20%20%20%20%20%20%20%20.split(%2F(%3F%3C%3D%5B%5C.%5C%3F!%5D%20)%2F)%0A%20%20%20%20%20%20%20%20.map(v%20%3D%3E%20%60%3Cspan%20class%3D%22sentence%22%3E%24%7Bv.trimEnd()%7D%3C%2Fspan%3E%60)%0A%20%20%20%20%20%20%20%20.join(%22%20%22)%3B%0A%20%20%20%20%7D%0A%20%20%7D)%3B%0A%0A%20%20%2F%2F%20Add%20click%20event%20to%20span%20elements%0A%20%20document.body.addEventListener(%22click%22%2C%20function%20(event)%20%7B%0A%20%20%20%20if%20(event.target.classList.contains(%22sentence%22))%20%7B%0A%20%20%20%20%20%20let%20selection%20%3D%20window.getSelection()%3B%0A%20%20%20%20%20%20selection.modify('extend'%2C%20'backward'%2C%20'word')%3B%0A%20%20%20%20%20%20let%20a%20%3D%20selection.toString()%3B%0A%0A%20%20%20%20%20%20selection.modify('extend'%2C%20'forward'%2C%20'word')%3B%0A%20%20%20%20%20%20while%20(selection.toString().slice(-1)%20%3D%3D%3D%20%22-%22)%20%7B%0A%20%20%20%20%20%20%20%20selection.modify('extend'%2C%20'forward'%2C%20'word')%3B%0A%20%20%20%20%20%20%7D%0A%20%20%20%20%20%20let%20b%20%3D%20selection.toString()%3B%0A%0A%20%20%20%20%20%20selection.modify('move'%2C%20'forward'%2C%20'character')%3B%0A%20%20%20%20%20%20let%20word%20%3D%20(a%20%2B%20b).replace(%2F%5B.%2C%5C%2F%23!%24%25%5C%5E%26%5C*%3B%3A%7B%7D%3D%5C_%E2%80%A6%60~()%5D%2Fg%2C%20%22%22).trim()%3B%0A%0A%20%20%20%20%20%20console.log(word)%3B%0A%20%20%20%20%20%20console.log(event)%3B%0A%0A%20%20%20%20%20%20let%20copyObj%20%3D%20%7B%0A%20%20%20%20%20%20%20%20%22sentence%22%3A%20event.target.textContent.trim()%2C%0A%20%20%20%20%20%20%20%20%22word%22%3A%20word%0A%20%20%20%20%20%20%7D%3B%0A%20%20%20%20%20%20console.log(copyObj)%3B%0A%20%20%20%20%20%20copyTextToClipboard(JSON.stringify(copyObj))%3B%0A%20%20%20%20%7D%0A%20%20%7D)%3B%0A%7D)()%3B%7D)()%3B
```

### Source

The source script (a slightly modified version of the web extension script)

```js
javascript: (function () {
  // Copy text to clipboard using modern Clipboard API
  function copyTextToClipboard(text) {
    navigator.clipboard
      .writeText(text)
      .then(function () {
        console.log("Copying to clipboard was successful!");
      })
      .catch(function (err) {
        console.error("Could not copy text: ", err);
      });
  }

  // Add a style element for hover effects
  const style = document.createElement("style");
  style.textContent = `
    span.sentence:hover {
      text-decoration: underline #6b7 solid 3px;
      text-decoration-skip-ink: none;
    }
  `;
  document.head.appendChild(style);

  // Process all paragraphs
  document.querySelectorAll("p").forEach(function (paragraph) {
    paragraph.innerHTML = paragraph.textContent
      .split(/(?<=[\.\?!] )/)
      .map((v) => `<span class="sentence">${v.trimEnd()}</span>`)
      .join(" ");
  });

  // Process divs without nested divs
  document.querySelectorAll("div").forEach(function (div) {
    if (!div.querySelector("div")) {
      div.innerHTML = div.textContent
        .split(/(?<=[\.\?!] )/)
        .map((v) => `<span class="sentence">${v.trimEnd()}</span>`)
        .join(" ");
    }
  });

  // Add click event to span elements
  document.body.addEventListener("click", function (event) {
    if (event.target.classList.contains("sentence")) {
      let selection = window.getSelection();
      selection.modify("extend", "backward", "word");
      let a = selection.toString();

      selection.modify("extend", "forward", "word");
      while (selection.toString().slice(-1) === "-") {
        selection.modify("extend", "forward", "word");
      }
      let b = selection.toString();

      selection.modify("move", "forward", "character");
      let word = (a + b).replace(/[.,\/#!$%\^&\*;:{}=\_…`~()]/g, "").trim();

      console.log(word);
      console.log(event);

      let copyObj = {
        sentence: event.target.textContent.trim(),
        word: word,
      };
      console.log(copyObj);
      copyTextToClipboard(JSON.stringify(copyObj));
    }
  });
})();
```
