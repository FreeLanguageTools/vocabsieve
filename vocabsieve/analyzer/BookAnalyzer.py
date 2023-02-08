from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os
from sentence_splitter import split_text_into_sentences
from operator import itemgetter
from ..tools import *
import time
from statistics import stdev, mean
from ..lemmatizer import lem_word
from ..known_words import getKnownData
import json
import numpy as np
from pyqtgraph import PlotWidget
from collections import Counter

prettydigits = lambda number: format(number, ',').replace(',', ' ')

class BookAnalyzer(QDialog):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.parent = parent
        self.path = path
        bookname, _ = os.path.splitext(os.path.basename(self.path))
        self.setWindowTitle("Analysis of " + bookname)
        self.langcode = self.parent.settings.value('target_language', 'en')
        self.content = ebook2text(self.path)
        self.layout = QGridLayout(self)
        self.layout.addWidget(QLabel("<h1>Analysis of \"" + bookname + "\"</h1>"), 0, 0, 1, 2)
        self.score, *_ = getKnownData(self.parent.settings, self.parent.rec)
        threshold = self.parent.settings.value('tracking/known_threshold', 100, type=int)
        self.known_words = [word for word, points in self.score.items() if points >= threshold and word.isalpha()]
        self.initWidgets()
        self.show()
    
    def initWidgets(self):
        self.basic_info_left = ""
        if self.langcode in ['ru', 'uk']:
            self.known_words = [word for word in self.known_words if starts_with_cyrillic(word)]
        
        print(self.langcode)
        print(len(self.known_words))
        self.layout.addWidget(QLabel("<h3>General info</h3>"), 1, 0, 1, 2)
        self.basic_info_left += "Total characters: " + prettydigits(len(self.content))
        self.basic_info_left += "<br>Total words: " + prettydigits(len(self.content.split()))
        #self.progress = QProgressDialog("Splitting book into sentences...", "Cancel", 0, len(self.content), self)
        start = time.time()

        sentences = [sentence for sentence in split_text_into_sentences(self.content, self.langcode) if sentence]
        print("Split book in " + str(time.time() - start) + " seconds.")
        self.basic_info_left += "<br>Total sentences: " + prettydigits(len(sentences))
        self.layout.addWidget(QLabel(self.basic_info_left), 2, 0)
        self.basic_info_right = ""
        self.basic_info_right += "Avg. word length: " + str(round(len(self.content) / len(self.content.split()), 2)) + " ± " + str(round(stdev([len(word) for word in self.content.split()]), 2))
        self.basic_info_right += "<br>Avg. sentence length (chars, incl. spaces): " + str(round(mean([len(sentence) for sentence in sentences]), 2)) + " ± " + str(round(stdev([len(sentence) for sentence in sentences]), 2))
        self.basic_info_right += "<br>Avg. sentence length (words): " + str(round(mean([len(sentence.split()) for sentence in sentences]), 2)) + " ± " + str(round(stdev([len(sentence.split()) for sentence in sentences]), 2))
        self.layout.addWidget(QLabel(self.basic_info_right), 2, 1)
        self.layout.addWidget(QLabel("<h3>Vocabulary coverage</h3>"), 3, 0)
        self.vocab_coverage = ""
        start = time.time()
        words = [lem_word(word, self.langcode) for word in self.content.split()]
        print("Lemmatized book in " + str(time.time() - start) + " seconds.")
        occurrences = sorted(Counter(words).items(), key=itemgetter(1), reverse=True)
        topN = list(zip(*occurrences[:100]))[0]
        self.known_words.extend(topN)
        self.known_words = set(self.known_words)
        unknown_words = [word for word in words if word not in self.known_words]
        self.vocab_coverage += "Unknown lemmas: " + prettydigits(len(unknown_words)) + " (" + str(round(len(unknown_words) / len(words) * 100, 2)) + "%)"
        self.vocab_coverage += "<br>Unknown unique lemmas: " + prettydigits(len(set(unknown_words))) + " (" + str(round(len(set(unknown_words)) / len(set(words)) * 100, 2)) + "%)"
        self.layout.addWidget(QLabel(self.vocab_coverage), 4, 0)

        start = time.time()
        unique_count = []
        new_unique_count = []
        already_seen = set()
        window_size = 1000
        step_size = 50
        startlens = []
        for n, w in enumerate(window(words, window_size)):
            if n % step_size == 0:
                
                already_seen = already_seen.union(set(w)) - self.known_words
                if n - window_size >= 0:
                    difference = len(already_seen) - startlens[n - window_size]
                else:
                    difference = None
            if difference:
                new_unique_count.append(difference)
            else:
                new_unique_count.append(np.nan)
            startlens.append(len(already_seen))
            unique_count.append(len(set(w) - self.known_words))
        print("Calculated unique unknown words in " + str(time.time() - start) + " seconds.")
        self.plotwidget_words = PlotWidget()
        
        self.plotwidget_words.setTitle("Unique unknown words per " + str(window_size) + " words")
        self.plotwidget_words.setBackground('#ffffff')
        self.plotwidget_words.addLegend()
        self.plotwidget_words.plot(unique_count, pen='#4e79a7', name="Unique unknown words")
        self.plotwidget_words.plot(new_unique_count, pen='#f28e2b', name="New unique unknown words")
        # Add X axis label
        self.plotwidget_words.setLabel('bottom', 'Words')
        # Add Y axis label
        self.plotwidget_words.setLabel('left', 'Count')
        self.layout.addWidget(self.plotwidget_words, 5, 0, 1, 2)

        self.plotwidget_sentences = PlotWidget()
        self.plotwidget_sentences.setTitle("Sentence target count")

        sentence_target_counts = [self.countTargets3(sentence) for sentence in sentences]
        print(len(sentence_target_counts))
        self.plotwidget_sentences.setBackground('#ffffff')
        self.plotwidget_sentences.addLegend()
        counts_0t = []
        counts_1t = []
        counts_2t = []
        counts_3t = []
        window_size = 300
        for w in window(sentence_target_counts, window_size):
            counts_0t.append(w.count(0)/window_size)
            counts_1t.append(w.count(1)/window_size)
            counts_2t.append(w.count(2)/window_size)
            counts_3t.append(w.count(3)/window_size)
        self.plotwidget_sentences.plot(counts_0t, pen='#4e79a7', name="0T")
        self.plotwidget_sentences.plot(counts_1t, pen='#59a14f', name="1T")
        self.plotwidget_sentences.plot(counts_2t, pen='#f28e2b', name="2T")
        self.plotwidget_sentences.plot(counts_3t, pen='#e15759', name=">3T")
        self.layout.addWidget(QLabel("<h3>Sentence types</h3>"), 6, 0)
        self.layout.addWidget(QLabel("0T: " + str(sentence_target_counts.count(0)) + " (" + str(round(sentence_target_counts.count(0) / len(sentence_target_counts) * 100, 2)) + "%)"), 7, 0)
        self.layout.addWidget(QLabel("1T: " + str(sentence_target_counts.count(1)) + " (" + str(round(sentence_target_counts.count(1) / len(sentence_target_counts) * 100, 2)) + "%)"), 7, 1)
        self.layout.addWidget(QLabel("2T: " + str(sentence_target_counts.count(2)) + " (" + str(round(sentence_target_counts.count(2) / len(sentence_target_counts) * 100, 2)) + "%)"), 8, 0)
        self.layout.addWidget(QLabel(">3T: " + str(sentence_target_counts.count(3)) + " (" + str(round(sentence_target_counts.count(3) / len(sentence_target_counts) * 100, 2)) + "%)"), 8, 1)
        
        verdict = ""
        if sentence_target_counts.count(3) / len(sentence_target_counts) > 0.20:
            verdict = "Too hard"
        elif sentence_target_counts.count(3) / len(sentence_target_counts) > 0.10:
            verdict = "Hard"
        elif sentence_target_counts.count(3) / len(sentence_target_counts) > 0.05:
            verdict = "Moderate"
        elif sentence_target_counts.count(3) / len(sentence_target_counts) < 0.05:
            verdict = "Easy"

        self.layout.addWidget(QLabel("<h4>Verdict: " + verdict + "</h4>"), 9, 0, 1, 2)
        self.layout.addWidget(self.plotwidget_sentences, 10, 0, 1, 2)
        
    
    def countTargets3(self, sentence):
        targets = [
            lem_word(word, self.langcode) 
            for word in sentence.split() 
            if lem_word(word, self.langcode) not in self.known_words
            ]
        return min(len(targets), 3)