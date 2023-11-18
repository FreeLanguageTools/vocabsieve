---
title: Workflows
layout: default
nav_order: 3
---
# Workflow gallery

{: .highlight}
Before setting up and starting to use VocabSieve, it is helpful to consider what your immersion workflow will be with VocabSieve.

VocabSieve supports a variety of different workflows. They can be broadly classified into two categories:
- Synchronous workflows, in which use VocabSieve *during* your immersion, such as reading or watching a video, 
- Asynchronous workflows, in which you use VocabSieve at some point *after* your immersion session is finished, such as importing highlights from an ereader.

## Synchronous workflows (Text)
### General
When you see any sentence from anywhere, you can simply copy it to the clipboard. It will appear on the Sentence field right away. Then, double click on any word. A definition should appear if found. You can look up words from the Definition field too. Then, when you are satisfied with the data, click on Add Note button to send it to Anki. You can add tags just like in Anki.

{: .note}
On MacOS and Linux with Wayland, clipboard change may not be detected due to OS restrictions. A workaround is implemented to use the focus event to retrieve clipboard content, but this may not work every time. Use the "Read clipboard" button if necessary.

### Browser
When you turn on the extension, you will notice that sentences are underlined in green. Whenever you click on any word, VocabSieve will receive both the whole sentence and the word under your cursor. The word will be looked up immediately too. Chances are, with lemmatization on, this is exactly the word you want. In that case, just press Ctrl/Cmd + S to save the card, and you can keep reading!

### Built-in reader
If you have an epub to read and would like to use VocabSieve in interactive mode while reading on your computer, you can use the built in reader, which can be accessed by the "Reader" button on the top bar.

![](https://camo.githubusercontent.com/ea02ac411022c3f99b812cfb4c24ed9ba70ebea0c620fd68b56cb7df4e337768/68747470733a2f2f692e706f7374696d672e63632f766d3766727637702f6f75742e676966)

## Synchronous workflows (Videos)

### mpv
You can use this tool in combination with [mpv](https://mpv.io) with the [mpvacious plugin](https://github.com/Ajatt-Tools/mpvacious) to make it copy subtitles to clipboard continuously. Then, you can use the Ctrl-m hotkey to add the media (screenshot and audio) afterwards. For details, check the documentation for mpvacious.

### asbplayer
You can use VocabSieve as a dictionary tool with [asbplayer](https://github.com/killergerbah/asbplayer). For details, check the documentation for mpvacious. You can refer to this [Youtube video](https://www.youtube.com/watch?v=jXO4gmCmcNE) from Refold to set up VocabSieve with asbplayer.

## Asynchronous workflows (Ereaders)

### KOReader and Kindle
If you have an ereader or phone with KOReader installed, you can use the [KOReader Importer]({{site.baseurl}}/importers/KOReader)

Alternatively, if you use a Kindle, you can use the [Kindle Importer]({{site.baseurl}}/importers/Kindle). They have essentially the same features.

![](https://camo.githubusercontent.com/3f08051e2956b5d20c14ffcb5fcc91c694c2fa61359315fa8ca9b5ea15f2e24e/68747470733a2f2f692e706f7374696d672e63632f35796a33566a50422f6f75742e676966)