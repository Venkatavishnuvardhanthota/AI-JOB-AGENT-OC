import logging
import re
from collections import Counter

from app.schemas.matching import KeywordScore

logger = logging.getLogger(__name__)

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "dare", "ought", "used", "about", "into", "over", "after", "before",
    "between", "under", "above", "below", "this", "that", "these", "those",
    "it", "its", "we", "our", "you", "your", "they", "their", "he", "she",
    "his", "her", "him", "i", "my", "me", "all", "each", "every", "both",
    "no", "nor", "not", "only", "same", "so", "than", "too", "very", "just",
    "also", "more", "most", "some", "any", "such", "which", "what", "who",
    "whom", "where", "when", "why", "how", "if", "then", "else", "other",
    "another", "one", "two", "many", "much", "few", "several", "own",
    "new", "old", "good", "bad", "high", "low", "long", "short", "big",
    "small", "large", "little", "first", "last", "next", "previous",
    "while", "during", "through", "throughout", "via", "per", "up", "down",
    "out", "off", "well", "back", "here", "there", "please", "must",
}


class KeywordExtractor:
    MIN_WORD_LENGTH = 3
    MAX_KEYWORDS = 30

    def extract(self, text: str) -> list[str]:
        if not text:
            return []
        lower = text.lower()
        tokens = re.findall(r'[a-z][a-z+#.]+', lower)
        phrases = []
        for t in tokens:
            t = t.strip().strip(",:;.!?()[]{}")
            if len(t) < self.MIN_WORD_LENGTH:
                continue
            if t in STOPWORDS:
                continue
            if t.isdigit():
                continue
            phrases.append(t)
        counter = Counter(phrases)
        sorted_phrases = [p for p, _ in counter.most_common(self.MAX_KEYWORDS)]
        return sorted_phrases

    def compute_score(
        self, user_keywords: list[str], job_keywords: list[str]
    ) -> KeywordScore:
        user_set = {k.lower().strip() for k in user_keywords}
        job_set = {k.lower().strip() for k in job_keywords}
        matched = sorted(job_set & user_set)
        score = len(matched) / max(len(job_set), 1)
        return KeywordScore(
            extracted=sorted(job_set),
            matched=[m.capitalize() for m in matched],
            total=len(job_set),
            score=round(score, 4),
        )
