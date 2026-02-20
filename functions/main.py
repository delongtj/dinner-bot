import os
from dotenv import load_dotenv

# Load .env for local development (no-op in Cloud Functions)
load_dotenv()

import functions_framework
from flask import jsonify


def _get_family_id_from_token(request_obj):
    """Verify the Firebase token and resolve the user's family_id.

    Returns (family_id, email, error_response).
    On success error_response is None.  On failure family_id/email are None.
    """
    from handlers.auth import verify_token
    from db.connection import query

    try:
        decoded = verify_token(request_obj)
    except ValueError as e:
        return None, None, (jsonify({"error": str(e)}), 401)

    email = decoded["email"]

    rows = query(
        "SELECT f.id FROM families f JOIN users u ON u.family_id = f.id WHERE u.email = %s",
        (email,),
    )
    if not rows:
        return None, email, (
            jsonify({"error": "No family found for this account. Please complete setup."}),
            404,
        )

    return str(rows[0]["id"]), email, None


@functions_framework.http
def health(request_obj):
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@functions_framework.http
def list_recipes(request_obj):
    """List recipes for a family."""
    from handlers.recipes import list_recipes as _list_recipes

    family_id, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

    try:
        recipes = _list_recipes(family_id)
        return jsonify(recipes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def add_recipe(request_obj):
    """Add a recipe by URL (extracts metadata via LLM) or manual entry."""
    from handlers.recipes import extract_and_create_recipe, create_recipe

    family_id, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

    data = request_obj.get_json()

    try:
        url = data.get("url")
        if url:
            result = extract_and_create_recipe(family_id, url)
        else:
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

    family_id, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

    try:
        result = create_session(family_id)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def planning_chat(request_obj):
    """Send a message in an active planning session."""
    from handlers.planning import chat

    _, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

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

    family_id, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

    data = request_obj.get_json()
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    try:
        result = finalize_session(session_id, family_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def abandon_plan(request_obj):
    """Abandon an active planning session."""
    from handlers.planning import abandon_session

    _, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

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
def get_config(request_obj):
    """Get family configuration."""
    from handlers.config import get_family_config

    family_id, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

    try:
        config = get_family_config(family_id)
        return jsonify({"config": config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def setup_config(request_obj):
    """Set up family configuration (calendars, preferences, etc.)."""
    from handlers.config import setup_family_config

    family_id, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

    data = request_obj.get_json()

    try:
        config = setup_family_config(family_id, data)
        return jsonify({"config": config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def get_grocery(request_obj):
    """Get the most recent grocery list for the family."""
    from db.connection import query as db_query

    family_id, _, err = _get_family_id_from_token(request_obj)
    if err:
        return err

    try:
        result = db_query(
            """
            SELECT gl.* FROM grocery_lists gl
            JOIN meal_plans mp ON mp.id = gl.meal_plan_id
            WHERE mp.family_id = %s
            ORDER BY gl.created_at DESC
            LIMIT 1
            """,
            (family_id,),
            fetch_one=True,
        )
        return jsonify({"grocery_list": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
