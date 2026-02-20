-- Drop existing tables if they exist
DROP TABLE IF EXISTS grocery_lists;
DROP TABLE IF EXISTS planning_sessions;
DROP TABLE IF EXISTS meal_plans;
DROP TABLE IF EXISTS recipe_usage;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS family_config;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS families;

-- Families (top-level entity)
CREATE TABLE families (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Users (minimal - just auth + family membership)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  email TEXT NOT NULL UNIQUE,
  name TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Family configuration
CREATE TABLE family_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id UUID NOT NULL UNIQUE REFERENCES families(id) ON DELETE CASCADE,

  -- Google Calendar
  personal_calendar_ids TEXT[] DEFAULT '{}',
  shared_calendar_id TEXT,
  calendar_sync_token TEXT,

  -- Preferences
  cuisine_preferences TEXT[] DEFAULT '{}',
  dietary_restrictions TEXT[] DEFAULT '{}',
  target_prep_time INT,
  serving_size INT DEFAULT 2,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Recipes
CREATE TABLE recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,

  url TEXT,
  title TEXT NOT NULL,
  prep_time INT,
  cook_time INT,
  servings INT DEFAULT 2,

  -- Structured ingredients for grocery list aggregation
  -- Format: [{name, quantity, unit, category}]
  ingredients JSONB DEFAULT '[]',
  instructions TEXT,

  -- Semantic tags
  cuisine_type TEXT[] DEFAULT '{}',
  meal_type TEXT DEFAULT 'dinner',
  complexity TEXT DEFAULT 'moderate',
  dietary_flags TEXT[] DEFAULT '{}',
  seasonal_relevance TEXT DEFAULT 'any',

  rating INT,
  active BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Recipe usage history
CREATE TABLE recipe_usage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
  planned_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Meal plans
CREATE TABLE meal_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,

  week_start_date DATE NOT NULL,
  plan JSONB NOT NULL,

  finalized BOOLEAN DEFAULT FALSE,
  finalized_at TIMESTAMP,

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Planning sessions (tracks the interactive chat for a planning session)
CREATE TABLE planning_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE SET NULL,

  messages JSONB DEFAULT '[]',
  context JSONB DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'active',

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),

  CONSTRAINT valid_status CHECK (status IN ('active', 'finalized', 'abandoned'))
);

-- Grocery lists (generated from a finalized meal plan)
CREATE TABLE grocery_lists (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  meal_plan_id UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,

  -- Format: [{name, quantity, unit, category, recipe_source}]
  items JSONB DEFAULT '[]',

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_family_id ON users(family_id);
CREATE INDEX idx_recipes_family_id ON recipes(family_id);
CREATE INDEX idx_recipes_active ON recipes(family_id, active) WHERE active = TRUE;
CREATE INDEX idx_recipe_usage_recipe_id ON recipe_usage(recipe_id);
CREATE INDEX idx_recipe_usage_planned_at ON recipe_usage(planned_at);
CREATE INDEX idx_meal_plans_family_id ON meal_plans(family_id);
CREATE INDEX idx_meal_plans_week_start ON meal_plans(week_start_date);
CREATE INDEX idx_planning_sessions_family_id ON planning_sessions(family_id);
CREATE INDEX idx_planning_sessions_status ON planning_sessions(family_id, status) WHERE status = 'active';
CREATE INDEX idx_grocery_lists_meal_plan_id ON grocery_lists(meal_plan_id);
