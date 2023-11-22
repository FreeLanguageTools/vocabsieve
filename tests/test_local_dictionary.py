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
    assert dictdb.define("bromisme", "fr", "fr-universal") == '''<div class="article"><div class="k"><b>bromisme</b></div><i><font color="green"><span class="abr"><font color="green"><i>m</i></font></span> <span class="abr"><font color="green"><i>мед.</i></font></span></font></i><br/> бром'изм (<i>отравление бромом</i>)</div>'''
    assert dictdb.define("dédié", "fr", "fr-universal") == '''<div class="article"><div class="k"><b>dédié</b></div><font color="green"><i><span class="abr"><font color="green"><i>adj</i></font></span> <span class="abr"><font color="green"><i>вчт.</i></font></span></i> (<span class="abr"><font color="green"><i><i>fém</i></i></font></span> - dédiée); <span class="abr"><font color="green"><i><i>см.</i></i></font></span> <a class="kref" href="bword://d&#xE9;dicac&#xE9;">dédicacé</a> 2)</font></div>'''
    assert dictdb.define("usurpateur", "fr", "fr-universal") == '''<div class="article"><div class="k"><b>usurpateur</b></div><b>1.</b> <font color="green"><span class="abr"><font color="green"><i><i>m</i></i></font></span> (<span class="abr"><font color="green"><i><i>f</i></i></font></span> - usurpatrice)</font>узурп'атор, захв'атчик<br/><b>2.</b> <font color="green"><span class="abr"><font color="green"><i><i>adj</i></i></font></span> (<span class="abr"><font color="green"><i><i>fém</i></i></font></span> - usurpatrice)</font>узурп'аторский</div>'''

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
