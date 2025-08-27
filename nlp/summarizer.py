import re
from typing import List, Dict

# --- tiny, dependency-light fallbacks ---
STOPWORDS = set("""
a an and are as at be by for from has have how i if in into is it its of on or that the their them they this to was were what when where which who will with you your
""".split())

def _safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _first_sentence(text: str) -> str:
    if not text:
        return ""
    m = re.split(r"(?<=[.!?])\s+", text.strip())
    return (m[0] if m else text).strip()

# -------------------------
# Public helpers
# -------------------------
def summarize_text(text: str, max_length: int = 220) -> str:
    """Very light summary: take first sentence or truncate."""
    t = (text or "").strip()
    if not t:
        return "No description available."
    s = _first_sentence(t)
    if len(s) < 30:
        s = t[:max_length].rstrip()
    return s

def extract_keywords(text: str, top_k: int = 6) -> List[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", (text or "").lower())
    freq = {}
    for w in words:
        if w in STOPWORDS or len(w) < 3:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in ranked[:top_k]]

def _collect_all_descriptions(api_spec: Dict) -> str:
    chunks = []
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            chunks.append(details.get("description") or details.get("summary") or "")
    return " ".join(chunks).strip()

def _build_endpoints_table(api_spec: Dict) -> str:
    rows = ["### Endpoints:", "| Endpoint | Method | Purpose |", "|----------|--------|---------|"]
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            desc = details.get("description") or details.get("summary") or "—"
            rows.append(f"| `{path}` | `{method.upper()}` | {desc} |")
    return "\n".join(rows)

def _build_params_table(api_spec: Dict) -> str:
    rows = ["### Parameters:", "| Endpoint | Parameter | In | Type | Required | Description |", "|----------|-----------|----|------|----------|-------------|"]
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            # path-level params
            for param in (details.get("parameters") or []):
                name = param.get("name","")
                loc = param.get("in","")
                typ = _safe_get(param, "schema", "type", default="—")
                req = "✅" if param.get("required") else "❌"
                desc = param.get("description","—")
                rows.append(f"| `{path}` | `{name}` | `{loc}` | `{typ}` | {req} | {desc} |")

            # request body (JSON schema) - flatten top-level props if present
            body = _safe_get(details, "requestBody", "content")
            if isinstance(body, dict):
                for _, v in body.items():
                    schema = _safe_get(v, "schema", default={})
                    props = _safe_get(schema, "properties", default={})
                    required_list = set(schema.get("required") or [])
                    for pname, pdef in props.items():
                        ptype = pdef.get("type") or pdef.get("format") or "object"
                        preq = "✅" if pname in required_list else "❌"
                        pdesc = pdef.get("description","—")
                        rows.append(f"| `{path}` | `{pname}` | `body` | `{ptype}` | {preq} | {pdesc} |")
    return "\n".join(rows)

def _build_auth_section(api_spec: Dict) -> str:
    sec_schemes = _safe_get(api_spec, "components", "securitySchemes", default={}) or {}
    lines = ["## 🔐 Authentication"]
    if not sec_schemes and not api_spec.get("security"):
        lines.append("No global auth defined. Endpoints may be public or define their own security.")
        return "\n".join(lines)

    for name, scheme in sec_schemes.items():
        typ = scheme.get("type", "—")
        scheme_name = scheme.get("scheme", "")
        bearer_fmt = scheme.get("bearerFormat","")
        flow = (scheme.get("flows") or {}).keys()
        lines.append(f"- **{name}** — type: `{typ}`" + (f", scheme: `{scheme_name}`" if scheme_name else "") + (f", bearerFormat: `{bearer_fmt}`" if bearer_fmt else ""))
        if flow:
            lines.append(f"  - OAuth2 flows: {', '.join(flow)}")
    if api_spec.get("security"):
        lines.append("- Global security requirement present (auth needed by default).")
    return "\n".join(lines)

def _generate_flow_diagram(api_spec: Dict) -> str:
    """
    Create a Mermaid diagram based on the endpoints in the API spec.
    Works for any uploaded OpenAPI (users, movies, hospitals, etc.).
    """
    paths = api_spec.get("paths") or {}
    flow = ["```mermaid", "flowchart LR", "U[👤 Client]"]

    # --- Authentication flows ---
    if any("signup" in p or "register" in p for p in paths):
        flow += ["U --> S[POST /signup]", "S --> SOK[✅ Account Created]"]

    if any("login" in p or ("auth" in p and "token" not in p) for p in paths):
        flow += ["U --> L[POST /login]", "L --> T[🔑 JWT/Session Token]"]

    if any("token" in p for p in paths):
        flow += ["U --> TK[POST /token]", "TK --> T[🔑 Access Token]"]

    # --- Detect generic resource collections ---
    for path, methods in paths.items():
        parts = [seg for seg in path.strip("/").split("/") if seg and "{" not in seg]
        if not parts:
            continue
        resource = parts[0]  # first segment as resource name (e.g. "users", "orders")

        for method in (methods or {}):
            m = method.upper()
            if m == "GET" and "{id}" in path:
                flow += [f"T --> G_{resource}[GET /{resource}/{{id}}]", f"G_{resource} --> V_{resource}[📄 {resource.title()} Detail]"]
            elif m == "GET":
                flow += [f"T --> L_{resource}[GET /{resource}]", f"L_{resource} --> LST_{resource}[📄 {resource.title()} List]"]
            elif m == "POST":
                flow += [f"T --> C_{resource}[POST /{resource}]", f"C_{resource} --> NEW_{resource}[➕ New {resource.title()}]"]
            elif m == "PUT":
                flow += [f"T --> U_{resource}[PUT /{resource}/{{id}}]", f"U_{resource} --> UPD_{resource}[✏️ Update {resource.title()}]"]
            elif m == "DELETE":
                flow += [f"T --> D_{resource}[DELETE /{resource}/{{id}}]", f"D_{resource} --> DEL_{resource}[❌ Delete {resource.title()}]"]

    # --- Fallback generic CRUD if nothing detected ---
    all_methods = {m.upper() for p in paths for m in (paths[p] or {})}
    if not any(" --> " in step for step in flow if "GET" in step):
        if "GET" in all_methods:
            flow += ["T --> R[GET read resource]"]
    if "POST" in all_methods:
        flow += ["T --> C[POST create resource]"]
    if "PUT" in all_methods:
        flow += ["T --> U2[PUT update resource]"]
    if "DELETE" in all_methods:
        flow += ["T --> D[DELETE remove resource]"]

    flow.append("```")
    return "\n".join(flow)

def format_api_summary(api_spec: Dict) -> str:
    """
    Return a layman-friendly Markdown summary with:
    - Overview
    - Endpoints table
    - Parameters table
    - Authentication section
    - Mermaid flow diagram
    """
    info_title = _safe_get(api_spec, "info", "title", default="API")
    info_ver = _safe_get(api_spec, "info", "version", default="N/A")
    combined_desc = _collect_all_descriptions(api_spec)
    overview = summarize_text(combined_desc)

    endpoints_table = _build_endpoints_table(api_spec)
    params_table = _build_params_table(api_spec)
    auth_section = _build_auth_section(api_spec)
    flow = _generate_flow_diagram(api_spec)

    md = [
        f"# 📄 {info_title} — Summary (v{info_ver})",
        "## 📝 Overview",
        overview or "No descriptions found in the spec.",
        "",
        endpoints_table,
        "",
        params_table,
        "",
        auth_section,
        "",
        "## 🔄 Flow Diagram",
        flow,
    ]
    return "\n".join(md)
