from nyc_movie_alert.extract import find_context_snippet, has_nearby_date, visible_text


def test_visible_text_strips_script_and_chrome():
    html = (
        "<html><head><script>var x = 'Blade Runner';</script></head>"
        "<body><nav>site nav</nav><main><p>Blade Runner playing</p></main>"
        "<footer>copyright</footer></body></html>"
    )
    text = visible_text(html)
    assert "Blade Runner playing" in text
    assert "site nav" not in text
    assert "copyright" not in text
    assert "var x" not in text


def test_find_context_snippet_returns_surrounding_text():
    text = "Now Playing Blade Runner - Fri, Sep 5 at 7:30pm"
    snippet = find_context_snippet("Blade Runner", text)
    assert "Blade Runner" in snippet
    assert "Sep 5" in snippet


def test_find_context_snippet_missing_title():
    assert find_context_snippet("Casablanca", "Blade Runner playing") is None


def test_has_nearby_date_true_for_weekday_and_time():
    assert has_nearby_date("Blade Runner - Fri, Sep 5 at 7:30pm")


def test_has_nearby_date_false_for_plain_mention():
    assert not has_nearby_date("Blade Runner is a great movie about replicants")
