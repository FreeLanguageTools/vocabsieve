from vocabsieve.local_dictionary import LocalDictionary

def test_local_dictionary():
    dictdb = LocalDictionary("testdir/basic")
    assert dictdb.countDicts() == 0
    dictdb.importdict({"test": "a test is a test"}, "de", "test-dict")
    assert dictdb.countDicts() == 1
    assert dictdb.define("test", "de", "test-dict") == "a test is a test"
    dictdb.deletedict("test-dict")
    assert dictdb.countDicts() == 0

def test_import_stardict_normal():
    dictdb = LocalDictionary("testdir/stardict_normal")
    assert dictdb.countDicts() == 0
    dictdb.dictimport("testdata/stardict/quick_eng-rus-2.4.2/quick_english-russian.ifo",
                      dicttype="stardict",
                      lang="en",
                      name="quick_eng-rus-2.4.2")
    assert dictdb.countDicts() == 1
    assert dictdb.define("abdominous", "en", "quick_eng-rus-2.4.2") == "толстый"
    assert dictdb.define("loophole", "en", "quick_eng-rus-2.4.2") == "бойница"
    assert dictdb.define("luggage", "en", "quick_eng-rus-2.4.2") == "багаж"
    

def test_import_stardict_xdxf():
    dictdb = LocalDictionary("testdir/stardict_xdxf")
    assert dictdb.countDicts() == 0
    dictdb.dictimport("testdata/stardict/stardict-FR-LingvoUniversal-2.4.2/FR-Universal.ifo",
                      dicttype="stardict",
                      lang="fr",
                      name="fr-universal")
    assert dictdb.countDicts() == 1
    assert dictdb.define("accouchement", "fr", "fr-universal") == '''<i>m</i>
 1) р'оды
  accouchement avant terme, accouchement prématuré — преждевр'еменные р'оды
  accouchement après terme, accouchement tardif — запозд'алые р'оды
  accouchement sans douleur — обезб'оливание р'одов
  douleurs de l'accouchement — родов'ые б'оли
 2) <i>перен.</i> дл'ительное созрев'ание, тр'удное осуществл'ение'''
    assert dictdb.define("persévérant", "fr", "fr-universal") == '''<i>adj</i>, <i>subst</i> (<i>fém</i> - persévérante)
 1) наст'ойчивый [наст'ойчивая], уп'орный [уп'орная]; твёрдый [твёрдая]
 2) посто'янный [посто'янная]'''
    assert dictdb.define("pièce-raccord", "fr", "fr-universal") == '''pièce-raccord
 <i>m</i>
 <i>(pl s + s</i> ) соедин'ительная часть, соедин'ительная дет'аль'''

def test_import_dsl():
    dictdb = LocalDictionary("testdir/dsl")
    assert dictdb.countDicts() == 0
    dictdb.dictimport("testdata/dsl/ru_en.dsl",
                      dicttype="dsl",
                      lang="ru",
                      name="dsl_test"
                      )
    dictdb.dictimport("testdata/dsl/ru_en.dsl.dz",
                      dicttype="dsl",
                      lang="ru",
                      name="dsl_test2"
                      )
    assert dictdb.countDicts() == 2
    assert dictdb.define("зубчатый", "ru", "dsl_test") == '''serrated, toothed'''
    assert dictdb.define("лиственный", "ru", "dsl_test") == '''broadleaf; deciduous; leafy'''
    assert dictdb.define("окорять", "ru", "dsl_test") == '''bark, peel'''
    assert dictdb.define("зубчатый", "ru", "dsl_test2") == '''serrated, toothed'''
    assert dictdb.define("лиственный", "ru", "dsl_test2") == '''broadleaf; deciduous; leafy'''
    assert dictdb.define("окорять", "ru", "dsl_test2") == '''bark, peel'''
    dictdb.dictimport("testdata/dsl/universal.dsl.dz",
                      dicttype="dsl",
                      lang="ru",
                      name="dsl_test3"
                      )
    assert dictdb.countDicts() == 3
    assert dictdb.define("ямчатость", "ru", "dsl_test3") == '''ж. с.-х.<br>  (патологическое свойство плодов) pit<br>'''
    assert dictdb.define("эмиграция", "ru", "dsl_test3") == '''ж.<br>  1) (переселение из своего отечества) emigration<br>  2) (пребывание в другой стране) life in emigration<br>    жить в эмиграции — live as an emigrant / émigré (фр.) /<'emɪgreɪ/><br>  3) собир. emigrants pl; émigrés (фр.) /<'emɪgreɪz/> pl<br>'''
    assert dictdb.define("щемящий", "ru", "dsl_test3") == '''1) (ноющий, тупой) aching /<'eɪk-/>, nagging<br>    щемящая боль — nagging ache /<eɪk/><br>  2) (мучительный, гнетущий) painful, melancholy, oppressive<br>    щемящий душу напев — plaintive / melancholy /<-k-/> tune<br>'''

