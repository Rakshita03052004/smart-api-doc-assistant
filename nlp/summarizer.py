import re
from typing import List, Dict, Optional

# --- tiny, dependency-light fallbacks ---
STOPWORDS = set("""
a an and are as at be by for from has have how i if in into is it its of on or that the their them they this to was were what when where which who will with you your
""".split())

def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _first_sentence(text: str) -> str:
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return sentences[0].strip() if sentences else text.strip()

# -------------------------
# Public helpers
# -------------------------
def summarize_text(text: str, max_length: int = 220) -> str:
    """Return first sentence or truncate text if too short."""
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
    rows = [
        "### Endpoints:",
        "| Endpoint | Method | Purpose |",
        "|----------|--------|---------|"
    ]
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            desc = details.get("description") or details.get("summary") or "—"
            rows.append(f"| `{path}` | `{method.upper()}` | {desc} |")
    return "\n".join(rows)

def _build_params_table(api_spec: Dict) -> str:
    rows = [
        "### Parameters:",
        "| Endpoint | Parameter | In | Type | Required | Description |",
        "|----------|-----------|----|------|----------|-------------|"
    ]
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            for param in (details.get("parameters") or []):
                name = param.get("name", "")
                loc = param.get("in", "")
                typ = _safe_get(param, "schema", "type", default="—")
                req = "✅" if param.get("required") else "❌"
                desc = param.get("description", "—")
                rows.append(f"| `{path}` | `{name}` | `{loc}` | `{typ}` | {req} | {desc} |")

            body = _safe_get(details, "requestBody", "content")
            if isinstance(body, dict):
                for _, v in body.items():
                    schema = _safe_get(v, "schema", default={})
                    props = _safe_get(schema, "properties", default={})
                    required_list = set(schema.get("required") or [])
                    for pname, pdef in props.items():
                        ptype = pdef.get("type") or pdef.get("format") or "object"
                        preq = "✅" if pname in required_list else "❌"
                        pdesc = pdef.get("description", "—")
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
        bearer_fmt = scheme.get("bearerFormat", "")
        flow = (scheme.get("flows") or {}).keys()
        lines.append(f"- **{name}** — type: `{typ}`" +
                     (f", scheme: `{scheme_name}`" if scheme_name else "") +
                     (f", bearerFormat: `{bearer_fmt}`" if bearer_fmt else ""))
        if flow:
            lines.append(f"  - OAuth2 flows: {', '.join(flow)}")
    if api_spec.get("security"):
        lines.append("- Global security requirement present (auth needed by default).")
    return "\n".join(lines)

def _generate_flow_diagram(api_spec: Dict) -> str:
    """Generate Mermaid flow diagram for common endpoints."""
    paths = set((api_spec.get("paths") or {}).keys())
    flow = ["```mermaid", "flowchart LR", "U[👤 Client]"]

    if any(p for p in paths if "signup" in p or "register" in p):
        flow += ["U --> S[POST /signup]", "S --> SOK[✅ Account Created]"]
    if any(p for p in paths if "login" in p or "auth" in p and "token" not in p):
        flow += ["U --> L[POST /login]", "L --> T[🔑 JWT/Session Token]"]
    if any("token" in p for p in paths):
        flow += ["U --> TK[POST /token]", "TK --> T[🔑 Access Token]"]

    # CRUD patterns
    for verb, node, label in [("POST", "C", "create resource"), ("GET", "R", "read resource"),
                              ("PUT", "U2", "update resource"), ("DELETE", "D", "remove resource")]:
        if any(verb in (m.upper() for m in (api_spec["paths"][p] or {}).keys()) for p in api_spec.get("paths", {})):
            flow += [f"T --> {node}[{verb} {label}]"]

    flow.append("```")
    return "\n".join(flow)

def format_api_summary(api_spec: Dict) -> str:
    """Generate Markdown summary of the API."""
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