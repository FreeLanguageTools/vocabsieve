from vocabsieve.local_dictionary import LocalDictionary


def test_local_dictionary(tmp_path):
    db = LocalDictionary(tmp_path)
    print(tmp_path)
    assert db.countDicts() == 0
    db.importdict({"test": "a test is a test"}, "de", "test-dict")
    assert db.countDicts() == 1
    assert db.define("test", "de", "test-dict") == "a test is a test"
    db.deletedict("test-dict")
    assert db.countDicts() == 0


def test_import_stardict_normal(tmp_path):
    db = LocalDictionary(tmp_path)
    assert db.countDicts() == 0
    db.dictimport("testdata/stardict/quick_eng-rus-2.4.2/quick_english-russian.ifo",
                  dicttype="stardict",
                  lang="en",
                  name="quick_eng-rus-2.4.2")
    assert db.countDicts() == 1
    assert db.define("abdominous", "en", "quick_eng-rus-2.4.2") == "толстый"
    assert db.define("loophole", "en", "quick_eng-rus-2.4.2") == "бойница"
    assert db.define("luggage", "en", "quick_eng-rus-2.4.2") == "багаж"


def test_import_stardict_xdxf(tmp_path):
    db = LocalDictionary(tmp_path)
    assert db.countDicts() == 0
    db.dictimport("testdata/stardict/stardict-FR-LingvoUniversal-2.4.2/FR-Universal.ifo",
                  dicttype="stardict",
                  lang="fr",
                  name="fr-universal")
    assert db.countDicts() == 1
    assert db.define("accouchement", "fr", "fr-universal") == '''<i>m</i>
 1) р'оды
  accouchement avant terme, accouchement prématuré — преждевр'еменные р'оды
  accouchement après terme, accouchement tardif — запозд'алые р'оды
  accouchement sans douleur — обезб'оливание р'одов
  douleurs de l'accouchement — родов'ые б'оли
 2) <i>перен.</i> дл'ительное созрев'ание, тр'удное осуществл'ение'''
    assert db.define("persévérant", "fr", "fr-universal") == '''<i>adj</i>, <i>subst</i> (<i>fém</i> - persévérante)
 1) наст'ойчивый [наст'ойчивая], уп'орный [уп'орная]; твёрдый [твёрдая]
 2) посто'янный [посто'янная]'''
    assert db.define("pièce-raccord", "fr", "fr-universal") == '''pièce-raccord
 <i>m</i>
 <i>(pl s + s</i> ) соедин'ительная часть, соедин'ительная дет'аль'''


def test_import_dsl(tmp_path):
    db = LocalDictionary(tmp_path)
    assert db.countDicts() == 0
    db.dictimport("testdata/dsl/ru_en.dsl",
                  dicttype="dsl",
                  lang="ru",
                  name="dsl_test"
                  )
    db.dictimport("testdata/dsl/ru_en.dsl.dz",
                  dicttype="dsl",
                  lang="ru",
                  name="dsl_test2"
                  )
    assert db.countDicts() == 2
    assert db.define("зубчатый", "ru", "dsl_test") == '''serrated, toothed'''
    assert db.define("лиственный", "ru", "dsl_test") == '''broadleaf; deciduous; leafy'''
    assert db.define("окорять", "ru", "dsl_test") == '''bark, peel'''
    assert db.define("зубчатый", "ru", "dsl_test2") == '''serrated, toothed'''
    assert db.define("лиственный", "ru", "dsl_test2") == '''broadleaf; deciduous; leafy'''
    assert db.define("окорять", "ru", "dsl_test2") == '''bark, peel'''
    db.dictimport("testdata/dsl/universal.dsl.dz",
                  dicttype="dsl",
                  lang="ru",
                  name="dsl_test3"
                  )
    assert db.countDicts() == 3
    assert db.define("ямчатость", "ru", "dsl_test3") == '''ж. с.-х.<br>  (патологическое свойство плодов) pit<br>'''
    assert db.define("эмиграция", "ru", "dsl_test3") == '''ж.<br>  1) (переселение из своего отечества) emigration<br>  2) (пребывание в другой стране) life in emigration<br>    жить в эмиграции — live as an emigrant / émigré (фр.) /<'emɪgreɪ/><br>  3) собир. emigrants pl; émigrés (фр.) /<'emɪgreɪz/> pl<br>'''
    assert db.define(
        "щемящий",
        "ru",
        "dsl_test3") == '''1) (ноющий, тупой) aching /<'eɪk-/>, nagging<br>    щемящая боль — nagging ache /<eɪk/><br>  2) (мучительный, гнетущий) painful, melancholy, oppressive<br>    щемящий душу напев — plaintive / melancholy /<-k-/> tune<br>'''


