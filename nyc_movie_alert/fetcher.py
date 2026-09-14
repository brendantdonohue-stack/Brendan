"""HTTP fetching for theater listing pages, with a headless-browser fallback
for pages that block plain requests or need JavaScript to render their
content (React/Next.js sites, Cloudflare-style bot walls)."""
from dataclasses import dataclass

import requests

from .extract import visible_text

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

# Below this many visible characters, a plain-HTTP fetch is treated as
# "probably a JS shell with no real content" and worth retrying with a
# headless browser instead.
MIN_USEFUL_VISIBLE_CHARS = 300


@dataclass
class FetchResult:
    html: str | None
    status_code: int | None
    error: str | None
    rendered: bool = False

    @property
    def ok(self) -> bool:
        return self.html is not None


def _fetch_plain(url: str, timeout: int) -> FetchResult:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    except requests.RequestException as exc:
        return FetchResult(html=None, status_code=None, error=f"{type(exc).__name__}: {exc}")

    if resp.status_code >= 400:
        return FetchResult(html=None, status_code=resp.status_code, error=f"HTTP {resp.status_code}")

    return FetchResult(html=resp.text, status_code=resp.status_code, error=None)


def _fetch_rendered(url: str, timeout: int) -> FetchResult:
    """Loads the page in headless Chromium and returns the rendered HTML.
    Handles both JS-only pages (nothing to see without a browser) and some
    bot walls that only check for JS execution rather than a real CAPTCHA."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return FetchResult(html=None, status_code=None, error="playwright not installed")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(user_agent=HEADERS["User-Agent"])
                page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
                # Give client-side rendering a moment to finish after the
                # initial HTML lands -- most React/Next.js sites paint
                # within a couple of seconds.
                page.wait_for_timeout(2500)
                html = page.content()
            finally:
                browser.close()
        return FetchResult(html=html, status_code=200, error=None, rendered=True)
    except Exception as exc:
        return FetchResult(html=None, status_code=None, error=f"{type(exc).__name__}: {exc}", rendered=True)


def fetch(url: str, timeout: int = 20) -> FetchResult:
    """Fetch a URL, falling back to a headless browser when the plain
    request fails outright or comes back with next to no visible content."""
    result = _fetch_plain(url, timeout)
    if result.ok and len(visible_text(result.html)) >= MIN_USEFUL_VISIBLE_CHARS:
        return result

    rendered = _fetch_rendered(url, timeout=max(timeout, 30))
    if rendered.ok:
        return rendered

    if result.ok:
        # Plain fetch worked but was too sparse, and rendering didn't
        # improve on it -- fall back to what we did get.
        return result

    return FetchResult(
        html=None,
        status_code=result.status_code,
        error=f"{result.error}; render fallback also failed: {rendered.error}",
        rendered=True,
    )


def fetch_html(url: str, timeout: int = 20) -> str | None:
    """Convenience wrapper for callers that only need the HTML or None."""
    return fetch(url, timeout=timeout).html
