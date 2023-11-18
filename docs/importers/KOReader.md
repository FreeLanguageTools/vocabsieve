---
layout: default
title: KOReader
nav_order: 1
parent: Importers
---
# KOReader Importer
[KOReader](https://koreader.rocks/) is a free and open source ebook reading program that can be installed on many devices. If you can use KOReader on your Kindle device, it is recommended that you do so, as KOReader is the most powerful reading program and receives the best support.

## Setup
1. Install KOReader on your device
2. Import the dictionaries you want to use. 
    > {: .highlight}
    KOReader only supports StarDict and does not support lemmatization, only fuzzy searches. However, it is not required for you to find a definition on KOReader in order to create a card.
3. Turn on the "Vocabulary builder" feature in KOReader.
    > {: .highlight}
    This is on by default in recent versions of KOReader

## Reading
By default, KOReader's Vocabulary Builder do not add words you looked up automatically. You are recommended to leave this as is. 

When reading, you can look up unknown words. There should be a button that says "Add to Vocab Builder". If you would like to create an Anki note for the sentence, press the button. 

## Usage

{: .note}
VocabSieve will import your lookup history automatically to its database for statistics purposes. It is recommended that you make sure the device time on your ereader does not drift too much from the actual time.

1. Select the "Import KOReader" from the dropdown menus. 
2. Navigate to the root directory of your ereader, such that it contains both all the books you want to import and KOReader's settings folder. 
3. A window should show, which you can use to select which notes to add to Anki and preview cards by selecting the books you want to import and the date range.

## Troubleshooting
### Can't find my books
Ensure that the language of your book is set correctly. VocabSieve filters so that it only shows books in your target language. Most books should have proper metadata for the language, but some may not.
 
You can set the book language by navigating to the .sdr folder located next to your book file, and open `metadata.xxx.lua` with a text editor, and find the following section:

```lua
["doc_props"] = {
        ["authors"] = "...",
        ["description"] = "...",
        ["language"] = "en", # Edit this
        ["title"] = "...",
    },
```

Change the string within the double quotes to the two-letter language code corrseponding to the actual language of the book. For example, `en` for English, `es` for Spansh, `it` for Italian, `el` for Greek, `de` for German.