# Text helpers shared by the web app (app.py) and the MCP tools (mcp_server.py):
# keyword extraction, picking the clusters most relevant to a topic, and the
# 1-5 importance clamp.
import re

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for",
    "of", "with", "and", "or", "but", "not", "this", "that", "it", "be", "has",
    "had", "have", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "can", "from", "by", "as", "so", "if", "than", "then", "only", "just",
    "also", "very", "too", "more", "most", "some", "any", "all", "each", "every",
    "such", "into", "over", "after", "before", "between", "about", "like", "been",
    "being", "its", "my", "our", "your", "his", "her", "their", "what", "which",
    "who", "whom", "when", "where", "how", "why", "no", "yes", "up", "out", "new",
    "old", "first", "since", "one", "two", "three",
}


def clamp_importance(v):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return 3
    return 1 if n < 1 else 5 if n > 5 else n


def extract_doc_keywords(doc):
    text = doc["content"].lower()
    text = re.sub(r'\{\{[^}]*\}\}', '', text)
    text = re.sub(r'<!--[^>]*-->', '', text)
    freq = {}
    for w in re.findall(r'[a-z]{3,}', text):
        if w not in STOP_WORDS:
            freq[w] = freq.get(w, 0) + 1
    fname_stem = doc["filename"].replace(".md", "").lower()
    keywords = [fname_stem] + [w for w in re.split(r"[_/]", fname_stem) if len(w) >= 3]
    for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True):
        keywords.append(w)
        if len(keywords) >= 20:
            break
    for h in re.findall(r'##\s+(.+)', doc["content"]):
        for w in re.findall(r'[a-z]{3,}', h.lower()):
            if w not in STOP_WORDS and w not in keywords:
                keywords.append(w)
    return keywords


def select_files(topic, docs, max_files=3):
    """The docs most relevant to a topic (filename and keyword overlap), else core.md."""
    topic_lower = topic.lower()
    topic_words = set(re.findall(r'[a-z]{3,}', topic_lower)) - STOP_WORDS
    scored = []
    for doc in docs:
        if doc["filename"].startswith("_"):
            continue
        fname_stem = doc["filename"].replace(".md", "").lower()
        score = 5 if fname_stem in topic_lower else 0
        for w in re.split(r"[_/]", fname_stem):
            if len(w) >= 3 and w in topic_lower:
                score += 3
        score += len(topic_words & set(extract_doc_keywords(doc))) * 2
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return [d for _, d in scored[:max_files]]
    return [d for d in docs if d["filename"] == "core.md"]
