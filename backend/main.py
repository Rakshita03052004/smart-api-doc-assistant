# backend/main.py
from __future__ import annotations
import os
import json
import yaml
import re
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# -------------- App setup --------------
app = FastAPI(title="Smart API Doc Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cached normalized spec
API_SPEC: Dict[str, Any] = {}

# ----------------- Normalizer -----------------
def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _normalize_openapi(spec: dict) -> dict:
    """
    Convert OpenAPI/Swagger to normalized format:
    {
      "info": {...},
      "paths": {
         "/path": { "get": {"summary": "...", "description": "...", "parameters": [...], "responses": {...}}, ...}
      }
    }
    """
    info = spec.get("info", {}) or {}
    paths = spec.get("paths", {}) or {}
    return {"info": info, "paths": paths}

def _normalize_postman(spec: dict) -> dict:
    """
    Convert Postman collection to normalized paths.
    Postman items may be nested; each item with 'request' contains method and url.
    """
    info = {"title": _safe_get(spec, "info", "name", default="Postman Collection")}
    paths = {}
    items = spec.get("item", []) or []
    def _walk(items_list):
        for it in items_list:
            if "item" in it:
                _walk(it["item"])
            else:
                req = it.get("request")
                if not req:
                    continue
                method = (req.get("method") or "GET").lower()
                url = req.get("url") or req.get("raw") or {}
                # Postman url can be string or object
                if isinstance(url, dict):
                    path = url.get("path")
                    if isinstance(path, list):
                        path = "/" + "/".join(path)
                else:
                    path = url if isinstance(url, str) else "/"
                if not path:
                    path = "/"
                if path not in paths:
                    paths[path] = {}
                paths[path][method] = {
                    "summary": it.get("name") or "",
                    "description": _safe_get(it, "request", "description", default=""),
                    "parameters": [] ,
                    "responses": {}
                }
    _walk(items)
    return {"info": info, "paths": paths}

def _normalize_custom_endpoints(spec: dict) -> dict:
    """
    Convert a simple custom schema that has top-level 'endpoints': [ {path, method, ...}, ... ]
    Example (your Library JSON): endpoints: [ {path:"/books", method:"GET", description:"..."}, ...]
    """
    info = spec.get("info", {}) or {}
    # try alternate top-level meta
    if not info and "name" in spec:
        info = {"title": spec.get("name"), "version": spec.get("version")}
    paths = {}
    for e in spec.get("endpoints", []) or []:
        path = e.get("path") or e.get("endpoint") or "/"
        method = (e.get("method") or "GET").lower()
        summary = e.get("name") or e.get("summary") or ""
        description = e.get("description") or ""
        # parameters: see queryParams, pathParams, body keys
        params = []
        if e.get("queryParams"):
            for k, t in (e.get("queryParams") or {}).items():
                params.append({"name": k, "in": "query", "schema": {"type": str(t)}, "required": False, "description": ""})
        if e.get("pathParams"):
            for k, t in (e.get("pathParams") or {}).items():
                params.append({"name": k, "in": "path", "schema": {"type": str(t)}, "required": True, "description": ""})
        # handle body object if present (flatten top-level)
        requestBody = {}
        if e.get("body"):
            # create a simple JSON schema
            props = {}
            required = []
            for k, v in (e.get("body") or {}).items():
                props[k] = {"type": "string", "description": ""}
            requestBody = {"content": {"application/json": {"schema": {"type": "object", "properties": props, "required": required}}}}
        # responses - best-effort
        responses = {}
        if e.get("response"):
            responses["200"] = {"description": "Response example", "content": {"application/json": {"example": e.get("response")}}}
        if path not in paths:
            paths[path] = {}
        paths[path][method] = {
            "summary": summary,
            "description": description,
            "parameters": params,
            "requestBody": requestBody,
            "responses": responses
        }
    return {"info": info, "paths": paths}

def _normalize_minimal(spec: dict) -> dict:
    """Last-resort normalization: treat top-level keys that look like endpoints"""
    info = spec.get("info", {}) or {"title": spec.get("title") or "API"}
    paths = {}
    # Try to find any keys that look like "/something"
    for k, v in spec.items():
        if isinstance(k, str) and k.startswith("/"):
            # assume v is a dict of methods
            paths[k] = {}
            if isinstance(v, dict):
                for m, d in v.items():
                    paths[k][m.lower()] = {"summary": _safe_get(d, "summary", default=""), "description": _safe_get(d, "description", default=""), "parameters": d.get("parameters", []), "responses": d.get("responses", {})}
    return {"info": info, "paths": paths}

def normalize_spec(raw_spec: dict) -> dict:
    """
    Detect format and return normalized dict: {"info":..., "paths":{...}}
    The 'paths' structure matches OpenAPI-like shape for easier downstream processing.
    """
    # OpenAPI/Swagger (v2/v3)
    if "paths" in raw_spec and isinstance(raw_spec["paths"], dict):
        return _normalize_openapi(raw_spec)
    # Postman collection (has 'item' array)
    if "item" in raw_spec and isinstance(raw_spec["item"], list):
        return _normalize_postman(raw_spec)
    # Custom simple 'endpoints' schema (your Library example)
    if "endpoints" in raw_spec and isinstance(raw_spec["endpoints"], list):
        return _normalize_custom_endpoints(raw_spec)
    # sometimes people paste OpenAPI under 'swagger' or 'openapi' keys but paths missing -> still attempt
    if "swagger" in raw_spec or "openapi" in raw_spec:
        return _normalize_openapi(raw_spec)
    # fallback: try minimal normalization scanning for path-like top-level keys
    return _normalize_minimal(raw_spec)

def render_mermaid(mermaid_code: str) -> str:
    """
    Convert Mermaid code to SVG using mermaid-cli (mmdc).
    Requires: npm install -g @mermaid-js/mermaid-cli
    """
    import tempfile, subprocess, os

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".mmd") as f:
        f.write(mermaid_code)
        f.flush()
        input_path = f.name
    output_path = input_path + ".svg"
    try:
        subprocess.run(
            ["mmdc", "-i", input_path, "-o", output_path],
            check=True
        )
        with open(output_path, "r", encoding="utf-8") as svgf:
            return svgf.read()
    finally:
        # cleanup
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# ----------------- Formatting / Summary helpers -----------------
STOPWORDS = set("""
a an and are as at be by for from has have how i if in into is it its of on or that the their them they this to was were what when where which who will with you your
""".split())

