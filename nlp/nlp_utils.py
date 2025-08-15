# nlp/nlp_utils.py
import json

def search_endpoint(spec: dict, query: str):
    """
    Simple keyword search in API spec
    """
    results = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if query.lower() in path.lower() or query.lower() in details.get("summary", "").lower():
                results.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", "")
                })
    return results