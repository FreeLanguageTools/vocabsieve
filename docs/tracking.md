---
layout: default
title: Vocabulary tracking
nav_order: 6
---
# Vocabulary tracking

VocabSieve has a built-in feature to track your vocabulary. This is done by logging *events* on words, each of which carries a certain amount of points. When a certain amount of points are reached, the word is classified as *known*. 

By default, 100 points is needed for a non-cognate word to be classified as known (25 points for cognate word) the points on each type of event (*weights*) are the following:

| Event | Default score | Note |
| ----- | ----- | ---- |
| Seen  | 8 | [Paper](https://core.ac.uk/download/pdf/323110125.pdf) assumes 12 exposures is needed to acquire a word |
| Lookup | 15 | Max one lookup event per day | 
| Mature Anki card target word | 80 | |
| Mature Anki card context | 30 | |
| Young Anki card target word | 40 | VocabSieve distinguishes between two types of Anki cards, which by default correspond to "mature" and "young" carrds in Anki, but this can be changed to arbitariy criteria by changing the query string |
| Young Anki card context | 20 | |

Using Anki data requires matching fields in each of your Anki note types. You should mark the field as "\<Ignored\>" if you do not wish to use the field or the note type as a whole.

Once you have set up vocabulary tracking, you can view a list of words VocabSieve thinks you know by going to Statistics -> Known words tab. After ensuring that you know almost all of the words listed in the text box, you can now use the features relying on vocab tracking, such as the book analyzer and auto imports from texts.

## Importing content
To tell VocabSieve what you've read/watched/listened to, you need to import the files into the database by using Track -> Content Manager. You can import ebooks, text files, and subtitles this way.

## Manual marking

If you have a lemmatized frequency list, you can also manually mark words off the list using Track -> Mark words from frequency list.

![](https://i.postimg.cc/pdd8nLjt/20240321-212612.png)

Clicking on a word toggles its known status.

Green background: Known

Red border: Manually marked as unknown

Bolded score: Modifier is set (manually marked as known or unknown)