def _first_sentence(text: str) -> str:
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return parts[0].strip() if parts else text.strip()

def summarize_text(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "No description available."
    s = _first_sentence(t)
    if len(s) < 30:
        return t[:220].rstrip()
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

# Build endpoints / params / auth / flow as Markdown
def _collect_all_descriptions(api_spec: Dict) -> str:
    chunks = []
    info_desc = _safe_get(api_spec, "info", "description", default="")
    if info_desc:
        chunks.append(str(info_desc))
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            chunks.append(str(details.get("description") or details.get("summary") or ""))
    return " ".join([c for c in chunks if c]).strip()

def _build_endpoints_table(api_spec: Dict) -> str:
    rows = ["### Endpoints:", "| Endpoint | Method | Purpose |", "|----------|--------|---------|"]
    paths = api_spec.get("paths") or {}
    if not paths:
        rows.append("| — | — | No paths found in spec. |")
        return "\n".join(rows)
    for path, methods in paths.items():
        for method, details in (methods or {}).items():
            desc = details.get("description") or details.get("summary") or "—"
            rows.append(f"| `{path}` | `{method.upper()}` | {desc} |")
    return "\n".join(rows)

def _build_params_table(api_spec: Dict) -> str:
    rows = ["### Parameters:", "| Endpoint | Parameter | In | Type | Required | Description |", "|----------|-----------|----|------|----------|-------------|"]
    any_row = False
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            # parameters array
            for param in (details.get("parameters") or []):
                name = param.get("name", "")
                loc = param.get("in", "")
                typ = _safe_get(param, "schema", "type", default="—")
                req = "✅" if param.get("required") else "❌"
                desc = param.get("description", "—")
                rows.append(f"| `{path}` | `{name}` | `{loc}` | `{typ}` | {req} | {desc} |")
                any_row = True
            # requestBody -> content -> schema -> properties
            body = _safe_get(details, "requestBody", "content", default={}) or {}
            if isinstance(body, dict):
                for _, v in body.items():
                    schema = _safe_get(v, "schema", default={}) or {}
                    props = schema.get("properties") or {}
                    required_list = set(schema.get("required") or [])
                    for pname, pdef in (props or {}).items():
                        ptype = pdef.get("type") or pdef.get("format") or "object"
                        preq = "✅" if pname in required_list else "❌"
                        pdesc = pdef.get("description", "—")
                        rows.append(f"| `{path}` | `{pname}` | `body` | `{ptype}` | {preq} | {pdesc} |")
                        any_row = True
    if not any_row:
        rows.append("| — | — | — | — | — | No parameters discovered. |")
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
        flows = (scheme.get("flows") or {}).keys()
        extra = []
        if scheme_name:
            extra.append(f"scheme: `{scheme_name}`")
        if bearer_fmt:
            extra.append(f"bearerFormat: `{bearer_fmt}`")
        line = f"- **{name}** — type: `{typ}`"
        if extra:
            line += ", " + ", ".join(extra)
        lines.append(line)
        if flows:
            lines.append(f"  - OAuth2 flows: {', '.join(flows)}")
    if api_spec.get("security"):
        lines.append("- Global security requirement present (auth needed by default).")
    return "\n".join(lines)

def _any_method(api_spec: Dict, method: str) -> bool:
    m = method.upper()
    for p, methods in (api_spec.get("paths") or {}).items():
        if any(m == mm.upper() for mm in (methods or {}).keys()):
            return True
    return False

def _has_path_contains(api_spec: Dict, needle: str) -> bool:
    needle = needle.lower()
    return any(needle in str(p).lower() for p in (api_spec.get("paths") or {}).keys())
@app.get("/diagram/flow")
def diagram_flow():
    """
    Return SVG rendering of the generated flow diagram.
    """
    if not API_SPEC:
        return JSONResponse({"error": "No API spec uploaded yet"}, status_code=400)

    md = format_api_summary(API_SPEC)
    # Extract the mermaid block from the markdown
    import re
    match = re.search(r"```mermaid\n(.*?)\n```", md, re.DOTALL)
    if not match:
        return JSONResponse({"error": "No diagram found in summary"}, status_code=400)

    mermaid_code = match.group(1).strip()
    try:
        svg = render_mermaid(mermaid_code)
        return PlainTextResponse(svg, media_type="image/svg+xml")
    except Exception as e:
        return JSONResponse({"error": f"Failed to render diagram: {e}"}, status_code=500)

# def _generate_flow_diagram(api_spec: Dict) -> str:
#     paths = set((api_spec.get("paths") or {}).keys())
#     flow = ["```mermaid", "flowchart LR", "U[👤 Client]"]
#     if _has_path_contains(api_spec, "signup") or _has_path_contains(api_spec, "register"):
#         flow += ["U --> S[POST /signup]", "S --> SOK[✅ Account Created]"]
#     if _has_path_contains(api_spec, "login") or _has_path_contains(api_spec, "auth"):
#         flow += ["U --> L[POST /login]", "L --> T[🔑 Session/JWT Token]"]
#     if _has_path_contains(api_spec, "token"):
#         flow += ["U --> TK[POST /token]", "TK --> T[🔑 Access Token]"]
#     if _has_path_contains(api_spec, "users") and any("{" in p for p in paths):
#         flow += ["T --> GU[GET /users/{id}]", "GU --> P[📄 User Profile]"]
#     elif _has_path_contains(api_spec, "users"):
#         flow += ["T --> GL[GET /users]", "GL --> LST[📄 User List]"]
#     if _any_method(api_spec, "POST"):
#         flow += ["T --> C[POST create resource]"]
#     if _any_method(api_spec, "GET"):
#         flow += ["T --> R[GET read resource]"]
#     if _any_method(api_spec, "PUT"):
#         flow += ["T --> U2[PUT update resource]"]
#     if _any_method(api_spec, "DELETE"):
#         flow += ["T --> D[DELETE remove resource]"]
#     flow.append("```")
#     return "\n".join(flow)

def format_api_summary(spec: dict) -> str:
    """
    Convert parsed OpenAPI spec into a Markdown summary + Mermaid diagram.
    """

    md_lines = ["# API Summary\n"]

    # --- Endpoints overview ---
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            md_lines.append(f"- **{method.upper()} {path}** — {details.get('summary', '')}")

    # --- Build flow diagram (always included) ---
    mermaid_lines = ["```mermaid", "flowchart LR"]

    # Client node
    mermaid_lines.append("Client((Client))")

    for path, methods in spec.get("paths", {}).items():
        for method in methods.keys():
            node_name = f"{method.upper()}_{path}".replace("/", "_").replace("{", "").replace("}", "")
            mermaid_lines.append(f"Client --> {node_name}[{method.upper()} {path}]")

    mermaid_lines.append("```")

    # Join markdown + diagram
    return "\n".join(md_lines + ["\n"] + mermaid_lines)


# ----------------- Routes -----------------
@app.post("/upload-spec")
async def upload_spec(file: UploadFile = File(...)):
    """
    Accept JSON or YAML API docs of many shapes, normalize them, cache
    and return short metadata that frontend expects.
    """
    global API_SPEC
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    parsed = None
    # Try JSON then YAML
    try:
        parsed = json.loads(text)
    except Exception:
        try:
            parsed = yaml.safe_load(text)
        except Exception as e:
            return JSONResponse({"error": f"Invalid JSON/YAML: {e}"}, status_code=400)
    if not isinstance(parsed, dict):
        return JSONResponse({"error": "Uploaded spec must be a JSON/YAML object"}, status_code=400)

    # Normalize (detect format)
    normalized = normalize_spec(parsed)
    API_SPEC = normalized

    title = _safe_get(API_SPEC, "info", "title", default=_safe_get(API_SPEC, "info", "name", default="undefined"))
    version = _safe_get(API_SPEC, "info", "version", default="undefined")
    path_count = len(API_SPEC.get("paths", {}) or {})

    return {"message": "Spec uploaded successfully", "title": title, "version": version, "path_count": path_count}

@app.get("/api-summary")
def api_summary():
    if not API_SPEC:
        return PlainTextResponse("❌ No API spec uploaded yet", status_code=400)
    md = format_api_summary(API_SPEC)
    return PlainTextResponse(md, media_type="text/markdown")

@app.get("/get-spec")
def get_spec():
    if not API_SPEC:
        return JSONResponse({"error": "No API spec uploaded yet"}, status_code=400)
    return JSONResponse(API_SPEC)

@app.get("/summarize-json")
def summarize_json():
    if not API_SPEC:
        return JSONResponse({"error": "No API spec uploaded yet"}, status_code=400)
    result = {}
    for endpoint, methods in (API_SPEC.get("paths") or {}).items():
        result[endpoint] = {}
        for method, details in (methods or {}).items():
            desc = details.get("description") or details.get("summary") or ""
            result[endpoint][method.upper()] = {"summary": summarize_text(desc), "keywords": extract_keywords(desc)}
    return JSONResponse(result)

@app.get("/search")
def search(keyword: str):
    if not API_SPEC:
        return JSONResponse({"error": "No API spec uploaded yet"}, status_code=400)
    kw = (keyword or "").lower().strip()
    if not kw:
        return JSONResponse({"error": "Empty keyword"}, status_code=400)
    results = {}
    for path, methods in (API_SPEC.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            blob = json.dumps(details, ensure_ascii=False).lower()
            if kw in path.lower() or kw in method.lower() or kw in blob:
                results.setdefault(path, {})[method] = details
    if not results:
        return JSONResponse({"message": f"No matches for '{keyword}'"})
    return JSONResponse(results)

# ---------------- Serve frontend if present ----------------
build_path = os.path.join(os.path.dirname(__file__), "../frontend/build")
if os.path.isdir(build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")

@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    index_file = os.path.join(build_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"error":"Frontend build not found. Run `npm run build`."}, status_code=404)
