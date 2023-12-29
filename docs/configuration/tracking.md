---
layout: default
title: Vocabulary tracking
nav_order: 1
parent: Configuration
---
# Vocabulary tracking

VocabSieve has a built-in feature to track your vocabulary. This is done by logging *events* on words, each of which carries a certain amount of points. When a certain amount of points are reached, the word is classified as *known*. 

By default, 100 points is needed for a non-cognate word to be classified as known (25 points for cognate word) the points on each type of event (*weights*) are the following:

| Event | Default score | Note |
| ----- | ----- | ---- |
| Seen  | 8 [1]| [Paper](https://core.ac.uk/download/pdf/323110125.pdf) assumes 12 exposures is needed to acquire a word |
| Lookup | 15 | Max one lookup event per day | 
| Mature Anki card target word | 80 | |
| Mature Anki card context | 30 | |
| Young Anki card target word | 40 | VocabSieve distinguishes between two types of Anki cards, which by default correspond to "mature" and "young" carrds in Anki, but this can be changed to arbitariy criteria by changing the query string |
| Young Anki card context | 20 | |

Using Anki data requires matching fields in each of your Anki note types. You should mark the field as "\<Ignored\>" if you do not wish to use the field or the note type as a whole.

Once you have set up vocabulary tracking, you can view a list of words VocabSieve thinks you know by going to Statistics -> Known words tab. After ensuring that you know almost all of the words listed in the text box, you can now use the features relying on vocab tracking, such as the book analyzer and auto imports from texts.