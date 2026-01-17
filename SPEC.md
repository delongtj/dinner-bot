# dinner-bot Specification

## Project Overview

dinner-bot is an AI-powered meal planning agent that streamlines weekly meal planning by:
- Parsing and managing a personal recipe repository
- Reading user calendar data to identify scheduling constraints
- Generating multiple complete weekly meal plans (Mon-Sun)
- Considering seasonal/weather factors and dietary preferences
- Delivering selected recipes to a shared Google Calendar (daily 5:00-6:00 PM dinner events with recipe details)

The system minimizes user friction through ultra-easy recipe intake, simple weekly selection, and leverages Google Calendar for delivery instead of custom email infrastructure.

---

## Goals & Success Criteria

### Primary Goals
1. **Solve a real problem:** Eliminate manual weekly meal planning for the core user(s)
2. **Learn AI/agent skills:** Practice structuring data for LLMs, building multi-tool agent systems
3. **Cheap/sustainable:** Minimal hosting costs; easily monetizable if desired

### MVP Success Criteria
- Recipe intake mechanism working (bookmark or paste-based)
- Calendar integration reading events
- Agent generates 3-4 complete weekly plans
- User selects preferred plan
- Selected plan automatically synced to shared Google Calendar (daily dinner events with recipe details)
- System runs weekly on schedule (Cloud Scheduler or similar)

---

## Data Schema

### Recipe
```
{
  id: string (uuid)
  url: string (original source)
  title: string
  prepTime: number (minutes)
  cookTime: number (minutes)
  servings: number
  ingredients: string[] (raw text for now)
  instructions: string
  
  // Semantic tags (for agent filtering/ranking)
  cuisineType: string[] (e.g., ["Italian", "Asian"])
  mealType: string (lunch | dinner | breakfast)
  complexity: "quick" | "moderate" | "involved"
  dietaryFlags: string[] (vegetarian, keto, dairy-free, etc.)
  seasonalRelevance: "spring" | "summer" | "fall" | "winter" | "any"
  
  // Tracking
  createdAt: timestamp
  usedDates: timestamp[] (when it was planned)
  rating: 1-5 (optional user feedback after cooking)
  lastPlanned: timestamp
  active: boolean
}
```

### MealPlan
```
{
  id: string (uuid)
  weekStartDate: date
  generated: timestamp
  plan: {
    [dayOfWeek]: {
      recipeName: string
      recipeId: string
      notes: string (optional)
    }
  }
  selected: boolean
  selectedAt: timestamp
  variant: number (1-4, for plan A/B/C/D)
}
```

### User/Config
```
{
  userId: string
  email: string
  
  // Calendar integration
  googleCalendarId: string
  calendarSyncToken: string (incremental sync)
  
  // Preferences
  cuisinePreferences: string[]
  dietaryRestrictions: string[]
  targetPrepTime: number (max minutes willing to prep)
  servingSize: number (number of people)
  
  // Scheduling
  planGenerationDay: string (e.g., "Saturday")
  planGenerationTime: string (e.g., "18:00")
  recipeEmailTime: string (e.g., "08:00")
  
  // Recipe intake settings
  recipeSourcePreferences: {
    allowedDomains: string[]
    parsingHints: object
  }
}
```

---

## Architecture

### Components

1. **Backend (Python + FastAPI)**
   - Recipe management (CRUD, metadata extraction)
   - Calendar polling (Google Calendar API)
   - Agent orchestration (Claude API calls)
   - Email delivery
   - Scheduled job runner

2. **Database (PostgreSQL)**
   - Recipes
   - Meal plans
   - User settings
   - Planning history

3. **Frontend (Optional MVP, maybe Svelte/Vue)**
   - Recipe intake UI (paste URL, parse, confirm metadata)
   - Weekly plan selector (view 3-4 options, pick one)
   - Simple recipe management (add/remove/edit)
   - Settings dashboard

4. **Integrations**
    - Google Calendar API (read events for constraints, write dinner events with recipes)
    - Claude API (plan generation, recipe metadata extraction)
    - Cloud Scheduler or APScheduler (weekly triggers)

