"""HTTP fetching for theater listing pages."""
from dataclasses import dataclass

import requests

# A full browser-like header set -- some theater sites (particularly ones
# behind Cloudflare/bot-detection, e.g. AMC/Regal) reject requests that look
# scripted, and a bare User-Agent alone isn't always enough to pass.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class FetchResult:
    html: str | None
    status_code: int | None
    error: str | None

    @property
    def ok(self) -> bool:
        return self.html is not None


def fetch(url: str, timeout: int = 20) -> FetchResult:
    """Fetch a URL, returning the HTML plus diagnostics on failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        return FetchResult(html=None, status_code=None, error=f"{type(exc).__name__}: {exc}")

    if resp.status_code >= 400:
        return FetchResult(html=None, status_code=resp.status_code, error=f"HTTP {resp.status_code}")

    return FetchResult(html=resp.text, status_code=resp.status_code, error=None)


def fetch_html(url: str, timeout: int = 20) -> str | None:
    """Convenience wrapper for callers that only need the HTML or None."""
    return fetch(url, timeout=timeout).html
