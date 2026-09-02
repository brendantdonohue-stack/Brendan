"""Turns raw HTML into visible text, and pulls out text near a match so a
human can sanity-check whether it's a real listing (a date, a showtime)
or just an incidental mention (nav link, unrelated blurb, SEO text)."""
import re

from bs4 import BeautifulSoup

from .matcher import normalize

# Common ways theater sites print dates/showtimes near a title.
_DATE_PATTERN = re.compile(
    r"\b("
    r"(mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(day)?s?\.?|"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2}|"
    r"\d{1,2}/\d{1,2}(/\d{2,4})?|"
    r"\d{1,2}:\d{2}\s*(am|pm)|"
    r"now\s+playing|"
    r"through\s+\w+\s+\d{1,2}"
    r")\b",
    re.IGNORECASE,
)


def visible_text(html: str) -> str:
    """Strips script/style/nav/header/footer tags and collapses whitespace,
    so matching and snippets reflect what a visitor actually sees, not
    every string embedded in scripts, meta tags, or site chrome."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def find_context_snippet(title: str, text: str, window: int = 100) -> str | None:
    """Returns a chunk of text surrounding the first occurrence of `title`
    in `text`, for a human to eyeball. Returns None if not found."""
    norm_title = normalize(title)
    if not norm_title:
        return None

    norm_text = normalize(text)
    idx = norm_text.find(norm_title)
    if idx == -1:
        return None

    # Map the normalized-text index back to an approximate position in the
    # original text by walking characters and counting only the ones that
    # survive normalization (letters/digits).
    orig_pos = 0
    seen = 0
    for i, ch in enumerate(text):
        if seen >= idx:
            orig_pos = i
            break
        if re.match(r"[a-zA-Z0-9]", ch):
            seen += 1
    else:
        orig_pos = len(text)

    start = max(0, orig_pos - window)
    end = min(len(text), orig_pos + len(title) + window)
    snippet = text[start:end].strip()
    return snippet


def has_nearby_date(snippet: str) -> bool:
    """Whether a context snippet contains something that looks like a date,
    weekday, or showtime -- a signal (not proof) that this is a real
    listing rather than an incidental title mention."""
    return bool(_DATE_PATTERN.search(snippet))
