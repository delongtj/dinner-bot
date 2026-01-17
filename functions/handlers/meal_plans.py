import json
from datetime import datetime
from db.connection import query, execute
from llm import get_llm_provider


def get_family_config(family_id: str):
    """Get family configuration."""
    sql = "SELECT * FROM family_config WHERE family_id = %s"
    return query(sql, (family_id,), fetch_one=True)


def get_active_recipes(family_id: str):
    """Get all active recipes for a family."""
    sql = """
        SELECT id, title, prep_time, cook_time, servings,
               cuisine_type, meal_type, complexity, dietary_flags,
               seasonal_relevance, rating, created_at
        FROM recipes
        WHERE family_id = %s AND active = TRUE
        ORDER BY created_at DESC
    """
    return query(sql, (family_id,))


def generate_meal_plans(family_id: str, num_plans: int = 4):
    """Generate multiple meal plan options."""
    config = get_family_config(family_id)
    recipes = get_active_recipes(family_id)
    
    if not recipes:
        raise ValueError("No active recipes available for meal planning")
    
    # Prepare preferences dict
    preferences = {
        "cuisine_preferences": config.get("cuisine_preferences", []),
        "dietary_restrictions": config.get("dietary_restrictions", []),
        "target_prep_time": config.get("target_prep_time"),
        "serving_size": config.get("serving_size", 2),
    }
    
    # TODO: Get calendar constraints (busy days, etc.)
    calendar_constraints = {}
    
    # Call LLM to generate plans
    llm = get_llm_provider()
    plans = llm.generate_meal_plans(
        recipes,
        preferences,
        calendar_constraints,
        num_plans
    )
    
    # Store generated plans
    results = []
    for i, plan in enumerate(plans, 1):
        sql = """
            INSERT INTO meal_plans (
                family_id, week_start_date, plan, variant
            ) VALUES (%s, CURRENT_DATE, %s, %s)
            RETURNING id, created_at
        """
        result = query(sql, (family_id, json.dumps(plan), i), fetch_one=True)
        results.append({**plan, "id": str(result["id"]), "variant": i})
    
    return results


def select_meal_plan(family_id: str, plan_id: str):
    """Mark a meal plan as selected."""
    # Deselect any previously selected plans
    execute(
        "UPDATE meal_plans SET selected = FALSE WHERE family_id = %s AND selected = TRUE",
        (family_id,)
    )
    
    # Select the chosen plan
    sql = """
        UPDATE meal_plans
        SET selected = TRUE, selected_at = CURRENT_TIMESTAMP
        WHERE id = %s AND family_id = %s
        RETURNING id, plan
    """
    return query(sql, (plan_id, family_id), fetch_one=True)
