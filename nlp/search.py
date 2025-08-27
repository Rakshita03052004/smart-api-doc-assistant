# search.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import json

router = APIRouter()

# This should be imported from your main module or loaded here
# For now, I'll create a placeholder that you can replace
API_SPEC = {}

def load_api_spec():
    """Load the API spec from wherever it's stored"""
    global API_SPEC
    try:
        # Replace this with your actual API spec loading logic
        # For example, if you're loading from a file:
        # with open('hospital.json', 'r') as f:
        #     API_SPEC = json.load(f)
        
        # Or if it's stored in memory from your main module:
        from main import get_api_spec  # Adjust import as needed
        API_SPEC = get_api_spec()
    except Exception as e:
        print(f"Error loading API spec: {e}")
        API_SPEC = {}

def generate_code_snippets(path: str, method: str, base_url: str = "http://localhost:8000") -> dict:
    """
    Generate Python, JavaScript, and cURL code snippets for the given endpoint.
    """
    url = f"{base_url}{path}"
    
    # Handle path parameters in examples
    example_path = path
    if "{id}" in path:
        example_path = path.replace("{id}", "123")
    example_url = f"{base_url}{example_path}"

    python_code = f"""import requests

url = "{example_url}"
"""

    js_code = f"""fetch("{example_url}", {{
  method: "{method.upper()}",
  headers: {{
    "Content-Type": "application/json"
  }}
"""

    curl_code = f"""curl -X {method.upper()} "{example_url}" \\
  -H "Content-Type: application/json\""""

    # Add payload for POST/PUT requests
    if method.upper() in ["POST", "PUT", "PATCH"]:
        python_code += """payload = {}
headers = {
    "Content-Type": "application/json"
}

response = requests.""" + method.lower() + """(url, json=payload, headers=headers)
print(response.json())"""

        js_code += """,
  body: JSON.stringify({})
})
  .then(res => res.json())
  .then(console.log)
  .catch(console.error);"""

        curl_code += """ \\
  -d '{}'"""

    else:  # GET, DELETE
        python_code += """headers = {}

response = requests.""" + method.lower() + """(url, headers=headers)
print(response.json())"""

        js_code += """})
  .then(res => res.json())
  .then(console.log)
  .catch(console.error);"""

    return {
        "python": python_code,
        "javascript": js_code,
        "curl": curl_code
    }


@router.get("/search")
async def search_endpoint(keyword: Optional[str] = Query(None, description="Keyword to search in API spec")):
    """Search for endpoints matching the keyword"""
    
    if not keyword:
        raise HTTPException(status_code=400, detail="Keyword parameter is required")
    
    # Load API spec if not already loaded
    if not API_SPEC:
        load_api_spec()
    
    if not API_SPEC:
        raise HTTPException(status_code=500, detail="No API spec available")

    results = []
    keyword_lower = keyword.lower()

    # Search inside "paths"
    paths = API_SPEC.get("paths", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            summary = details.get("summary", "")
            description = details.get("description", "")
            operation_id = details.get("operationId", "")
            
            # Check if keyword matches any of these fields
            if any(keyword_lower in field.lower() for field in [path, method, summary, description, operation_id]):
                result_item = {
                    "endpoint": path,
                    "method": method.upper(),
                    "summary": summary,
                    "description": description,
                    "operationId": operation_id,
                    "code_snippets": generate_code_snippets(path, method)
                }
                results.append(result_item)

    # Search inside "components" (schemas, etc.)
    components_results = []
    if "components" in API_SPEC:
        for comp_type, comp_dict in API_SPEC["components"].items():
            if isinstance(comp_dict, dict):
                for comp_name, comp_details in comp_dict.items():
                    if keyword_lower in comp_name.lower():
                        components_results.append({
                            "type": comp_type,
                            "name": comp_name,
                            "details": comp_details
                        })

    response_data = {
        "keyword": keyword,
        "endpoints_found": len(results),
        "components_found": len(components_results),
        "endpoints": results
    }
    
    if components_results:
        response_data["components"] = components_results

    if not results and not components_results:
        return {
            "keyword": keyword,
            "message": f"No matches found for '{keyword}'",
            "endpoints_found": 0,
            "components_found": 0,
            "endpoints": [],
            "suggestion": "Try searching for terms like 'patient', 'doctor', 'appointment', etc."
        }

    return response_data


@router.get("/endpoints")
async def list_all_endpoints():
    """List all available endpoints"""
    
    if not API_SPEC:
        load_api_spec()
    
    if not API_SPEC:
        raise HTTPException(status_code=500, detail="No API spec available")

    endpoints = []
    paths = API_SPEC.get("paths", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            endpoints.append({
                "endpoint": path,
                "method": method.upper(),
                "summary": details.get("summary", ""),
                "description": details.get("description", "")
            })
    
    return {
        "total_endpoints": len(endpoints),
        "endpoints": endpoints
    }