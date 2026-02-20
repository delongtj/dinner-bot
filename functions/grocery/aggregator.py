import json
from fractions import Fraction
from db.connection import query

# Unit aliases → canonical short form
UNIT_ALIASES = {
    "tablespoon": "tbsp",
    "tablespoons": "tbsp",
    "tbsp": "tbsp",
    "tbs": "tbsp",
    "teaspoon": "tsp",
    "teaspoons": "tsp",
    "tsp": "tsp",
    "cup": "cup",
    "cups": "cup",
    "ounce": "oz",
    "ounces": "oz",
    "oz": "oz",
    "pound": "lb",
    "pounds": "lb",
    "lb": "lb",
    "lbs": "lb",
    "gram": "g",
    "grams": "g",
    "g": "g",
    "kilogram": "kg",
    "kilograms": "kg",
    "kg": "kg",
    "milliliter": "ml",
    "milliliters": "ml",
    "ml": "ml",
    "liter": "L",
    "liters": "L",
    "l": "L",
    "pint": "pint",
    "pints": "pint",
    "quart": "quart",
    "quarts": "quart",
    "gallon": "gallon",
    "gallons": "gallon",
    "clove": "clove",
    "cloves": "clove",
    "can": "can",
    "cans": "can",
    "bunch": "bunch",
    "bunches": "bunch",
    "slice": "slice",
    "slices": "slice",
    "piece": "piece",
    "pieces": "piece",
}

# Category sort order for grouped output
CATEGORY_ORDER = [
    "produce",
    "meat",
    "dairy",
    "bakery",
    "frozen",
    "pantry",
    "spices",
    "other",
]


def _normalize_unit(unit: str) -> str:
    """Normalize a unit string to its canonical short form."""
    return UNIT_ALIASES.get(unit.lower().strip(), unit.lower().strip())


def _parse_quantity(qty_str: str) -> float:
    """
    Parse a quantity string into a float.
    Handles fractions (1/2), mixed numbers (1 1/2), and decimals (1.5).
    """
    if not qty_str:
        return 0.0

    qty_str = qty_str.strip()

    # Try plain float first
    try:
        return float(qty_str)
    except ValueError:
        pass

    # Try fraction (e.g. "1/2")
    try:
        return float(Fraction(qty_str))
    except (ValueError, ZeroDivisionError):
        pass

    # Try mixed number (e.g. "1 1/2")
    parts = qty_str.split()
    if len(parts) == 2:
        try:
            whole = float(parts[0])
            frac = float(Fraction(parts[1]))
            return whole + frac
        except (ValueError, ZeroDivisionError):
            pass

    return 0.0


def _format_quantity(qty: float) -> str:
    """Format a float quantity back to a readable string."""
    if qty == int(qty):
        return str(int(qty))
    # Round to 2 decimal places
    return f"{qty:.2f}".rstrip("0").rstrip(".")


def aggregate_grocery_list(plan_data: dict) -> list:
    """
    Build a consolidated grocery list from a meal plan.

    Args:
        plan_data: dict mapping day names to {recipe_id, recipe_name, notes}

    Returns:
        Sorted list of {name, quantity, unit, category, recipe_sources}
    """
    # Collect all recipe IDs from the plan
    recipe_ids = []
    recipe_day_map = {}  # recipe_id -> list of day names
    for day, entry in plan_data.items():
        rid = entry.get("recipe_id")
        if rid:
            if rid not in recipe_day_map:
                recipe_ids.append(rid)
                recipe_day_map[rid] = []
            recipe_day_map[rid].append(day)

    if not recipe_ids:
        return []

    # Fetch recipes from DB
    placeholders = ",".join(["%s"] * len(recipe_ids))
    recipes = query(
        f"SELECT id, title, ingredients FROM recipes WHERE id IN ({placeholders})",
        tuple(recipe_ids),
    )

    # Flatten and deduplicate ingredients
    # Key: (normalized_name, normalized_unit) -> accumulated item
    merged = {}

    for recipe in recipes:
        ingredients = recipe.get("ingredients", [])
        if isinstance(ingredients, str):
            try:
                ingredients = json.loads(ingredients)
            except (json.JSONDecodeError, TypeError):
                continue

        recipe_title = recipe.get("title", "Unknown")

        for ing in ingredients:
            name = ing.get("name", "").strip().lower()
            unit = _normalize_unit(ing.get("unit", ""))
            qty = _parse_quantity(str(ing.get("quantity", "0")))
            category = ing.get("category", "other").lower()

            if not name:
                continue

            key = (name, unit)
            if key in merged:
                merged[key]["quantity"] += qty
                if recipe_title not in merged[key]["recipe_sources"]:
                    merged[key]["recipe_sources"].append(recipe_title)
            else:
                merged[key] = {
                    "name": name,
                    "quantity": qty,
                    "unit": unit,
                    "category": category,
                    "recipe_sources": [recipe_title],
                }

    # Sort by category order, then by name within each category
    def sort_key(item):
        cat_idx = CATEGORY_ORDER.index(item["category"]) if item["category"] in CATEGORY_ORDER else len(CATEGORY_ORDER)
        return (cat_idx, item["name"])

    items = sorted(merged.values(), key=sort_key)

    # Format quantities for output
    for item in items:
        item["quantity"] = _format_quantity(item["quantity"])

    return items


def save_grocery_list(meal_plan_id: str, items: list) -> dict:
    """
    Persist a grocery list to the database.

    Returns the created grocery_list record.
    """
    from psycopg2.extras import Json

    sql = """
        INSERT INTO grocery_lists (meal_plan_id, items)
        VALUES (%s, %s)
        RETURNING id, created_at
    """
    result = query(sql, (meal_plan_id, Json(items)), fetch_one=True)
    return {
        "id": str(result["id"]),
        "meal_plan_id": meal_plan_id,
        "items": items,
        "created_at": str(result["created_at"]),
    }
