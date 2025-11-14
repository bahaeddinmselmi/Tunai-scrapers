"""Text extraction and processing utilities."""

import re
from re import Pattern

from bs4 import BeautifulSoup

# Precompiled regex patterns for better performance
ARABIC_PATTERN: Pattern = re.compile(r"[\u0600-\u06FF]{2,}")
ROMAN_TOKEN_PATTERN: Pattern = re.compile(r"[A-Za-z0-9]{3,}")
TUNISIAN_DIGIT_PATTERN: Pattern = re.compile(r"[2395678]")
SENTENCE_SPLIT_PATTERN: Pattern = re.compile(r"(?<=[.!؟?؛])\s+")
WHITESPACE_PATTERN: Pattern = re.compile(r"\s+")
FLASHCARD_PATTERN: Pattern = re.compile(
    r"Word of the day:\s*(.*?)\s+([\u0600-\u06FF].*?)\s+([A-Za-z0-9 '\-]+)"
)

# Frozen set for O(1) lookup
EN_STOP = frozenset(
    {
        "the",
        "and",
        "for",
        "are",
        "you",
        "your",
        "with",
        "this",
        "that",
        "have",
        "has",
        "from",
        "was",
        "were",
        "not",
        "but",
        "can",
        "all",
        "any",
        "our",
        "out",
        "about",
        "more",
        "will",
        "just",
        "over",
        "into",
        "how",
        "what",
        "when",
        "where",
        "who",
        "why",
        "use",
        "used",
        "using",
        "on",
        "in",
        "at",
        "by",
        "of",
        "to",
        "as",
    }
)

# Tunisian-specific patterns for detection
TUNISIAN_PATTERNS = (
    "barcha",
    "barsha",
    "toun",
    "touns",
    "tunsi",
    "3lech",
    "9a",
    "7keya",
    "9leb",
    "kh",
    "gh",
)


def extract_text(html: str) -> str:
    """Extract clean text from HTML.

    Args:
        html: HTML string to extract text from

    Returns:
        Cleaned text content
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg", "form", "iframe"]):
        tag.decompose()

    # Find main content container
    container = soup.find(["article", "main"]) or soup.body or soup

    # Extract text from relevant elements
    parts = []
    for el in container.find_all(["h1", "h2", "h3", "p", "li", "blockquote"], recursive=True):
        txt = el.get_text(" ", strip=True)
        if txt:
            parts.append(txt)

    # Join and normalize whitespace
    text = "\n".join(parts)
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def split_sentences(text: str) -> list[str]:
    """Split text into sentences.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    if not text:
        return []

    sentences = SENTENCE_SPLIT_PATTERN.split(text)
    return [s.strip() for s in sentences if s.strip()]


def _is_roman_tunisian_token(token: str) -> bool:
    """Check if token is likely romanized Tunisian.

    Args:
        token: Token to check

    Returns:
        True if token appears to be romanized Tunisian
    """
    if len(token) < 3 or token in EN_STOP or token.isdigit():
        return False

    # Check for Tunisian-specific digits (2,3,5,6,7,8,9 used in romanization)
    if TUNISIAN_DIGIT_PATTERN.search(token):
        return True

    # Check for common Tunisian patterns
    return any(pattern in token for pattern in TUNISIAN_PATTERNS)


def extract_tokens(text: str) -> tuple[list[str], list[str]]:
    """Extract Arabic and romanized Tunisian tokens.

    Args:
        text: Text to extract tokens from

    Returns:
        Tuple of (arabic_tokens, romanized_tokens)
    """
    if not text:
        return [], []

    # Extract Arabic tokens
    arabic = ARABIC_PATTERN.findall(text)

    # Extract and filter romanized tokens
    roman_all = ROMAN_TOKEN_PATTERN.findall(text.lower())
    romanized = [t for t in roman_all if _is_roman_tunisian_token(t)]

    return arabic, romanized


def build_vocab(freq: dict[str, int], samples: dict[str, dict]) -> list[dict]:
    """Build vocabulary JSON structure.

    Args:
        freq: Word frequency dictionary
        samples: Word samples dictionary with script and examples

    Returns:
        List of vocabulary entries sorted by frequency
    """
    vocab = []
    for word, count in sorted(freq.items(), key=lambda x: x[1], reverse=True):
        sample = samples.get(word, {})
        vocab.append(
            {
                "word": word,
                "count": count,
                "script": sample.get("script"),
                "examples": sample.get("examples", []),
            }
        )
    return vocab


def extract_cards(text: str, url: str) -> list[dict[str, str]]:
    """Extract flashcards (English-Arabic-Romanized triplets) from text.

    Args:
        text: Text to extract cards from
        url: Source URL for the cards

    Returns:
        List of dicts with keys: source, url, english, arabic, roman
    """
    cards = []
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Try to find triplets: English, Arabic, Romanized
    cards.extend(_extract_card_triplets(lines, url))

    # Also try explicit "Word of the day:" patterns
    if match := FLASHCARD_PATTERN.search(text):
        en, ar, ro = match.groups()
        if TUNISIAN_DIGIT_PATTERN.search(ro):
            cards.append(_create_card_dict(url, en.strip(), ar.strip(), ro.strip()))

    return cards


def _extract_card_triplets(lines: list[str], url: str) -> list[dict[str, str]]:
    """Extract card triplets from consecutive lines.

    Args:
        lines: List of text lines
        url: Source URL

    Returns:
        List of card dictionaries
    """
    cards = []

    for i in range(len(lines) - 2):
        en, ar, ro = lines[i], lines[i + 1], lines[i + 2]

        if _is_valid_card_triplet(en, ar, ro):
            cards.append(_create_card_dict(url, en, ar, ro))

    return cards


def _is_valid_card_triplet(en: str, ar: str, ro: str) -> bool:
    """Check if three lines form a valid flashcard triplet.

    Args:
        en: Potential English text
        ar: Potential Arabic text
        ro: Potential romanized text

    Returns:
        True if this is a valid card triplet
    """
    return (
        len(en) >= 5
        and len(ar) >= 2
        and ARABIC_PATTERN.search(ar) is not None
        and re.fullmatch(r"[A-Za-z0-9 '\-]+", ro) is not None
        and TUNISIAN_DIGIT_PATTERN.search(ro) is not None
    )


def _create_card_dict(url: str, english: str, arabic: str, roman: str) -> dict[str, str]:
    """Create a card dictionary.

    Args:
        url: Source URL
        english: English text
        arabic: Arabic text
        roman: Romanized text

    Returns:
        Card dictionary
    """
    return {
        "source": "derja.ninja",
        "url": url,
        "english": english,
        "arabic": arabic,
        "roman": roman,
    }
