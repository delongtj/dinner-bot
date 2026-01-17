from db.connection import query, execute


def setup_family_config(family_id: str, config_data: dict):
    """
    Initialize or update family configuration.
    
    Args:
        family_id: UUID of the family
        config_data: Dict with keys:
            - personal_calendar_ids: List of personal calendar email addresses
            - shared_calendar_id: Shared calendar ID
            - cuisine_preferences: List of cuisine types
            - dietary_restrictions: List of dietary restrictions
            - target_prep_time: Max prep time in minutes
            - serving_size: Number of servings
            - plan_generation_day: Day to generate plans (e.g., "Saturday")
            - plan_generation_time: Time to generate plans (e.g., "18:00")
    """
    sql = """
        INSERT INTO family_config (
            family_id, personal_calendar_ids, shared_calendar_id,
            cuisine_preferences, dietary_restrictions, target_prep_time,
            serving_size, plan_generation_day, plan_generation_time
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (family_id) DO UPDATE SET
            personal_calendar_ids = EXCLUDED.personal_calendar_ids,
            shared_calendar_id = EXCLUDED.shared_calendar_id,
            cuisine_preferences = EXCLUDED.cuisine_preferences,
            dietary_restrictions = EXCLUDED.dietary_restrictions,
            target_prep_time = EXCLUDED.target_prep_time,
            serving_size = EXCLUDED.serving_size,
            plan_generation_day = EXCLUDED.plan_generation_day,
            plan_generation_time = EXCLUDED.plan_generation_time,
            updated_at = CURRENT_TIMESTAMP
        RETURNING *
    """
    
    params = (
        family_id,
        config_data.get("personal_calendar_ids", []),
        config_data.get("shared_calendar_id"),
        config_data.get("cuisine_preferences", []),
        config_data.get("dietary_restrictions", []),
        config_data.get("target_prep_time"),
        config_data.get("serving_size", 2),
        config_data.get("plan_generation_day", "Saturday"),
        config_data.get("plan_generation_time", "18:00"),
    )
    
    return query(sql, params, fetch_one=True)


def get_family_config(family_id: str):
    """Get family configuration."""
    sql = "SELECT * FROM family_config WHERE family_id = %s"
    return query(sql, (family_id,), fetch_one=True)