def test_import_cognates():
    dictdb = LocalDictionary("testdir/cognates")
    assert dictdb.countDicts() == 0
    dictdb.dictimport("testdata/cognates/cognates.json.gz",
                      dicttype="cognates",
                      lang="<all>",
                      name="cognates"
                      )
    assert dictdb.countDicts() == 1
    assert dictdb.define("chodník", "cs", "cognates") == '''["sk", "pl"]'''
    assert dictdb.define("beluga", "hr", "cognates") == '''["fi", "hu", "ru", "nl", "en", "de", "bg", "fr", "ro", "ca", "mhr", "kk", "pt", "eo", "uk", "cs", "es"]'''
    assert dictdb.define("apple", "en", "cognates") == '''["nl", "ksh", "xh", "nso", "da", "kn", "hsb", "pl", "dsb", "uk", "ltg", "hr", "af", "ru", "nb", "lb", "pap", "bg", "ml", "tn", "brx", "gd", "jam", "sah", "gv", "ve", "zu", "cs", "wym", "si", "cy", "fo", "sco", "bn", "sk", "ga", "sv", "zsm", "fy", "be", "mk", "as", "mi", "cu", "lt", "abe", "de", "nn", "br", "id", "ta", "st", "kok", "te", "ms", "sl", "is"]'''
    assert dictdb.define("tragisch", "de", "cognates") == '''["nl", "fi", "ro", "pt", "pl", "hr", "hu", "nb", "ast", "fr", "ms", "eu", "eo", "cs", "ca", "sk", "sv", "lij", "es", "en", "id", "oc", "gl", "sl"]'''

def test_kaikki():
    dictdb = LocalDictionary("testdir/kaikki")
    assert dictdb.countDicts() == 0
    dictdb.dictimport("testdata/kaikki/kaikki.org-dictionary-Swedish.json.gz",
                      dicttype="wiktdump",
                      lang="sv",
                      name="kaikki-swedish"
                      )
    assert dictdb.countDicts() == 1
    assert dictdb.define("uppåkrakaka", "sv", "kaikki-swedish") == '''<i>Noun</i>
uppåkrakaka c
1. a biscuit made of mördeg (without egg), in a circular shape folded almost in the middle, garnished with chopped pistachios and nib sugar'''
    assert dictdb.define("affektionsvärde", "sv", "kaikki-swedish") == '''<i>Noun</i>
affektionsvärde n
1. sentimental value'''
    assert dictdb.define("rådigt", "sv", "kaikki-swedish") == '''<i>Adv</i>
rådigt (comparative rådigare, superlative rådigast)
1. resourcefully, resolutely'''

    dictdb.dictimport("testdata/kaikki/fr-extract.json.gz",
                      dicttype="wiktdump",
                      lang="fr",
                      name="kaikki-french"
                      )
    assert dictdb.countDicts() == 2
    # french tests
    assert dictdb.define("évhémérisassent", "fr", "kaikki-french") == """<i>Verb</i>
1. Troisième personne du pluriel de l’imparfait du subjonctif de évhémériser."""
    assert dictdb.define("fortitrer", "fr", "kaikki-french") == """<i>Verb</i>
1. Un cerf fortitre, quand il évite de passer près des chiens frais et des relais."""
    assert dictdb.define("géminer", "fr", "kaikki-french") == """<i>Verb</i>
1. Se doubler.
2. Grouper deux à deux, doubler."""
    