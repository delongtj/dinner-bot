import json
from datetime import datetime, timedelta
from psycopg2.extras import Json
from db.connection import query, execute
from llm import get_llm_provider
from handlers.meal_plans import (
    get_family_config,
    get_active_recipes,
    _get_calendar_constraints,
    sync_meal_plan_to_calendar,
)
from grocery.aggregator import aggregate_grocery_list, save_grocery_list


def _build_system_prompt(config, recipes, calendar_constraints, weather, recent_usage):
    """Assemble the system prompt with all pre-loaded context."""
    cuisine_prefs = config.get("cuisine_preferences", [])
    dietary = config.get("dietary_restrictions", [])
    serving_size = config.get("serving_size", 2)
    target_prep = config.get("target_prep_time")

    recipe_list = "\n".join(
        f"- {r['title']} (id: {r['id']}, prep: {r.get('prep_time', '?')}min, "
        f"cuisine: {r.get('cuisine_type', [])}, complexity: {r.get('complexity', '?')})"
        for r in recipes
    )

    busy_days = calendar_constraints.get("busy_days", [])
    busy_section = (
        f"Busy days this week (suggest quick meals): {', '.join(busy_days)}"
        if busy_days
        else "No unusually busy days this week."
    )

    weather_section = "Weather data not available."
    if weather and weather.get("forecast"):
        lines = []
        for day in weather["forecast"]:
            lines.append(
                f"  {day['day']} ({day['date']}): {day.get('condition', '?')}, "
                f"high {day.get('high_f', '?')}°F / low {day.get('low_f', '?')}°F, "
                f"{day.get('precipitation_chance', '?')}% rain"
            )
        weather_section = f"Weather for {weather.get('location', 'your area')}:\n" + "\n".join(lines)

    recent_section = "No recent recipe usage data."
    if recent_usage:
        recent_names = [r["title"] for r in recent_usage]
        recent_section = f"Recently used recipes (last 3 weeks): {', '.join(recent_names)}"

    return f"""You are a friendly, knowledgeable meal-planning assistant for a family.
Your job is to help them plan dinners for the upcoming week (Monday through Sunday)
by having a collaborative conversation. Suggest recipes from their library, consider
their preferences, calendar, weather, and recent usage to avoid repetition.

FAMILY CONTEXT:
- Serving size: {serving_size}
- Cuisine preferences: {', '.join(cuisine_prefs) if cuisine_prefs else 'No specific preferences'}
- Dietary restrictions: {', '.join(dietary) if dietary else 'None'}
- Target prep time: {f'{target_prep} minutes' if target_prep else 'No limit'}

RECIPE LIBRARY:
{recipe_list if recipe_list else 'No recipes in library yet.'}

CALENDAR:
{busy_section}

WEATHER:
{weather_section}

RECENT USAGE:
{recent_section}

GUIDELINES:
- Be conversational and warm, not robotic.
- Proactively suggest a full week but be flexible when they want changes.
- On busy days, lean toward quick/simple recipes.
- In cold/rainy weather, suggest comfort food; in hot weather, suggest lighter fare.
- Avoid recipes used in the last 2 weeks unless requested.
- When the user seems satisfied with the plan, summarize the final week and ask them to confirm.
"""


def create_session(family_id: str) -> dict:
    """
    Start a new interactive planning session.

    Pre-loads family context (config, recipes, calendar, weather, recent usage),
    makes an initial LLM call for a greeting, and stores the session.
    """
    config = get_family_config(family_id)
    if not config:
        raise ValueError("Family config not found. Please set up config first.")

    recipes = get_active_recipes(family_id)
    calendar_constraints = _get_calendar_constraints(config)

    # Weather forecast
    weather = {}
    zip_code = config.get("zip_code")
    if zip_code:
        try:
            from weather.open_meteo import get_weekly_forecast
            weather = get_weekly_forecast(zip_code)
        except Exception as e:
            print(f"Warning: Could not fetch weather: {e}")

    # Recent recipe usage (last 3 weeks)
    three_weeks_ago = datetime.now() - timedelta(weeks=3)
    recent_usage = query(
        """
        SELECT DISTINCT r.title
        FROM recipe_usage ru
        JOIN recipes r ON r.id = ru.recipe_id
        WHERE ru.planned_at >= %s
        ORDER BY r.title
        """,
        (three_weeks_ago,),
    )

    system_prompt = _build_system_prompt(
        config, recipes, calendar_constraints, weather, recent_usage
    )

    # Initial LLM greeting
    llm = get_llm_provider()
    initial_messages = [{"role": "user", "content": "Let's plan meals for this week!"}]
    greeting = llm.chat_plan(system_prompt, initial_messages)

    messages = [
        {
            "role": "assistant",
            "content": greeting,
            "timestamp": datetime.now().isoformat(),
        }
    ]

    context = {
        "calendar_constraints": calendar_constraints,
        "weather": weather,
        "recipe_count": len(recipes),
    }

    # Store session
    sql = """
        INSERT INTO planning_sessions (family_id, messages, context, status)
        VALUES (%s, %s, %s, 'active')
        RETURNING id, created_at
    """
    result = query(sql, (family_id, Json(messages), Json(context)), fetch_one=True)

    return {
        "session_id": str(result["id"]),
        "messages": messages,
        "context": context,
    }


