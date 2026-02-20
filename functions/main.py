import os
from dotenv import load_dotenv

# Load .env for local development (no-op in Cloud Functions)
load_dotenv()

import functions_framework
from flask import jsonify


@functions_framework.http
def health(request_obj):
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@functions_framework.http
def list_recipes(request_obj):
    """List recipes for a family."""
    from handlers.recipes import list_recipes as _list_recipes

    family_id = request_obj.args.get("family_id")
    if not family_id:
        return jsonify({"error": "family_id required"}), 400

    try:
        recipes = _list_recipes(family_id)
        return jsonify(recipes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def add_recipe(request_obj):
    """Add a recipe by URL (extracts metadata via LLM) or manual entry."""
    from handlers.recipes import extract_and_create_recipe, create_recipe

    data = request_obj.get_json()
    family_id = data.get("family_id")

    if not family_id:
        return jsonify({"error": "family_id required"}), 400

    try:
        url = data.get("url")
        if url:
            # Extract metadata from URL and create recipe
            result = extract_and_create_recipe(family_id, url)
        else:
            # Manual entry - requires at least a title
            if not data.get("title"):
                return jsonify({"error": "url or title required"}), 400
            result = create_recipe(family_id, data)

        return jsonify({"recipe": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def create_planning_session(request_obj):
    """Start a new interactive planning session."""
    from handlers.planning import create_session

    data = request_obj.get_json()
    family_id = data.get("family_id")

    if not family_id:
        return jsonify({"error": "family_id required"}), 400

    try:
        result = create_session(family_id)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def planning_chat(request_obj):
    """Send a message in an active planning session."""
    from handlers.planning import chat

    data = request_obj.get_json()
    session_id = data.get("session_id")
    message = data.get("message")

    if not session_id or not message:
        return jsonify({"error": "session_id and message required"}), 400

    try:
        result = chat(session_id, message)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def finalize_plan(request_obj):
    """Finalize a planning session into a meal plan."""
    from handlers.planning import finalize_session

    data = request_obj.get_json()
    session_id = data.get("session_id")
    family_id = data.get("family_id")

    if not session_id or not family_id:
        return jsonify({"error": "session_id and family_id required"}), 400

    try:
        result = finalize_session(session_id, family_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def abandon_plan(request_obj):
    """Abandon an active planning session."""
    from handlers.planning import abandon_session

    data = request_obj.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    try:
        result = abandon_session(session_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def setup_config(request_obj):
    """Set up family configuration (calendars, preferences, etc.)."""
    from handlers.config import setup_family_config
    
    data = request_obj.get_json()
    family_id = data.get("family_id")
    
    if not family_id:
        return jsonify({"error": "family_id required"}), 400
    
    try:
        config = setup_family_config(family_id, data)
        return jsonify({"config": config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
