import json
from db.connection import query, execute
from llm import get_llm_provider


def list_recipes(family_id: str):
    """List all active recipes for a family."""
    sql = """
        SELECT id, title, prep_time, cook_time, servings, 
               cuisine_type, meal_type, complexity, dietary_flags, 
               seasonal_relevance, rating, created_at, updated_at
        FROM recipes
        WHERE family_id = %s AND active = TRUE
        ORDER BY created_at DESC
    """
    return query(sql, (family_id,))


def get_recipe(recipe_id: str):
    """Get a single recipe by ID."""
    sql = """
        SELECT * FROM recipes WHERE id = %s
    """
    return query(sql, (recipe_id,), fetch_one=True)


def create_recipe(family_id: str, data: dict):
    """Create a new recipe."""
    sql = """
        INSERT INTO recipes (
            family_id, url, title, prep_time, cook_time, servings,
            ingredients, instructions, cuisine_type, meal_type,
            complexity, dietary_flags, seasonal_relevance
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at
    """
    params = (
        family_id,
        data.get("url"),
        data["title"],
        data.get("prep_time", 0),
        data.get("cook_time", 0),
        data.get("servings", 2),
        data.get("ingredients", ""),
        data.get("instructions", ""),
        data.get("cuisine_type", []),
        data.get("meal_type", "dinner"),
        data.get("complexity", "moderate"),
        data.get("dietary_flags", []),
        data.get("seasonal_relevance", "any")
    )
    result = query(sql, params, fetch_one=True)
    return result


def extract_and_create_recipe(family_id: str, url: str):
    """Extract recipe metadata from URL and create recipe."""
    llm = get_llm_provider()
    metadata = llm.extract_recipe_metadata(url=url)
    metadata["url"] = url
    
    return create_recipe(family_id, metadata)
