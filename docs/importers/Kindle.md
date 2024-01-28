---
layout: default
title: Kindle
nav_order: 2
parent: Importers
---
# Kindle Importer
Amazon Kindle is a series of e-readers made by Amazon. They are supported in Vocabsieve with an importer that reads the vocabulary database to find words.

## Reading
Kindles record when you look up words in to the vocabulary database. However, this usually results in too many words being selected for import. To combat this, VocabSieve's importer provide an option to only import words which are specifically highlighted. The highlights are stored in "My Clippings.txt".

## Usage

{: .note}
VocabSieve will import your lookup history automatically to its database for statistics purposes. It is recommended that you make sure the device time on your ereader does not drift too much from the actual time.

1. Select the "Import > Kindle lookups" from the dropdown menus. 
2. Navigate to the root directory of your ereader. The directory should look like this:
```
.
├── audible
├── documents
│   ├── dictionaries
│   ├── Downloads
│   └── My Clippings.txt
├── fonts
└── system
    ├── [...]
    ├── vocabulary
    └── [...]
```
3. A window should show, which you can use to select which notes to add to Anki and preview cards by selecting the books you want to import and the date range.

## Troubleshooting
### Can't find my books
Ensure that the language of your book is set correctly. VocabSieve filters so that it only shows books in your target language. Most books should have proper metadata for the language, but some may not.
 
