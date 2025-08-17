# nlp/nlp_utils.py
from sentence_transformers import SentenceTransformer, util

# Load the model once globally
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def search_endpoint(spec: dict, query: str):
    """
    Semantic search in API spec using Sentence-BERT embeddings
    """
    results = []
    paths = spec.get("paths", {})
    query_emb = model.encode(query, convert_to_tensor=True)

    for path, methods in paths.items():
        for method, details in methods.items():
            desc = details.get("summary", "") + " " + details.get("description", "")
            if desc:
                emb = model.encode(desc, convert_to_tensor=True)
                score = util.cos_sim(query_emb, emb).item()
                if score > 0.5:  # threshold for relevance
                    results.append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "score": score
                    })
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results