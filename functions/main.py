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
def generate_plans(request_obj):
    """Generate meal plan options."""
    from handlers.meal_plans import generate_meal_plans
    
    family_id = request_obj.args.get("family_id")
    if not family_id:
        return jsonify({"error": "family_id required"}), 400
    
    try:
        plans = generate_meal_plans(family_id)
        return jsonify({"plans": plans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@functions_framework.http
def select_plan(request_obj):
    """Select a meal plan."""
    from handlers.meal_plans import select_meal_plan
    
    data = request_obj.get_json()
    family_id = data.get("family_id")
    plan_id = data.get("plan_id")
    
    if not family_id or not plan_id:
        return jsonify({"error": "family_id and plan_id required"}), 400
    
    try:
        plan = select_meal_plan(family_id, plan_id)
        return jsonify({"plan": plan})
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
