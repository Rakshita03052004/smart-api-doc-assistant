# search.py
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()

# Assume API_SPEC is loaded in main.py and imported here
from main import API_SPEC  

@router.get("/search")
async def search_endpoint(keyword: Optional[str] = Query(..., description="Keyword to search in API spec")):
    if not API_SPEC:
        return {"error": "No API spec uploaded"}

    results = {}

    # Search inside "paths"
    for path, methods in API_SPEC.get("paths", {}).items():
        if keyword.lower() in path.lower():
            results[path] = methods
        else:
            for method, details in methods.items():
                if (keyword.lower() in method.lower() or
                        keyword.lower() in details.get("summary", "").lower() or
                        keyword.lower() in details.get("description", "").lower()):
                    results[path] = {method: details}

    # Search inside "components" if available
    if "components" in API_SPEC:
        for comp_type, comp_dict in API_SPEC["components"].items():
            for comp_name, comp_details in comp_dict.items():
                if keyword.lower() in comp_name.lower():
                    results[f"components/{comp_type}/{comp_name}"] = comp_details

    return {"results": results}