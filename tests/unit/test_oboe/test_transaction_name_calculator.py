from solarwinds_apm.oboe.transaction_name_calculator import resolve_transaction_name

def test_resolve_transaction_name_unknown():
    assert resolve_transaction_name(123) == "unknown"

def test_resolve_transaction_name():
    assert resolve_transaction_name("http://www.boost.org/index.html") == "/index.html"
    assert resolve_transaction_name("http://www.boost.org/index.html?field=value") == "/index.html"
    assert resolve_transaction_name("http://www.boost.org/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("http://www.boost.org:80/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("https://www.boost.org/index.html") == "/index.html"
    assert resolve_transaction_name("https://www.boost.org/index.html?field=value") == "/index.html"
    assert resolve_transaction_name("https://www.boost.org/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("https://www.boost.org:80/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("https://example.com") == "/"
    assert resolve_transaction_name("https://example.com:8080") == "/"
    assert resolve_transaction_name("https://example.com/") == "/"
    assert resolve_transaction_name("https://example.com:8080/") == "/"
    assert resolve_transaction_name("ftp://example.com") == "/"
    assert resolve_transaction_name("ftp://example.com:8000") == "/"
    assert resolve_transaction_name("sftp://example.com") == "/"
    assert resolve_transaction_name("sftp://example.com:8000") == "/"
    assert resolve_transaction_name("http://www.boost.org/1/2/3/4/5/index.html?field=value#downloads") == "/1/2"
    assert resolve_transaction_name("http://www.boost.org:8000/1/2/3/4/5/index.html?field=value#downloads") == "/1/2"
    assert resolve_transaction_name("https://user:pass@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("https://@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("https://user@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("https://:pass@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name( "https://:@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name( "a") == "/a"
    assert resolve_transaction_name( "/a") == "/a"
    assert resolve_transaction_name( "/a/b") == "/a/b"
    assert resolve_transaction_name("/") == "/"
    assert resolve_transaction_name("images/dot.gif?v=hide#a") == "/images/dot.gif"

def test_resolve_transaction_name_length_limit():
    path_len_255 = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstu"
    assert resolve_transaction_name(path_len_255) == "/" + path_len_255[:254]
