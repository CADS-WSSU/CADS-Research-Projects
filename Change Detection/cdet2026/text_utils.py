"""Shared lightweight text helpers used by both the lexical retriever (BM25) and,
later, the novelty term-set signal (M3)."""
import re

_WORD = re.compile(r"[a-z0-9]+")

# Minimal English stopword list — enough to keep BM25/novelty term sets content-bearing
# without pulling in a heavy dependency.
STOPWORDS = frozenset(
    """a an and are as at be by for from has have he in is it its of on that the to was
    were will with this these those they their them i you we our your he she his her
    not no but or if then than so such can could would should may might do does did
    about into over after before between during while which who whom whose what when
    where why how all any both each few more most other some only own same too very
    s t just don now""".split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens (for BM25; no stopword removal — BM25 idf handles it)."""
    return _WORD.findall(text.lower())


def content_terms(text: str) -> set[str]:
    """Stopword-filtered token set, length>2 — used for novelty 'new terms' signal."""
    return {t for t in tokenize(text) if len(t) > 2 and t not in STOPWORDS}
