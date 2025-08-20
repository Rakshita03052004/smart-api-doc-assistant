from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

# Load summarizer once
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

def summarize_text(text: str, max_length: int = 150, min_length: int = 40) -> str:
    """Summarize given text (API documentation, descriptions, etc.) into plain English."""
    if not text.strip():
        return "No description available."
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]["summary_text"]

def extract_keywords(text: str, top_k: int = 5) -> list[str]:
    """Extract keywords from text using TF-IDF."""
    if not text.strip():
        return []
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform([text])
    scores = zip(vectorizer.get_feature_names_out(), X.toarray()[0])
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    keywords = [word for word, score in sorted_scores[:top_k]]
    return keywords

def format_api_summary(api_spec: dict) -> str:
    """
    Return a human-friendly English summary of API spec with tables.
    """
    # Collect all descriptions & summaries
    combined_desc = " ".join(
        details.get("description") or details.get("summary") or ""
        for path in api_spec.get("paths", {}).values()
        for details in path.values()
    )

    summary_text = summarize_text(combined_desc)

    # Build Endpoints table
    endpoints_table = "### Endpoints:\n| Endpoint | Method | Purpose |\n|----------|--------|---------|\n"
    for path, methods in api_spec.get("paths", {}).items():
        for method, details in methods.items():
            desc = details.get("description") or details.get("summary") or "No description available."
            endpoints_table += f"| {path} | {method.upper()} | {desc} |\n"

    # Build Parameters table
    params_table = "\n### Parameters:\n| Endpoint | Parameter | Type | Required | Description |\n|----------|-----------|------|----------|-------------|\n"
    for path, methods in api_spec.get("paths", {}).items():
        for method, details in methods.items():
            for param in details.get("parameters", []):
                name = param.get("name", "")
                typ = param.get("schema", {}).get("type", "")
                req = "✅" if param.get("required", False) else "❌"
                desc = param.get("description", "No description available.")
                params_table += f"| {path} | {name} | {typ} | {req} | {desc} |\n"

    # Build keywords
    keywords = extract_keywords(combined_desc)
    keywords_text = "\n### Keywords:\n" + (", ".join(keywords) if keywords else "No keywords extracted") + "\n"

    return f"# 📄 API Documentation Summary\n\n{summary_text}\n\n{endpoints_table}\n{params_table}\n{keywords_text}"

def format_summary(summary: str) -> str:
    return f"""# 📄 API Documentation Summary  

## 🔐 Authentication
{summary.strip()}

---

## 📝 Parameters
| Endpoint | Parameter | Type | Required | Description |
|----------|-----------|------|----------|-------------|
| `/login` | `username` | string | ✅ | User’s login name |
| `/login` | `password` | string | ✅ | User’s password |
"""