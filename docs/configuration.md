---
title: Configuration
layout: default
nav_order: 5
---

# Configuration

VocabSieve is meant to have sane defaults, so that only minimal configuration is required to start using it, but a few things are still necessary. The configuration window will pop up when you first open it. 

Before opening VocabSieve for the first time, it is recommended to have Anki with AnkiConnect installed open so you can access all settings at first, though you can always change the settings later. 

You need to first select a target language from the list. Then, you can select a dictionary. We recommend using Google translation only if the other two are not available, because translations are always less detailed than dictionary definitions and may not provide the full range of meanings needed. You are recommended to leave lemmatization on as it is by default. It can greatly boost dictionary coverage for many languages.

Optionally, you can add frequency lists and local dictionary files via the bottom option of "Manage local dictionaries". Consult the [Resources]({{site.baseurl}}/resources.html) page for compatible files. You can always do this later.

Next, on the Anki tab, you will see a number of settings. You usually do not have to change the first one, which is the API endpoint, unless you configured a different endpoint in AnkiConnect, but in that case you will know how to do this. You should then select a deck to add your notes to. By default, VocabSieve will generate a new note type for you to be used with the tool to minimize required setup, so the fields should be populated by default. But if you would like to use your own, match the note type and data fields into note fields. To do this you must have a note type with at least three fields, one each for Sentence, Word, and Definition. 

You're done! Now you are ready to mine sentences.