### Deployment
- Backend: Google Cloud Functions (Python, serverless)
- Database: Supabase (PostgreSQL)
- Frontend: Cloud Storage + Cloud CDN (static Svelte build)
- Scheduler: Google Cloud Scheduler (free tier)
- Google Calendar: Shared calendar (free)
- Cost estimate: ~$0 (free tiers only, except optional Supabase overage)

---

## Agent Logic (High-Level)

### Weekly Plan Generation

**Input:**
- User preferences (dietary, cuisine, max prep time)
- Recent recipe history (avoid repetition)
- Calendar events for the week (identify quick/slow-cooker days)
- Current season/weather

**Process:**
1. Filter recipes by:
   - User dietary/cuisine preferences
   - Seasonal relevance
   - Complexity vs. calendar constraints
2. Rank by:
   - Variety (cuisine, proteins, prep methods)
   - Recency (don't repeat recent meals)
   - Calendar fit (quick meals on busy days)
3. Generate 4 complete plans (Mon-Sun) respecting constraints
4. Return all 4 to user with brief reasoning

**Output:**
- 4 complete MealPlan objects with diversity in approach

### Recipe Metadata Extraction

**Input:** URL or recipe text

**Process:**
1. Fetch page content
2. Use Claude (or simpler parser) to extract:
   - Title, prep time, cook time, servings
   - Ingredients list
   - Instructions
   - Infer: cuisine type, complexity, dietary flags
3. Manual override option if parsing weak

**Output:** Recipe object ready for storage

---

## User Workflows

### 1. Recipe Intake (Frictionless)
- User finds recipe online
- Uses bookmarklet/browser extension → paste URL
- Agent extracts metadata, shows preview
- User confirms or manually adjusts tags
- Saved to recipe repository

### 2. Weekly Planning
- Saturday evening: Agent generates 4 meal plans
- User reviews 3-4 options (presented in UI or email preview)
- User selects preferred plan (1 click/tap)
- Plan locked in

### 3. Daily Delivery
- Selected plan synced to shared Google Calendar
- Each day: 5:00-6:00 PM dinner event created with recipe details (title, link, ingredients, prep notes) in event description
- Google Calendar sends 6 AM email reminder to all subscribers (built-in Google Calendar reminder)

---

## MVP Scope (Phase 1)

**Exclude from MVP:**
- Grocery integration / sale tracking
- Advanced feedback loop ("I'm tired of chili")
- Recipe rating system
- Multi-user support initially (single service account per household)
- Frontend "nice-to-haves"
- OAuth support (use service account for MVP)

**Include in MVP:**
- Recipe CRUD + basic metadata
- Calendar integration (read events for constraints, write dinner events)
- Agent-driven plan generation (3-4 options)
- Plan selection mechanism
- Google Calendar event creation with recipe details + reminder setup
- Weekly scheduler

---

## Tech Stack (Finalized)

**Backend:** Python (Cloud Functions)
**Database:** Supabase (PostgreSQL)
**LLM:** Gemini API (free tier, abstraction layer for provider swapping)
**Calendar:** Google Calendar API (read events + write dinner events)
**Scheduling:** Google Cloud Scheduler
**Frontend:** Svelte (static build on Cloud Storage + CDN)
**Deployment:** GCP-centric (Cloud Functions, Cloud Storage, Cloud Scheduler)

---

## Timeline Estimate

- **Week 1-2:** Schema design, DB setup, basic API scaffolding
- **Week 3-4:** Recipe intake + parsing, calendar integration
- **Week 5-6:** Agent logic, plan generation
- **Week 7-8:** Email delivery, scheduler, testing
- **Week 9:** Frontend polish, documentation
- **Target:** ~2 months for functional MVP

---

## Future Enhancements (Post-MVP)

1. Grocery integration (Publix, Aldi scraping or APIs)
2. Smart suggestions based on sales
3. Meal prep planning (ingredient prep schedule)
4. Multi-user/family management
5. Recipe rating system + continuous learning
6. Dietary tracking (macros, micronutrients)
7. Mobile app
8. Monetization (SaaS subscription, managed hosting)

---

## Notes

- Start with manual recipe data entry for first 10-20 recipes to validate concept
- Keep agent prompts simple and focused initially; iterate
- Log agent reasoning for debugging and learning
- Plan for calendar sync edge cases (deleted events, time changes)
