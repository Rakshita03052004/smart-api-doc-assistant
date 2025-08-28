"""
search.py

Module to implement search logic on the API specification data.
"""

from typing import List, Dict

def search_api_spec(api_spec: Dict, query: str) -> List[Dict]:
    """
    Search API specification for endpoints matching the query.

    Args:
        api_spec (Dict): Loaded API specification dictionary.
        query (str): Search query string.

    Returns:
        List[Dict]: List of matching endpoints with basic details.
    """
    if not query:
        return []

    query_lower = query.lower()
    results = []

    # Assuming api_spec["paths"] contains the paths dictionary
    paths = api_spec.get("paths", {})

    for path, methods in paths.items():
        for method, details in methods.items():
            summary = details.get("summary", "").lower()
            description = details.get("description", "").lower()
            tags = [tag.lower() for tag in details.get("tags", [])]

            if (
                query_lower in path.lower()
                or query_lower in summary
                or query_lower in description
                or any(query_lower in tag for tag in tags)
            ):
                results.append(
                    {
                        "endpoint": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                    }
                )

    return results
def build_smart_description(path: str, method: str, details: dict) -> str:
    # 1. If description exists, use it
    if details.get("description"):
        return details["description"]

    # 2. If summary exists, use it
    if details.get("summary"):
        return details["summary"]

    # 3. Try to build from schema
    desc_parts = []

    # Parameters
    params = details.get("parameters", [])
    if params:
        param_names = [p.get("name", "") for p in params]
        desc_parts.append(f"parameters: {', '.join(param_names)}")

    # Request body
    if "requestBody" in details:
        content = details["requestBody"].get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            if "properties" in schema:
                fields = list(schema["properties"].keys())
                desc_parts.append(f"request fields: {', '.join(fields)}")

    # Responses
    responses = details.get("responses", {})
    if "200" in responses:
        resp_content = responses["200"].get("content", {})
        if "application/json" in resp_content:
            schema = resp_content["application/json"].get("schema", {})
            if "properties" in schema:
                fields = list(schema["properties"].keys())
                desc_parts.append(f"returns: {', '.join(fields)}")

    # 4. Final fallback
    if desc_parts:
        return f"{method.upper()} {path} → " + "; ".join(desc_parts)

    return f"{method.upper()} {path} → No description available"
