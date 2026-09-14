"""Title normalization and matching against fetched page content."""
import re


def normalize(title: str) -> str:
    """Lowercase and strip everything but letters/digits, so punctuation and
    whitespace differences between sources don't cause a missed match."""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def find_match(title: str, page_text: str) -> bool:
    """Return True if the normalized title appears anywhere in the normalized page text."""
    norm_title = normalize(title)
    if not norm_title:
        return False
    return norm_title in normalize(page_text)


def find_link_for_title(title: str, html: str) -> str | None:
    """Best-effort: find an <a href="..."> whose link text contains the title,
    to include a direct link in the alert. Returns None if not found."""
    norm_title = normalize(title)
    for match in re.finditer(
        r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL
    ):
        href, link_text = match.group(1), match.group(2)
        link_text = re.sub(r"<[^>]+>", " ", link_text)
        if norm_title and norm_title in normalize(link_text):
            return href
    return None
