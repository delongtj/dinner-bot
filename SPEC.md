# dinner-bot Specification

## Project Overview

dinner-bot is an AI-assisted meal planning tool that streamlines weekly dinner planning through an interactive chat experience. The user drives the process — the AI handles the tedious parts (pulling calendar/weather context, managing the recipe library, generating consolidated ingredient lists).

Core value props:
- **Interactive planning:** Conversational back-and-forth to build a weekly meal plan, not a take-it-or-leave-it generated plan
- **Context-aware suggestions:** Calendar events and weather pre-loaded so the AI can suggest appropriately (quick meals on busy nights, comfort food when it's cold)
- **Consolidated grocery list:** The real pain point — once the plan is locked, automatically aggregate and deduplicate ingredients across all recipes
- **Effortless daily reminders:** Google Calendar events with full recipe details, so Google's built-in reminders deliver the recipe each morning

---

## Goals & Success Criteria

### Primary Goals
1. **Solve a real problem:** Make weekly meal planning faster and less painful for the core user(s)
2. **Learn AI/agent skills:** Practice structuring data for LLMs, building conversational agent systems
3. **Cheap/sustainable:** Minimal hosting costs; easily monetizable if desired

### MVP Success Criteria
- Recipe intake mechanism working (paste URL, AI extracts metadata)
- Calendar + weather context pre-loaded into planning sessions
- Interactive chat-based planning flow (user and AI collaborate on the week's plan)
- Finalized plan creates Google Calendar dinner events with recipe details
- Consolidated ingredient list generated from finalized plan
- Morning recipe reminders working via Google Calendar's built-in notifications

---

## Data Schema

### Family
Top-level entity enabling spouse/family collaboration
```
{
  id: uuid
  name: string
  created_at: timestamp
  updated_at: timestamp
}
```

### User
Minimal auth + family membership
```
{
  id: uuid
  family_id: uuid (FK to Family)
  email: string (unique)
  name: string
  created_at: timestamp
  updated_at: timestamp
}
```

### FamilyConfig
Shared configuration per family
```
{
  id: uuid
  family_id: uuid (unique FK to Family)
  google_calendar_id: string
  calendar_sync_token: string
  cuisine_preferences: string[]
  dietary_restrictions: string[]
  target_prep_time: number (minutes)
  serving_size: number
  created_at: timestamp
  updated_at: timestamp
}
```

### Recipe
```
{
  id: uuid
  family_id: uuid (FK to Family)
  url: string
  title: string
  prep_time: number (minutes)
  cook_time: number (minutes)
  servings: number
  ingredients: jsonb (structured list: [{name, quantity, unit, category}])
  instructions: string
  cuisine_type: string[]
  meal_type: string (breakfast | lunch | dinner)
  complexity: string (quick | moderate | involved)
  dietary_flags: string[]
  seasonal_relevance: string (spring | summer | fall | winter | any)
  rating: number (1-5, optional)
  active: boolean
  created_at: timestamp
  updated_at: timestamp
}
```

### RecipeUsage
History of when recipes were planned
```
{
  id: uuid
  recipe_id: uuid (FK to Recipe)
  planned_at: timestamp
  created_at: timestamp
}
```

### MealPlan
```
{
  id: uuid
  family_id: uuid (FK to Family)
  week_start_date: date
  plan: jsonb { "Monday": { "recipe_id": "...", "recipe_name": "...", "notes": "..." }, ... }
  finalized: boolean
  finalized_at: timestamp
  created_at: timestamp
  updated_at: timestamp
}
```

### GroceryList
Generated from a finalized MealPlan
```
{
  id: uuid
  meal_plan_id: uuid (FK to MealPlan)
  items: jsonb [{name, quantity, unit, category, recipe_source}]
  created_at: timestamp
  updated_at: timestamp
}
```

### PlanningSession
Tracks the chat conversation for a planning session
```
{
  id: uuid
  family_id: uuid (FK to Family)
  meal_plan_id: uuid (FK to MealPlan, nullable until plan is created)
  messages: jsonb [{role, content, timestamp}]
  context: jsonb {calendar_events, weather, recent_recipes}
  status: string (active | finalized | abandoned)
  created_at: timestamp
  updated_at: timestamp
}
```

---

## Architecture

### Components

1. **Backend (Python + FastAPI)**
   - Recipe management (CRUD, metadata extraction via LLM)
   - Calendar polling (Google Calendar API)
   - Weather fetching
   - Chat endpoint (streams LLM responses, manages planning session state)
   - Grocery list aggregation
   - Google Calendar event creation

2. **Database (PostgreSQL via NeonDB)**
   - Families, Users, FamilyConfig
   - Recipes, RecipeUsage
   - MealPlans, GroceryLists
   - PlanningSessions

3. **Frontend (Svelte)**
   - Chat interface for meal planning sessions
   - Recipe intake UI (paste URL, review extracted metadata, confirm)
   - Recipe library browser
   - Grocery list view (grouped by category, copy-friendly)
   - Settings page

4. **Integrations**
   - Google Calendar API (read events for context, write dinner events)
   - Weather API (forecast for the planning week)
   - LLM API (conversational planning, recipe metadata extraction)

### Deployment
- Backend: Google Cloud Functions (Python, serverless)
- Database: NeonDB (PostgreSQL, free tier)
- Frontend: Cloud Storage + Cloud CDN (static Svelte build)
- Google Calendar: Shared calendar (free)
- Cost estimate: ~$0 (free tiers only)

---

## Agent Logic (High-Level)

### Planning Session

When the user starts a planning session, the backend:

1. **Pre-loads context:**
   - Fetches Google Calendar events for the upcoming week
   - Fetches weather forecast for the week
   - Queries recent recipe usage (last 3-4 weeks) to avoid repetition
   - Loads family preferences (dietary restrictions, cuisine preferences, serving size)
   - Loads the full recipe library (or at least active recipes)

2. **Assembles system prompt** with all the above context, plus instructions to be a collaborative meal planning assistant (not a plan-generator-in-a-box)

3. **Streams a conversational response** — the LLM opens with observations about the week ("Looks like a busy Tuesday, rainy Thursday...") and some initial suggestions

4. **User iterates** — swaps meals, adds constraints ("we have leftover chicken"), requests specific recipes, etc.

5. **User finalizes** — triggers plan lock-in, which:
   - Saves the MealPlan
   - Creates Google Calendar events (daily 5:00-6:00 PM dinner slots with recipe details in the description)
   - Generates the consolidated GroceryList
   - Records RecipeUsage entries

### Recipe Metadata Extraction

**Input:** URL or recipe text

**Process:**
1. Fetch page content
2. Use LLM to extract:
   - Title, prep time, cook time, servings
   - Structured ingredients list (name, quantity, unit, category)
   - Instructions
   - Infer: cuisine type, complexity, dietary flags
3. User reviews and adjusts before saving

**Output:** Recipe object ready for storage

### Grocery List Generation

**Input:** Finalized MealPlan (list of recipe IDs)

**Process:**
1. Pull structured ingredients from each recipe
2. Normalize units where possible (e.g., 4 tbsp butter + 2 tbsp butter = 6 tbsp butter)
3. Deduplicate common pantry items
4. Group by category (produce, protein, dairy, pantry, etc.)

**Output:** GroceryList object, rendered in the UI grouped by category

---

## User Workflows

### 1. Recipe Intake
- User finds recipe online
- Pastes URL into the app
- AI extracts metadata, shows structured preview
- User confirms or adjusts
- Saved to recipe library

### 2. Weekly Planning (Interactive)
- User opens the app and starts a new planning session
- System pre-loads calendar, weather, recipe history, preferences
- AI opens with context-aware suggestions
- User and AI go back and forth until the plan feels right
- User hits "Lock it in" to finalize
- Calendar events created, grocery list generated

### 3. Grocery List
- Generated automatically when a plan is finalized
- Ingredients aggregated and deduplicated across all recipes for the week
- Grouped by category (produce, dairy, protein, pantry, etc.)
- Copyable / shareable from the UI

### 4. Daily Delivery
- Finalized plan synced to shared Google Calendar
- Each day: 5:00-6:00 PM dinner event with recipe details (title, link, ingredients, instructions) in event description
- Google Calendar sends morning email reminder to all calendar subscribers

---

## MVP Scope (Phase 1)

**Include in MVP:**
- Recipe CRUD + LLM-powered metadata extraction from URLs
- Google Calendar integration (read events for context, write dinner events)
- Weather API integration
- Interactive chat-based planning session
- Plan finalization → calendar sync
- Consolidated grocery list generation
- Svelte frontend (chat UI, recipe library, grocery list view)

**Exclude from MVP:**
- Store-specific grocery list splitting (Publix vs. Aldi)
- Grocery store API/app integration
- Advanced feedback loop ("I'm tired of chili")
- Recipe rating system
- Multi-user auth (single service account per household for MVP)
- OAuth (use service account for MVP)

---

## Tech Stack

**Backend:** Python (Cloud Functions)
**Database:** NeonDB (PostgreSQL, free tier)
**LLM:** Gemini API (free tier, abstraction layer for provider swapping)
**Calendar:** Google Calendar API (read events + write dinner events)
**Weather:** Open-Meteo or similar free weather API
**Frontend:** Svelte (static build on Cloud Storage + CDN)
**Deployment:** GCP-centric (Cloud Functions, Cloud Storage)

---

## Future Enhancements (Post-MVP)

1. Store-specific grocery list splitting (Publix vs. Aldi based on item category mapping)
2. Grocery store app integration (share lists directly if APIs become available)
3. Smart suggestions based on grocery sales/flyers
4. Meal prep planning (ingredient prep schedule)
5. Multi-user auth and family management
6. Recipe rating system + learning from preferences over time
7. Pantry tracking (skip items you already have)
8. Mobile app / PWA
9. Monetization (SaaS subscription)

---

## Notes

- Start with manual recipe data entry for first 10-20 recipes to validate the concept
- Structured ingredients (`[{name, quantity, unit, category}]`) are critical — the grocery list feature depends on good ingredient parsing
- Keep agent prompts simple and focused initially; iterate based on real planning sessions
- Log planning session conversations for debugging and prompt improvement
- Plan for calendar sync edge cases (deleted events, time changes, re-planning mid-week)
