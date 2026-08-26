from nyc_movie_alert.matcher import find_link_for_title, find_match, normalize


def test_normalize_strips_punctuation_and_case():
    assert normalize("It's a Wonderful Life!") == normalize("its a wonderful life")


def test_find_match_exact():
    assert find_match("Blade Runner", "<h2>Now Playing: Blade Runner</h2>")


def test_find_match_punctuation_insensitive():
    assert find_match("It's a Wonderful Life", "<p>Its A Wonderful Life -- 7:30pm</p>")


def test_find_match_no_match():
    assert not find_match("Blade Runner", "<p>Casablanca, The Godfather</p>")


def test_find_match_empty_title():
    assert not find_match("", "<p>anything</p>")


def test_find_link_for_title():
    html = '<a href="/films/blade-runner">Blade Runner</a>'
    assert find_link_for_title("Blade Runner", html) == "/films/blade-runner"


def test_find_link_for_title_missing():
    html = '<a href="/films/casablanca">Casablanca</a>'
    assert find_link_for_title("Blade Runner", html) is None
