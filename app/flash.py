from fastapi import Request
from typing import List, Dict, Any

def flash(request: Request, message: str, category: str = "primary"):
    """
    Adds a flash message to the session's message list.
    """
    if "_messages" not in request.session:
        request.session["_messages"] = []
    # In some Python versions, mutating a list in a session might not be detected.
    # To be safe, we can re-assign it.
    messages = request.session["_messages"]
    messages.append({"category": category, "message": message})
    request.session["_messages"] = messages

def get_flashed_messages(request: Request) -> List[Dict[str, Any]]:
    """
    Retrieves and clears all flash messages from the session.
    """
    return request.session.pop("_messages", [])