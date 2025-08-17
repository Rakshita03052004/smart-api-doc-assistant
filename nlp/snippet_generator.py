# nlp/snippet_generator.py

def generate_example_request():
    """
    Generates a sample API request snippet.
    Returns a dictionary representing a request body.
    """
    # Example placeholder request
    return {
        "endpoint": "/api/example",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "param1": "value1",
            "param2": "value2"
        }
    }

def generate_example_response():
    """
    Generates a sample API response snippet.
    Returns a dictionary representing a response body.
    """
    # Example placeholder response
    return {
        "status": "success",
        "data": {
            "id": 1,
            "message": "Example response"
        }
    }