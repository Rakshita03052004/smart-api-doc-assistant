# backend/main.py
from __future__ import annotations
import os
import json
import yaml
import re
from typing import Any, Dict, List

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# ---------------- App Setup ----------------
app = FastAPI(title="Smart API Doc Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Global State ----------------
API_SPEC: Dict[str, Any] = {}

# ---------------- Helpers ----------------
def _safe_get(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

# ---------------- Normalizers ----------------
def _normalize_openapi(spec: dict) -> dict:
    info = spec.get("info", {}) or {}
    paths = spec.get("paths", {}) or {}
    return {"info": info, "paths": paths}

def _normalize_postman(spec: dict) -> dict:
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
                    "parameters": [],
                    "responses": {}
                }
    _walk(items)
    return {"info": info, "paths": paths}

def _normalize_custom_endpoints(spec: dict) -> dict:
    info = spec.get("info", {}) or {}
    if not info and "name" in spec:
        info = {"title": spec.get("name"), "version": spec.get("version")}
    paths = {}
    for e in spec.get("endpoints", []) or []:
        path = e.get("path") or e.get("endpoint") or "/"
        method = (e.get("method") or "GET").lower()
        summary = e.get("name") or e.get("summary") or ""
        description = e.get("description") or ""
        params = []
        if e.get("queryParams"):
            for k, t in (e.get("queryParams") or {}).items():
                params.append({"name": k, "in": "query", "schema": {"type": str(t)}, "required": False, "description": ""})
        if e.get("pathParams"):
            for k, t in (e.get("pathParams") or {}).items():
                params.append({"name": k, "in": "path", "schema": {"type": str(t)}, "required": True, "description": ""})
        requestBody = {}
        if e.get("body"):
            props = {k: {"type": "string", "description": ""} for k in e.get("body", {})}
            requestBody = {"content": {"application/json": {"schema": {"type": "object", "properties": props, "required": []}}}}
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
    info = spec.get("info", {}) or {"title": spec.get("title") or "API"}
    paths = {}
    for k, v in spec.items():
        if isinstance(k, str) and k.startswith("/"):
            paths[k] = {}
            if isinstance(v, dict):
                for m, d in v.items():
                    paths[k][m.lower()] = {"summary": _safe_get(d, "summary", default=""), "description": _safe_get(d, "description", default=""), "parameters": d.get("parameters", []), "responses": d.get("responses", {})}
    return {"info": info, "paths": paths}

def normalize_spec(raw_spec: dict) -> dict:
    if "paths" in raw_spec and isinstance(raw_spec["paths"], dict):
        return _normalize_openapi(raw_spec)
    if "item" in raw_spec and isinstance(raw_spec["item"], list):
        return _normalize_postman(raw_spec)
    if "endpoints" in raw_spec and isinstance(raw_spec["endpoints"], list):
        return _normalize_custom_endpoints(raw_spec)
    if "swagger" in raw_spec or "openapi" in raw_spec:
        return _normalize_openapi(raw_spec)
    return _normalize_minimal(raw_spec)


# ---------------- Text Helpers ----------------
STOPWORDS = set("a an and are as at be by for from has have how i if in into is it its of on or that the their them they this to was were what when where which who will with you your".split())

def _first_sentence(text: str) -> str:
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return parts[0].strip() if parts else text.strip()

def summarize_text(text: str, max_length: int = 250) -> str:
    t = (text or "").strip()
    if not t:
        return "No description available."
    s = _first_sentence(t)
    if len(s) < 30:
        return t[:max_length].rstrip()
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
    info_desc = _safe_get(api_spec, "info", "description", default="")
    if info_desc:
        chunks.append(str(info_desc))
    for path, methods in (api_spec.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            chunks.append(str(details.get("description") or details.get("summary") or ""))
    return " ".join([c for c in chunks if c]).strip()

# ---------------- Markdown Builders ----------------
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
            for param in (details.get("parameters") or []):
                name = param.get("name", "")
                loc = param.get("in", "")
                typ = _safe_get(param, "schema", "type", default="—")
                req = "✅" if param.get("required") else "❌"
                desc = param.get("description", "—")
                rows.append(f"| `{path}` | `{name}` | `{loc}` | `{typ}` | {req} | {desc} |")
                any_row = True
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

def _generate_flow_diagram(api_spec: Dict) -> str:
    paths = set((api_spec.get("paths") or {}).keys())
    flow = ["```mermaid", "flowchart LR"]
    flow.append("Client((Client))")
    for path, methods in (api_spec.get("paths") or {}).items():
        for method in methods.keys():
            node_name = f"{method.upper()}_{path}".replace("/", "_").replace("{", "").replace("}", "")
            flow.append(f"Client --> {node_name}[{method.upper()} {path}]")
    flow.append("```")
    return "\n".join(flow)

# ---------------- Format API Summary ----------------
def format_api_summary(api_spec: dict) -> str:
    overview_text = summarize_text(_collect_all_descriptions(api_spec))
    md = [
        f"# 📄 { _safe_get(api_spec, 'info', 'title', default='API') } — Summary",
        "## 📝 Overview",
        overview_text,
        "",
        _build_endpoints_table(api_spec),
        "",
        _build_params_table(api_spec),
        "",
        _build_auth_section(api_spec),
        "",
        "## 🔄 Flow Diagram",
        _generate_flow_diagram(api_spec)
    ]
    return "\n".join(md)

# ---------------- Routes ----------------
@app.post("/upload-spec")
async def upload_spec(file: UploadFile = File(...)):
    global API_SPEC
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    parsed = None
    try:
        parsed = json.loads(text)
    except Exception:
        try:
            parsed = yaml.safe_load(text)
        except Exception as e:
            return JSONResponse({"error": f"Invalid JSON/YAML: {e}"}, status_code=400)
    if not isinstance(parsed, dict):
        return JSONResponse({"error": "Uploaded spec must be a JSON/YAML object"}, status_code=400)
    normalized = normalize_spec(parsed)
    API_SPEC = normalized
    title = _safe_get(API_SPEC, "info", "title", default="undefined")
    version = _safe_get(API_SPEC, "info", "version", default="undefined")
    path_count = len(API_SPEC.get("paths", {}) or {})
    return {"message": "Spec uploaded successfully", "title": title, "version": version, "path_count": path_count}

@app.get("/api-summary")
def api_summary():
    if not API_SPEC:
        return PlainTextResponse("❌ No API spec uploaded yet", status_code=400)
    return PlainTextResponse(format_api_summary(API_SPEC), media_type="text/markdown")

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
    for path, methods in (API_SPEC.get("paths") or {}).items():
        result[path] = {}
        for method, details in (methods or {}).items():
            desc = details.get("description") or details.get("summary") or ""
            result[path][method.upper()] = {"summary": summarize_text(desc), "keywords": extract_keywords(desc)}
    return JSONResponse(result)
# ---------------- Search Helpers ----------------
def build_smart_description(path: str, method: str, details: Dict) -> str:
    """Generate fallback description if missing in spec"""
    parts = []
    if details.get("summary"):
        parts.append(details["summary"])
    if details.get("operationId"):
        parts.append(f"Operation ID: {details['operationId']}")
    if details.get("tags"):
        parts.append(f"Tags: {', '.join(details['tags'])}")
    if not parts:
        return f"→ {method.upper()} {path} (no description in spec)"
    return " | ".join(parts)


# ---------------- Routes ----------------
@app.get("/search")
def search(keyword: str):
    if not API_SPEC:
        return JSONResponse({"error": "No API spec uploaded yet"}, status_code=400)

    kw = (keyword or "").lower().strip()
    if not kw:
        return JSONResponse({"error": "Empty keyword"}, status_code=400)

    results = []
    for path, methods in (API_SPEC.get("paths") or {}).items():
        for method, details in (methods or {}).items():
            blob = json.dumps(details, ensure_ascii=False).lower()
            if kw in path.lower() or kw in method.lower() or kw in blob:
                results.append({
                    "endpoint": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "description": details.get("description") or build_smart_description(path, method, details)
                })

    if not results:
        return JSONResponse({"message": f"No matches for '{keyword}'"})

    return JSONResponse({"results": results})

# @app.get("/search")
# def build_smart_description(path: str, method: str, details: Dict) -> str:
#     """Generate fallback description if missing in spec"""
#     parts = []
#     if details.get("summary"):
#         parts.append(details["summary"])
#     if details.get("operationId"):
#         parts.append(f"Operation ID: {details['operationId']}")
#     if details.get("tags"):
#         parts.append(f"Tags: {', '.join(details['tags'])}")
#     if not parts:
#         return f"→ {method.upper()} {path} (no description in spec)"
#     return " | ".join(parts)

# def search(keyword: str):
#     if not API_SPEC:
#         return JSONResponse({"error": "No API spec uploaded yet"}, status_code=400)

#     kw = (keyword or "").lower().strip()
#     if not kw:
#         return JSONResponse({"error": "Empty keyword"}, status_code=400)

#     results = []
#     for path, methods in (API_SPEC.get("paths") or {}).items():
#         for method, details in (methods or {}).items():
#             blob = json.dumps(details, ensure_ascii=False).lower()
#             if kw in path.lower() or kw in method.lower() or kw in blob:
#                 results.append({
#     "endpoint": path,
#     "method": method.upper(),
#     "summary": details.get("summary", ""),
#     "description": details.get("description") or build_smart_description(path, method, details)
# })



#     if not results:
#         return JSONResponse({"message": f"No matches for '{keyword}'"})

#     return JSONResponse({"results": results})


# ---------------- Serve Frontend ----------------
build_path = os.path.join(os.path.dirname(__file__), "../frontend/build")
if os.path.isdir(build_path):
    app.mount("/static", StaticFiles(directory=os.path.join(build_path, "static")), name="static")

@app.get("/{full_path:path}")
async def serve_react(full_path: str):
    index_file = os.path.join(build_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return JSONResponse({"error":"Frontend build not found. Run `npm run build`."}, status_code=404)