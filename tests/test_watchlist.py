from nyc_movie_alert import watchlist


def test_add_and_list(tmp_path):
    path = tmp_path / "watchlist.json"
    assert watchlist.add_movie("Blade Runner", path=path)
    assert watchlist.list_movies(path=path)[0]["title"] == "Blade Runner"


def test_add_duplicate_is_case_insensitive(tmp_path):
    path = tmp_path / "watchlist.json"
    watchlist.add_movie("Blade Runner", path=path)
    assert not watchlist.add_movie("blade runner", path=path)
    assert len(watchlist.list_movies(path=path)) == 1


def test_remove(tmp_path):
    path = tmp_path / "watchlist.json"
    watchlist.add_movie("Blade Runner", path=path)
    assert watchlist.remove_movie("blade runner", path=path)
    assert watchlist.list_movies(path=path) == []


def test_remove_missing(tmp_path):
    path = tmp_path / "watchlist.json"
    assert not watchlist.remove_movie("Blade Runner", path=path)
