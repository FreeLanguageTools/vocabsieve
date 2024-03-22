---
layout: default
title: Auto Text
nav_order: 3
parent: Importers
---
# Auto Text Importer
The Auto Text Importer uses VocabSieve's databases to extract appropriate sentences from your text automatically. Currently, it is not very configurable, and will only add sentences with only one unknown word based on available data. 

Except for German and Luxembourgish, words starting with capital letters are considered proper names and automatically considered known to avoid them being added into Anki. 

This is currently experimental and may not work as well as the other importers, since it has to make a lot more guesses. Please report any bugs you observe. 

You may want to use this for two reasons:

## Usage 1: Teaching VocabSieve about your progress
Anki data is the primary source VocabSieve draws on when determining whether or not you know a word. By adding a lot of cards into Anki and marking the cards as known, you can tell VocabSieve about your progress and calibrate its database.

0. Configure your tracking data sources. See [Tracking]({{site.baseurl}}/configuration/tracking.html), and wait for the known data to be ready. You can check if the data is ready by opening the Statistics window.
1. Obtain articles, books, or transcripts of things you've read or watched or listened to. Be sure the file to be imported is either in an ebook format (.epub, .fb2, .mobi, etc) or are a text file (.txt)
2. Use Import > Auto import from text, and select your file.
3. Simple press "Lookup selected", and view the results. You can then decide whether to add the cards.

## Usage 2: Asynchronous sentence mining
If you don't have a lot of time to do active sentence mining, this may present an compelling alternative. However, for it to work well, VocabSieve needs to know quite well exactly which words you know. Therefore, it may require going through a lot of false positive (known target word) cards first anyways.