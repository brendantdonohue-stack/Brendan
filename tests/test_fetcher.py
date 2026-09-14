import unittest.mock as mock

from nyc_movie_alert import fetcher


def test_plain_fetch_with_enough_content_skips_render():
    plain = fetcher.FetchResult(html="<p>" + "x" * 400 + "</p>", status_code=200, error=None)
    with mock.patch("nyc_movie_alert.fetcher._fetch_plain", return_value=plain), mock.patch(
        "nyc_movie_alert.fetcher._fetch_rendered"
    ) as rendered:
        result = fetcher.fetch("https://example.com")
    assert result.ok
    assert not result.rendered
    assert not rendered.called


def test_failed_plain_fetch_falls_back_to_render():
    plain = fetcher.FetchResult(html=None, status_code=403, error="HTTP 403")
    rendered_result = fetcher.FetchResult(html="<p>rendered</p>", status_code=200, error=None, rendered=True)
    with mock.patch("nyc_movie_alert.fetcher._fetch_plain", return_value=plain), mock.patch(
        "nyc_movie_alert.fetcher._fetch_rendered", return_value=rendered_result
    ) as rendered:
        result = fetcher.fetch("https://example.com")
    assert result.ok
    assert result.rendered
    assert rendered.called


def test_near_empty_plain_fetch_falls_back_to_render():
    plain = fetcher.FetchResult(html="<p>hi</p>", status_code=200, error=None)
    rendered_result = fetcher.FetchResult(html="<p>" + "y" * 400 + "</p>", status_code=200, error=None, rendered=True)
    with mock.patch("nyc_movie_alert.fetcher._fetch_plain", return_value=plain), mock.patch(
        "nyc_movie_alert.fetcher._fetch_rendered", return_value=rendered_result
    ) as rendered:
        result = fetcher.fetch("https://example.com")
    assert result.ok
    assert result.rendered
    assert rendered.called


def test_both_fetch_strategies_fail_combines_errors():
    plain = fetcher.FetchResult(html=None, status_code=403, error="HTTP 403")
    rendered_result = fetcher.FetchResult(html=None, status_code=None, error="TimeoutError: boom", rendered=True)
    with mock.patch("nyc_movie_alert.fetcher._fetch_plain", return_value=plain), mock.patch(
        "nyc_movie_alert.fetcher._fetch_rendered", return_value=rendered_result
    ):
        result = fetcher.fetch("https://example.com")
    assert not result.ok
    assert "HTTP 403" in result.error
    assert "TimeoutError: boom" in result.error
