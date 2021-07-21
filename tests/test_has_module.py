def test_import_module():
    try:
        import ssmtool
        assert True
    except:
        assert False, "Can't import ssmtool"