def chat(session_id: str, user_message: str) -> dict:
    """
    Process a conversational turn in a planning session.
    """
    session = query(
        "SELECT * FROM planning_sessions WHERE id = %s",
        (session_id,),
        fetch_one=True,
    )
    if not session:
        raise ValueError("Planning session not found")
    if session["status"] != "active":
        raise ValueError(f"Session is {session['status']}, cannot chat")

    family_id = str(session["family_id"])
    messages = session.get("messages", [])

    # Append user message
    messages.append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now().isoformat(),
    })

    # Rebuild system prompt for this turn
    config = get_family_config(family_id)
    recipes = get_active_recipes(family_id)
    calendar_constraints = session.get("context", {}).get("calendar_constraints", {})
    weather = session.get("context", {}).get("weather", {})

    three_weeks_ago = datetime.now() - timedelta(weeks=3)
    recent_usage = query(
        """
        SELECT DISTINCT r.title
        FROM recipe_usage ru
        JOIN recipes r ON r.id = ru.recipe_id
        WHERE ru.planned_at >= %s
        ORDER BY r.title
        """,
        (three_weeks_ago,),
    )

    system_prompt = _build_system_prompt(
        config, recipes, calendar_constraints, weather, recent_usage
    )

    # LLM call (strip timestamps for the LLM — only role + content)
    llm_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    llm = get_llm_provider()
    reply = llm.chat_plan(system_prompt, llm_messages)

    # Append assistant reply
    messages.append({
        "role": "assistant",
        "content": reply,
        "timestamp": datetime.now().isoformat(),
    })

    # Update session
    execute(
        """
        UPDATE planning_sessions
        SET messages = %s, updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (Json(messages), session_id),
    )

    return {
        "session_id": session_id,
        "message": {"role": "assistant", "content": reply},
    }


def finalize_session(session_id: str, family_id: str) -> dict:
    """
    Finalize a planning session: extract plan, save meal plan, generate
    grocery list, sync calendar, record usage.
    """
    session = query(
        "SELECT * FROM planning_sessions WHERE id = %s",
        (session_id,),
        fetch_one=True,
    )
    if not session:
        raise ValueError("Planning session not found")
    if session["status"] != "active":
        raise ValueError(f"Session is {session['status']}, cannot finalize")

    config = get_family_config(family_id)
    recipes = get_active_recipes(family_id)
    messages = session.get("messages", [])

    # Build system prompt for extraction
    calendar_constraints = session.get("context", {}).get("calendar_constraints", {})
    weather = session.get("context", {}).get("weather", {})
    recent_usage = []
    system_prompt = _build_system_prompt(
        config, recipes, calendar_constraints, weather, recent_usage
    )

    # Extract structured plan from conversation
    llm_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    llm = get_llm_provider()
    plan_data = llm.extract_plan_from_conversation(system_prompt, llm_messages, recipes)

    # Save meal plan
    today = datetime.now().date()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    week_start = today + timedelta(days=days_until_monday)

    plan_result = query(
        """
        INSERT INTO meal_plans (family_id, week_start_date, plan, finalized, finalized_at)
        VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP)
        RETURNING id, created_at
        """,
        (family_id, week_start, Json(plan_data)),
        fetch_one=True,
    )
    plan_id = str(plan_result["id"])

    # Link session to meal plan, mark finalized
    execute(
        """
        UPDATE planning_sessions
        SET meal_plan_id = %s, status = 'finalized', updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (plan_id, session_id),
    )

    # Sync to Google Calendar
    calendar_result = None
    try:
        calendar_result = sync_meal_plan_to_calendar(family_id, plan_id)
    except Exception as e:
        print(f"Warning: Calendar sync failed: {e}")
        calendar_result = {"error": str(e)}

    # Generate grocery list
    grocery_list = aggregate_grocery_list(plan_data)
    grocery_result = save_grocery_list(plan_id, grocery_list)

    # Record recipe usage
    for day, entry in plan_data.items():
        recipe_id = entry.get("recipe_id")
        if recipe_id:
            try:
                execute(
                    "INSERT INTO recipe_usage (recipe_id, planned_at) VALUES (%s, %s)",
                    (recipe_id, week_start),
                )
            except Exception:
                pass  # Non-critical — don't fail the finalize

    return {
        "plan_id": plan_id,
        "plan": plan_data,
        "grocery_list": grocery_result,
        "calendar_sync": calendar_result,
    }


def abandon_session(session_id: str) -> dict:
    """Mark a planning session as abandoned."""
    session = query(
        "SELECT id, status FROM planning_sessions WHERE id = %s",
        (session_id,),
        fetch_one=True,
    )
    if not session:
        raise ValueError("Planning session not found")
    if session["status"] != "active":
        raise ValueError(f"Session is already {session['status']}")

    execute(
        """
        UPDATE planning_sessions
        SET status = 'abandoned', updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """,
        (session_id,),
    )

    return {"session_id": session_id, "status": "abandoned"}