def test_import_cognates(tmp_path):
    db = LocalDictionary(tmp_path)
    assert db.countDicts() == 0
    db.dictimport("testdata/cognates/cognates.json.gz",
                  dicttype="cognates",
                  lang="<all>",
                  name="cognates"
                  )
    assert db.define("chodník", "cs", "cognates") == '''["sk", "pl"]'''
    assert db.define(
        "beluga",
        "hr",
        "cognates") == '''["fi", "hu", "ru", "nl", "en", "de", "bg", "fr", "ro", "ca", "mhr", "kk", "pt", "eo", "uk", "cs", "es"]'''
    assert db.define(
        "apple",
        "en",
        "cognates") == '''["nl", "ksh", "xh", "nso", "da", "kn", "hsb", "pl", "dsb", "uk", "ltg", "hr", "af", "ru", "nb", "lb", "pap", "bg", "ml", "tn", "brx", "gd", "jam", "sah", "gv", "ve", "zu", "cs", "wym", "si", "cy", "fo", "sco", "bn", "sk", "ga", "sv", "zsm", "fy", "be", "mk", "as", "mi", "cu", "lt", "abe", "de", "nn", "br", "id", "ta", "st", "kok", "te", "ms", "sl", "is"]'''
    assert db.define(
        "tragisch",
        "de",
        "cognates") == '''["nl", "fi", "ro", "pt", "pl", "hr", "hu", "nb", "ast", "fr", "ms", "eu", "eo", "cs", "ca", "sk", "sv", "lij", "es", "en", "id", "oc", "gl", "sl"]'''
    assert db.countDicts() == 1


def test_kaikki(tmp_path):
    db = LocalDictionary(tmp_path)
    assert db.countDicts() == 0
    db.dictimport("testdata/kaikki/swedish_short.json",
                  dicttype="wiktdump",
                  lang="sv",
                  name="kaikki-swedish"
                  )
    assert db.countDicts() == 1
    assert db.define("uppåkrakaka", "sv", "kaikki-swedish") == '''<i>Noun</i>
uppåkrakaka c
1. a biscuit made of mördeg (without egg), in a circular shape folded almost in the middle, garnished with chopped pistachios and nib sugar'''
    assert db.define("affektionsvärde", "sv", "kaikki-swedish") == '''<i>Noun</i>
affektionsvärde n
1. sentimental value'''
    assert db.define("rådigt", "sv", "kaikki-swedish") == '''<i>Adj</i>
rådigt
1. indefinite neuter singular of rådig

<i>Adv</i>
rådigt (comparative rådigare, superlative rådigast)
1. resourcefully, resolutely'''

    db.dictimport("testdata/kaikki/fr_short.json",
                  dicttype="wiktdump",
                  lang="fr",
                  name="kaikki-french"
                  )
    assert db.countDicts() == 2
    # french tests
    assert db.define("évhémérisassent", "fr", "kaikki-french") == """<i>Verb</i>
1. Troisième personne du pluriel de l’imparfait du subjonctif de évhémériser."""
    assert db.define("fortitrer", "fr", "kaikki-french") == """<i>Verb</i>
1. Un cerf fortitre, quand il évite de passer près des chiens frais et des relais."""
    assert db.define("géminer", "fr", "kaikki-french") == """<i>Verb</i>
1. Se doubler.
2. Grouper deux à deux, doubler."""
