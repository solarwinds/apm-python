import pytest
from solarwinds_apm.oboe.transaction_name_calculator import resolve_transaction_name

def test_resolve_transaction_name_nothing():
    assert resolve_transaction_name("", "", "") == "unknown"

def test_resolve_transaction_name_transaction_name_only():
    assert resolve_transaction_name("transaction", "", "") == "transaction"
    assert resolve_transaction_name("/transaction", "", "") == "/transaction"
    assert resolve_transaction_name("transaction/", "", "") == "transaction/"
    assert resolve_transaction_name("/transaction/", "", "") == "/transaction/"

def test_resolve_transaction_name_domain_only():
    assert resolve_transaction_name("", "domain", "") == "domain/"

def test_resolve_transaction_name_uri_only():
    assert resolve_transaction_name("", "", "http://www.boost.org/index.html") == "/index.html"
    assert resolve_transaction_name("", "", "http://www.boost.org/index.html?field=value") == "/index.html"
    assert resolve_transaction_name("", "", "http://www.boost.org/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("", "", "http://www.boost.org:80/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("", "", "https://www.boost.org/index.html") == "/index.html"
    assert resolve_transaction_name("", "", "https://www.boost.org/index.html?field=value") == "/index.html"
    assert resolve_transaction_name("", "", "https://www.boost.org/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("", "", "https://www.boost.org:80/index.html?field=value#downloads") == "/index.html"
    assert resolve_transaction_name("", "", "https://example.com") == "/"
    assert resolve_transaction_name("", "", "https://example.com:8080") == "/"
    assert resolve_transaction_name("", "", "https://example.com/") == "/"
    assert resolve_transaction_name("", "", "https://example.com:8080/") == "/"
    assert resolve_transaction_name("", "", "ftp://example.com") == "/"
    assert resolve_transaction_name("", "", "ftp://example.com:8000") == "/"
    assert resolve_transaction_name("", "", "sftp://example.com") == "/"
    assert resolve_transaction_name("", "", "sftp://example.com:8000") == "/"
    assert resolve_transaction_name("", "", "http://www.boost.org/1/2/3/4/5/index.html?field=value#downloads") == "/1/2"
    assert resolve_transaction_name("", "", "http://www.boost.org:8000/1/2/3/4/5/index.html?field=value#downloads") == "/1/2"
    assert resolve_transaction_name("", "", "https://user:pass@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("", "", "https://@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("", "", "https://user@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("", "", "https://:pass@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("", "", "https://:@example.com/1/a.html") == "/1/a.html"
    assert resolve_transaction_name("", "", "a") == "/a"
    assert resolve_transaction_name("", "", "/a") == "/a"
    assert resolve_transaction_name("", "", "/a/b") == "/a/b"
    assert resolve_transaction_name("", "", "/") == "/"
    assert resolve_transaction_name("", "", "images/dot.gif?v=hide#a") == "/images/dot.gif"

def test_resolve_transaction_name_transaction_and_domain():
    assert resolve_transaction_name("transaction.name.go", "domain.a.b.c.d.com", "") == "domain.a.b.c.d.com/transaction.name.go"

def test_resolve_transaction_name_domain_and_uri():
    domain = "domain.a.b.c.d.com"
    assert resolve_transaction_name("", domain, "http://www.boost.org/index.html") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "http://www.boost.org/index.html?field=value") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "http://www.boost.org/index.html?field=value#downloads") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "http://www.boost.org:80/index.html?field=value#downloads") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "https://www.boost.org/index.html") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "https://www.boost.org/index.html?field=value") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "https://www.boost.org/index.html?field=value#downloads") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "https://www.boost.org:80/index.html?field=value#downloads") == domain + "/index.html"
    assert resolve_transaction_name("", domain, "https://example.com") == domain + "/"
    assert resolve_transaction_name("", domain, "https://example.com:8080") == domain + "/"
    assert resolve_transaction_name("", domain, "https://example.com/") == domain + "/"
    assert resolve_transaction_name("", domain, "https://example.com:8080/") == domain + "/"
    assert resolve_transaction_name("", domain, "ftp://example.com") == domain + "/"
    assert resolve_transaction_name("", domain, "ftp://example.com:8000") == domain + "/"
    assert resolve_transaction_name("", domain, "sftp://example.com") == domain + "/"
    assert resolve_transaction_name("", domain, "sftp://example.com:8000") == domain + "/"
    assert resolve_transaction_name("", domain, "http://www.boost.org/1/2/3/4/5/index.html?field=value#downloads") == domain + "/1/2"
    assert resolve_transaction_name("", domain, "http://www.boost.org:8000/1/2/3/4/5/index.html?field=value#downloads") == domain + "/1/2"
    assert resolve_transaction_name("", domain, "https://user:pass@example.com/1/a.html") == domain + "/1/a.html"
    assert resolve_transaction_name("", domain, "https://@example.com/1/a.html") == domain + "/1/a.html"
    assert resolve_transaction_name("", domain, "https://user@example.com/1/a.html") == domain + "/1/a.html"
    assert resolve_transaction_name("", domain, "https://:pass@example.com/1/a.html") == domain + "/1/a.html"
    assert resolve_transaction_name("", domain, "https://:@example.com/1/a.html") == domain + "/1/a.html"

def test_resolve_transaction_name_uri():
    assert resolve_transaction_name("", "", "/index.html") == "/index.html"
    assert resolve_transaction_name("", "", "/info.php") == "/info.php"
    assert resolve_transaction_name("", "", "/api/app.php") == "/api/app.php"
    assert resolve_transaction_name("", "", "/1/2/3/4.php") == "/1/2"

def test_resolve_transaction_name_transaction_and_uri():
    assert resolve_transaction_name("transaction", "", "http://www.boost.org/index.html") == "transaction"

def test_resolve_transaction_name_transaction_and_domain_and_uri():
    assert resolve_transaction_name("transaction", "domain", "http://www.boost.org/index.html") == "domain/transaction"

def test_resolve_transaction_name_length_limit():
    name_len_255 = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstu"
    assert resolve_transaction_name(name_len_255 + "v", "", "") == name_len_255
