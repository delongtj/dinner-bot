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
        "SELECT u.id as user_id, f.id as family_id FROM families f JOIN users u ON u.family_id = f.id WHERE u.email = %s",
        (email,),
    )
    if not rows:
        return None, email, (
            jsonify({"error": "not_registered"}),
            404,
        )

    return str(rows[0]["family_id"]), email, None


def _get_user_from_token(request_obj):
    """Verify the Firebase token and return the full user row.

    Returns (user_row, error_response).
    """
    from handlers.auth import verify_token
    from db.connection import query

    try:
        decoded = verify_token(request_obj)
    except ValueError as e:
        return None, (jsonify({"error": str(e)}), 401)

    email = decoded["email"]

    user = query(
        "SELECT * FROM users WHERE email = %s",
        (email,),
        fetch_one=True,
    )

    return user, None


@functions_framework.http
def health(request_obj):
    """Health check endpoint."""
    return jsonify({"status": "ok"})


@functions_framework.http
def register(request_obj):
    """Register a new user. Creates a family or joins one via invite code."""
    from handlers.auth import verify_token
    from db.connection import query
    from handlers.users import register_user, join_family_with_invite

    try:
        decoded = verify_token(request_obj)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401

    email = decoded["email"]

    # If user already exists, return their info (idempotent)
    existing = query("SELECT * FROM users WHERE email = %s", (email,), fetch_one=True)
    if existing:
        family = query(
            "SELECT * FROM families WHERE id = %s",
            (str(existing["family_id"]),),
            fetch_one=True,
        )
        members = query(
            "SELECT id, email, name, created_at FROM users WHERE family_id = %s ORDER BY created_at",
            (str(existing["family_id"]),),
        )
        return jsonify({"user": existing, "family": family, "members": members})

    data = request_obj.get_json(silent=True) or {}
    name = data.get("name")
    invite_code = data.get("invite_code")

    try:
        if invite_code:
            result = join_family_with_invite(email, name, invite_code)
        else:
            result = register_user(email, name)

        members = query(
            "SELECT id, email, name, created_at FROM users WHERE family_id = %s ORDER BY created_at",
            (str(result["family"]["id"]),),
        )
        result["members"] = members
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def me(request_obj):
    """Get current user info, family, and family members."""
    from handlers.users import get_family_members

    user, err = _get_user_from_token(request_obj)
    if err:
        return err

    if not user:
        return jsonify({"error": "not_registered"}), 404

    from db.connection import query
    family = query(
        "SELECT * FROM families WHERE id = %s",
        (str(user["family_id"]),),
        fetch_one=True,
    )
    members = get_family_members(str(user["family_id"]))

    return jsonify({"user": user, "family": family, "members": members})


@functions_framework.http
def create_invite(request_obj):
    """Generate an invite code for the current user's family."""
    from handlers.users import create_invite as _create_invite

    user, err = _get_user_from_token(request_obj)
    if err:
        return err

    if not user:
        return jsonify({"error": "not_registered"}), 404

    try:
        result = _create_invite(str(user["family_id"]), str(user["id"]))
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
