from collections import Counter
import re

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def summarize_text(text: str, max_sentences=2) -> str:
    sentences = text.split(".")
    words = clean_text(text).split()
    word_freq = Counter(words)
    
    ranking = []
    for sent in sentences:
        score = sum(word_freq.get(w,0) for w in clean_text(sent).split())
        ranking.append((score, sent))
    ranking.sort(reverse=True)
    
    summary = ". ".join([sent for score, sent in ranking[:max_sentences]])
    return summary.strip() + "."

def extract_keywords(text: str, top_n=5):
    words = clean_text(text).split()
    freq = Counter(words)
    return [word for word, count in freq.most_common(top_n)]