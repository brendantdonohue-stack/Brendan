"""HTTP fetching for theater listing pages."""
import requests

USER_AGENT = (
    "Mozilla/5.0 (compatible; nyc-movie-alert/1.0; "
    "personal watchlist checker; +https://github.com/)"
)


def fetch_html(url: str, timeout: int = 20) -> str | None:
    """Fetch a URL and return its HTML text, or None on failure."""
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException:
        return None
