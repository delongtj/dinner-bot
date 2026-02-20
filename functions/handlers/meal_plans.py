from datetime import datetime, timedelta
from db.connection import query
from calendar.google_calendar import GoogleCalendarProvider


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



def _get_calendar_constraints(config: dict) -> dict:
    """
    Read personal calendars to identify busy days.
    Returns a dict with busy days for the upcoming week.
    """
    personal_calendar_ids = config.get("personal_calendar_ids", [])
    if not personal_calendar_ids:
        return {}
    
    try:
        cal = GoogleCalendarProvider()
        # Get Monday of the current week
        today = datetime.now().date()
        days_since_monday = today.weekday()
        week_start = datetime.combine(today - timedelta(days=days_since_monday), datetime.min.time())
        
        busy_days = set()
        for cal_id in personal_calendar_ids:
            days = cal.get_busy_days(cal_id, week_start)
            busy_days.update(days)
        
        return {"busy_days": sorted(list(busy_days))}
    except Exception as e:
        print(f"Warning: Could not read calendar constraints: {e}")
        return {}


def sync_meal_plan_to_calendar(family_id: str, plan_id: str) -> dict:
    """
    Sync a selected meal plan to the shared Google Calendar.
    Creates dinner events for each day of the plan.
    """
    config = get_family_config(family_id)
    shared_calendar_id = config.get("shared_calendar_id")
    
    if not shared_calendar_id:
        raise ValueError("No shared calendar configured for this family")
    
    # Get the selected plan
    plan = query(
        "SELECT * FROM meal_plans WHERE id = %s AND family_id = %s",
        (plan_id, family_id),
        fetch_one=True
    )
    
    if not plan:
        raise ValueError("Meal plan not found")
    
    plan_data = plan.get("plan", {})
    week_start_date = plan.get("week_start_date")
    
    # Clear existing dinner events for this week
    cal = GoogleCalendarProvider()
    week_start_dt = datetime.combine(week_start_date, datetime.min.time())
    cal.clear_weekly_dinner_events(shared_calendar_id, week_start_dt)
    
    # Create events for each day
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    created_events = []
    
    for i, day_name in enumerate(day_names):
        day_plan = plan_data.get(day_name)
        if day_plan:
            recipe_id = day_plan.get("recipe_id")
            recipe_name = day_plan.get("recipe_name", "Unknown Recipe")
            notes = day_plan.get("notes", "")
            
            # Get recipe details
            recipe = query(
                "SELECT url, ingredients FROM recipes WHERE id = %s",
                (recipe_id,),
                fetch_one=True
            )
            
            event_date = week_start_dt + timedelta(days=i)
            
            event = cal.create_meal_plan_event(
                shared_calendar_id=shared_calendar_id,
                day=day_name,
                date=event_date,
                recipe_name=recipe_name,
                recipe_link=recipe.get("url") if recipe else None,
                ingredients=recipe.get("ingredients") if recipe else None,
                prep_notes=notes
            )
            created_events.append(event)
    
    return {
        "plan_id": str(plan_id),
        "week_start": str(week_start_date),
        "events_created": len(created_events),
        "events": created_events
    }
