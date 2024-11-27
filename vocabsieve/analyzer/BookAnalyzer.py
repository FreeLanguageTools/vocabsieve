from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QHBoxLayout, QSlider, QWidget, QCheckBox, QSpinBox, QPushButton, QFormLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
import os
from operator import itemgetter
from ..tools import ebook2text, starts_with_cyrillic, prettydigits, amount_and_percent, grouper, window, get_first_number
import time
from statistics import stdev, mean
from ..lemmatizer import lem_word
from ..importer import WordListImporter
from ..global_names import logger, settings
import itertools
import random
import numpy as np
from pyqtgraph import PlotWidget, AxisItem
from collections import Counter
from multiprocessing import Pool, freeze_support
import threading

freeze_support()


class BookAnalyzer(QDialog):
    def __init__(self, parent, path):
        logger.debug("Initializing BookAnalyzer")
        super().__init__(parent)
        self.parent = parent
        self.path = path
        bookname, _ = os.path.splitext(os.path.basename(self.path))
        self.setWindowTitle("Analysis of " + bookname)
        self.langcode = settings.value('target_language', 'en')
        self.splitter = parent.splitter
        self.chapters, self.ch_pos = ebook2text(self.path)
        self._layout = QGridLayout(self)
        self._layout.addWidget(QLabel("<h1>Analysis of \"" + bookname + "\"</h1>"), 0, 0, 1, 2)
        self.known_words, _ = parent.getKnownWords()
        self.is_drawing_lock = threading.Lock()
        self.initWidgets()
        self.show()

    def initWidgets(self):
        self.basic_info_left = ""
        if self.langcode in ['ru', 'uk', 'bg', 'mk', 'be', 'kk', 'ky', 'mn', 'tg', 'uz']:
            # languages: Russian, Ukrainian, Bulgarian, Macedonian, Belarusian, Kazakh,
            # Kyrgyz, Mongolian, Tajik, Uzbek
            self.known_words = {word for word in self.known_words if starts_with_cyrillic(word)}
        else:
            self.known_words = set(self.known_words)
        logger.debug(f"Known words: {len(self.known_words)}")
        self.content = "\n".join(self.chapters)

        self._layout.addWidget(QLabel("<h2>General info</h2>"), 2, 0, 1, 2)
        self.basic_info_left += "Total characters: " + prettydigits(len(self.content))
        self.basic_info_left += "<br>Total words: " + prettydigits(len(self.content.split()))
        #self.progress = QProgressDialog("Splitting book into sentences...", "Cancel", 0, len(self.content), self)
        with Pool() as p:
            start = time.time()
            self.sentences = list(sentence for sentence in
                                  itertools.chain.from_iterable(
                                      p.starmap(self.splitter.split, ((ch,) for ch in self.chapters))
                                  )
                                  if sentence)
            logger.debug(f"Split book in { time.time() - start } seconds.")

            start = time.time()
            self.words = list(p.starmap(lem_word, ((word, self.langcode) for word in self.content.split())))
            logger.debug(f"Lemmatized book in { time.time() - start } seconds.")
        unique_words_3k = []
        unique_words_10k = []
        # Unique words per 3000 tokens
        for w in grouper(self.words, 3000):
            unique_words_3k.append(len(set(w)))
        for w in grouper(self.words, 10000):
            unique_words_10k.append(len(set(w)))

        self.basic_info_left += "<br>Total sentences: " + prettydigits(len(self.sentences))
        self.basic_info_left += "<br>Unique lemmas per 3000: " + \
            str(round(mean(unique_words_3k))) + " ± " + str(round(stdev(unique_words_3k), 1))
        self._layout.addWidget(QLabel(self.basic_info_left), 3, 0)
        self.basic_info_right = ""
        self.basic_info_right += "Avg. word length: " + \
            str(round(len(self.content) / len(self.content.split()), 2)) + " ± " + str(round(stdev([len(word) for word in self.content.split()]), 2))
        self.basic_info_right += "<br>Avg. sentence length (chars, incl. spaces): " + str(round(mean(
            [len(sentence) for sentence in self.sentences]), 2)) + " ± " + str(round(stdev([len(sentence) for sentence in self.sentences]), 2))
        self.basic_info_right += "<br>Avg. sentence length (words): " + str(round(mean([len(sentence.split(
        )) for sentence in self.sentences]), 2)) + " ± " + str(round(stdev([len(sentence.split()) for sentence in self.sentences]), 2))
        self.basic_info_right += "<br>Unique lemmas per 10000: " + \
            str(round(mean(unique_words_10k))) + " ± " + str(round(stdev(unique_words_10k), 1))
        self._layout.addWidget(QLabel(self.basic_info_right), 3, 1)
        self._layout.addWidget(QLabel("<h2>Vocabulary coverage</h2>"), 4, 0)
        self.vocab_coverage = ""
        occurrences = sorted(Counter(self.words).items(), key=itemgetter(1), reverse=True)
        topN = list(zip(*occurrences[:100]))[0]
        self.known_words = set(self.known_words)
        self.known_words.update(topN)
        unknown_words = [word for word in self.words if word not in self.known_words]
        self.vocab_coverage += "Unknown lemmas: " + amount_and_percent(len(unknown_words), len(self.words))
        self.vocab_coverage += "<br>Unknown unique lemmas: " + \
            amount_and_percent(len(set(unknown_words)), len(set(self.words)))
        self._layout.addWidget(QLabel(self.vocab_coverage), 5, 0)

        self.plotwidget_words = PlotWidget()
        self.plotwidget_words.setTitle("Unique unknown words per " + str(1000) + " words")
        bgcolor = self.parent.palette().color(QPalette.Background)
        self.plotwidget_words.setBackground(bgcolor)
        self.plotwidget_words.addLegend()

        self.updateWordChart(self.words, settings.value("analyzer/word_step_size", 100, type=int))
        self.plotwidget_sentences = PlotWidget()
        self.plotwidget_sentences.setTitle("Sentence target count")
        self.plotwidget_sentences.setBackground(bgcolor)
        self.plotwidget_sentences.addLegend()
        self._layout.addWidget(self.plotwidget_words, 6, 0, 1, 2)

        learning_rate_box = QWidget()
        learning_rate_box_layout = QHBoxLayout(learning_rate_box)
        learning_rate_box_layout.addWidget(QLabel("Learning rate: "))
        self.learning_rate_slider = QSlider(Qt.Horizontal)
        self.learning_rate_slider.setMinimum(0)
        self.learning_rate_slider.setMaximum(100)
        self.learning_rate_slider.setValue(40)
        learning_rate_box_layout.addWidget(self.learning_rate_slider)
        learning_rate_label = QLabel("40%")
        learning_rate_box_layout.addWidget(learning_rate_label)
        self.learning_rate_slider.valueChanged.connect(lambda x: learning_rate_label.setText(str(x) + "%"))
        self.learned_words_count_label = QLabel()
        learning_rate_box_layout.addWidget(self.learned_words_count_label)

        self.learning_rate_slider.sliderReleased.connect(self.onSliderRelease)
        self.label_0t = QLabel()
        self.label_1t = QLabel()
        self.label_2t = QLabel()
        self.label_3t = QLabel()
        self.label_0t.setToolTip("Sentences expected to be encountered, where you know all lemmas")
        self.label_1t.setToolTip("Sentences expected to be encountered, where you know all but one lemma")
        self.label_2t.setToolTip("Sentences expected to be encountered, where you know all but two lemmas")
        self.label_3t.setToolTip("Sentences expected to be encountered, where at least three lemmas are unknown to you")

        sentence_target_counts = self.categorizeSentences(self.sentences, self.learning_rate_slider.value() / 100)

        if sentence_target_counts is None:
            return

        self._layout.addWidget(QLabel("<h3>Sentence types</h3>"), 7, 0)
        self._layout.addWidget(self.label_0t, 8, 0)
        self._layout.addWidget(self.label_1t, 9, 0)
        self._layout.addWidget(self.label_2t, 10, 0)
        self._layout.addWidget(self.label_3t, 11, 0)

        start = time.time()

        target_words_in_3t = []
        sentences_3t = [sentence for sentence in self.sentences if self.countTargets3(sentence) == 3]
        for sentence in sentences_3t:
            target_words_in_3t.extend([lem_word(word, self.langcode) for word in sentence.split()
                                      if lem_word(word, self.langcode) not in self.known_words])

        occurrences_3t = Counter(target_words_in_3t)
        # Get the most frequent words in 3t sentences
        cram_widget_box = QWidget()
        self._layout.addWidget(cram_widget_box, 7, 1, 5, 1)
        cram_widget_box_layout = QFormLayout(cram_widget_box)
        cram_widget_box_layout.addRow(QLabel("<h3>Cram words</h3>"))
        cram_buttons = []
        for n_cram in [100, 200, 400, 800]:
            most_frequent_3t = [word for word, _ in occurrences_3t.most_common(n_cram)]
            tmp_known_words = self.known_words.union(set(most_frequent_3t))
            new_count_3t = [self.countTargets3(sentence, tmp_known_words) for sentence in sentences_3t].count(3)
            cram_widget = QLabel(
                f"Cram {n_cram} words: {amount_and_percent(new_count_3t, len(self.sentences))} ≥3T sentences")
            cram_widget.setToolTip(
                f"After learning the {n_cram} most occuring words, the book would contain this many ≥3T sentences")
            cram_buttons.append(QPushButton("Import"))
            cram_buttons[-1].clicked.connect(lambda _, words=most_frequent_3t: self.cramWords(words))
            cram_widget_box_layout.addRow(cram_widget, cram_buttons[-1])

        logger.debug("Calculated cram words in " + str(time.time() - start) + " seconds.")

        verdict = ""

        if len(sentences_3t) / len(sentence_target_counts) > 0.15:
            verdict = "Too hard"
        elif len(sentences_3t) / len(sentence_target_counts) > 0.08:
            verdict = "Hard"
        elif len(sentences_3t) / len(sentence_target_counts) > 0.03:
            verdict = "Moderate"
        elif len(sentences_3t) / len(sentence_target_counts) < 0.03:
            verdict = "Easy"

        show_chapter_names_button = QCheckBox("Toggle full chapter names")
        show_chapter_names_button.clicked.connect(self.addChapterAxes)
        self._layout.addWidget(QLabel("<h3>Predicted difficulty: " + verdict + "</h3>"), 1, 0)
        self._layout.addWidget(show_chapter_names_button, 1, 1)

        self._layout.addWidget(learning_rate_box, 12, 0, 1, 2)
        self._layout.addWidget(self.plotwidget_sentences, 13, 0, 1, 2)

        start = time.time()
        if self.ch_pos:
            # convert character positions to word positions
            self.ch_pos_word = {len(self.content[:pos].split()): name for pos, name in self.ch_pos.items()}
            logger.debug(f"Converted character positions to word positions in {time.time() - start} seconds.")
            start = time.time()
            # convert character positions to sentence positions
            self.ch_pos_sent = {}
            length = 0
            for n, sentence in enumerate(self.sentences):
                length += len(sentence)
                try:
                    if length > next(iter(self.ch_pos)):
                        self.ch_pos_sent[n] = self.ch_pos[next(iter(self.ch_pos))]
                        del self.ch_pos[next(iter(self.ch_pos))]
                except StopIteration:
                    pass
            logger.debug(f"Converted character positions to sentence positions in { time.time() - start } seconds.")
            self.addChapterAxes()
        logger.debug(f"Chapter axes added in {time.time() - start} seconds.")

        self._layout.addWidget(QLabel("Word chart step size:"), 14, 0)
        self.word_chart_step_size = QSpinBox()
        self.word_chart_step_size.setMinimum(1)
        self.word_chart_step_size.setSingleStep(10)
        self.word_chart_step_size.setMaximum(1000)
        self.word_chart_step_size.setValue(settings.value("analyzer/word_step_size", 100, type=int))
        self.word_chart_step_size.editingFinished.connect(
            lambda: self.updateWordChart(
                self.words, self.word_chart_step_size.value()))
        self.word_chart_step_size.editingFinished.connect(
            lambda: settings.setValue(
                "analyzer/word_step_size",
                self.word_chart_step_size.value()))
        self._layout.addWidget(self.word_chart_step_size, 14, 1)
        self._layout.addWidget(QLabel("Sentence chart step size:"), 15, 0)
        self.sentence_chart_step_size = QSpinBox()
        self._layout.addWidget(self.sentence_chart_step_size, 15, 1)
        self.sentence_chart_step_size.setValue(settings.value("analyzer/sentence_window_size", 100, type=int))
        self.sentence_chart_step_size.setMinimum(10)
        self.sentence_chart_step_size.setSingleStep(5)
        self.sentence_chart_step_size.setMaximum(1000)
        self.sentence_chart_step_size.editingFinished.connect(self.updateSentenceChart)

    def cramWords(self, words):
        WordListImporter(self.parent, words).exec()

    def updateWordChart(self, words, step_size=100):
        with self.is_drawing_lock:
            start = time.time()
            unique_count = []
            new_unique_count = []
            already_seen: set[str] = set()
            window_size = 1000
            startlens: list[int] = []
            for n, w in enumerate(window(words, window_size)):
                if n % step_size == 0:
                    already_seen = already_seen.union(set(w)).difference(self.known_words)
                    if n - window_size >= 0:
                        difference = len(already_seen) - startlens[(n - window_size) // step_size]
                    else:
                        difference = None
                    if difference:
                        new_unique_count.append(difference)
                    else:
                        new_unique_count.append(np.nan)
                    startlens.append(len(already_seen))
                    unique_count.append(len(set(w) - self.known_words))

            logger.debug("Calculated unique unknown words in " + str(time.time() - start) + " seconds.")

            self.plotwidget_words.clear()
            self.plotwidget_words.plot(list(range(0, len(unique_count) * step_size, step_size)),
                                       unique_count, pen='#4e79a7', name="Unique unknown words")
            self.plotwidget_words.plot(
                list(
                    range(
                        0,
                        len(new_unique_count) *
                        step_size,
                        step_size)),
                new_unique_count,
                pen='#f28e2b',
                name="New unique unknown words")
            # Add X axis label
            self.plotwidget_words.setLabel('bottom', 'Words')
            # Add Y axis label
            self.plotwidget_words.setLabel('left', 'Count')

    def addChapterAxes(self, names=False):
        # Match first number from string
        if not names:
            ch_pos_word = [{pos: get_first_number(name) for pos, name in self.ch_pos_word.items()}.items()]
            ch_pos_sent = [{pos: get_first_number(name) for pos, name in self.ch_pos_sent.items()}.items()]
        else:
            ch_pos_word = [self.ch_pos_word.items()]
            ch_pos_sent = [self.ch_pos_sent.items()]
        word_chapter_axis = AxisItem('top')
        word_chapter_axis.setLabel("Chapter")
        word_chapter_axis.setTicks(ch_pos_word)
        self.plotwidget_words.setAxisItems({'top': word_chapter_axis})
        sentence_chapter_axis = AxisItem('top')
        sentence_chapter_axis.setLabel("Chapter")
        sentence_chapter_axis.setTicks(ch_pos_sent)
        self.plotwidget_sentences.setAxisItems({'top': sentence_chapter_axis})

    def onSliderRelease(self):
        self.learning_rate = self.learning_rate_slider.value() / 100
        self.categorizeSentences(self.sentences, self.learning_rate)

    def updateSentenceChart(self):
        window_size = self.sentence_chart_step_size.value()
        self.learning_rate = self.learning_rate_slider.value() / 100
        self.categorizeSentences(self.sentences, self.learning_rate, window_size)
        settings.setValue("analyzer/sentence_window_size", window_size)

    def categorizeSentences(self, sentences, learning_rate, window_size=None):
        with self.is_drawing_lock:
            if window_size is None:
                window_size = settings.value("analyzer/sentence_window_size", 80, type=int)
            start = time.time()
            logger.debug(f"Categorizing sentences at learning rate { learning_rate }")
            counts_0t = []
            counts_1t = []
            counts_2t = []
            counts_3t = []
            known_words = self.known_words.copy()
            learned_words = set()
            sentence_target_counts = []
            for w in grouper(sentences, window_size):
                w_counts = [self.countTargets3(sentence, known_words) for sentence in w if sentence]
                sents_1t = [sentence for i, sentence in zip(w_counts, w) if i == 1]
                sents_2t = [sentence for i, sentence in zip(w_counts, w) if i == 2]
                sents_3t = [sentence for i, sentence in zip(w_counts, w) if i == 3]
                sents_to_learn = []
                sents_to_learn.extend(random.sample(sents_1t, int(len(sents_1t) * learning_rate)))
                sents_to_learn.extend(random.sample(sents_2t, int(len(sents_2t) * learning_rate**2)))
                sents_to_learn.extend(random.sample(sents_3t, int(len(sents_3t) * learning_rate**3)))
                words_to_learn = list(itertools.chain(
                    *[self.getTargets(sentence, known_words) for sentence in sents_to_learn]))
                learned_words.update(words_to_learn)
                known_words.update(words_to_learn)

                sentence_target_counts.extend(w_counts)
                counts_0t.append(w_counts.count(0) / len(w_counts))
                counts_1t.append(w_counts.count(1) / len(w_counts))
                counts_2t.append(w_counts.count(2) / len(w_counts))
                counts_3t.append(w_counts.count(3) / len(w_counts))
            self.plotwidget_sentences.clear()
            self.plotwidget_sentences.plot(
                list(
                    range(
                        0,
                        len(counts_0t) *
                        window_size,
                        window_size)),
                counts_0t,
                pen='#4e79a7',
                name="0T")
            self.plotwidget_sentences.plot(
                list(
                    range(
                        0,
                        len(counts_1t) *
                        window_size,
                        window_size)),
                counts_1t,
                pen='#59a14f',
                name="1T")
            self.plotwidget_sentences.plot(
                list(
                    range(
                        0,
                        len(counts_2t) *
                        window_size,
                        window_size)),
                counts_2t,
                pen='#f28e2b',
                name="2T")
            self.plotwidget_sentences.plot(
                list(
                    range(
                        0,
                        len(counts_3t) *
                        window_size,
                        window_size)),
                counts_3t,
                pen='#e15759',
                name="≥3T")

            self.label_0t.setText(
                "0T: " +
                amount_and_percent(
                    sentence_target_counts.count(0),
                    len(sentence_target_counts)))
            self.label_1t.setText(
                "1T: " +
                amount_and_percent(
                    sentence_target_counts.count(1),
                    len(sentence_target_counts)))
            self.label_2t.setText(
                "2T: " +
                amount_and_percent(
                    sentence_target_counts.count(2),
                    len(sentence_target_counts)))
            self.label_3t.setText(
                "≥3T: " +
                amount_and_percent(
                    sentence_target_counts.count(3),
                    len(sentence_target_counts)))
            self.learned_words_count_label.setText(str(len(learned_words)) + " words will be learned")

            logger.debug(f"Categorization done in { time.time() - start } seconds.")
        return sentence_target_counts

    def getTargets(self, sentence, known_words=None):
        if not known_words:
            known_words = self.known_words
        targets = [
            lem_word(word, self.langcode)
            for word in sentence.split()
            if lem_word(word, self.langcode) not in known_words
        ]
        return targets

    def countTargets3(self, sentence, known_words=None):
        if not known_words:
            known_words = self.known_words
        targets = [
            lem_word(word, self.langcode)
            for word in sentence.split()
            if lem_word(word, self.langcode) not in known_words
        ]
        return min(len(targets), 3)
