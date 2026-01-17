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
  google_calendar_id TEXT,
  calendar_sync_token TEXT,
  
  -- Preferences
  cuisine_preferences TEXT[] DEFAULT '{}',
  dietary_restrictions TEXT[] DEFAULT '{}',
  target_prep_time INT,
  serving_size INT DEFAULT 2,
  
  -- Scheduling
  plan_generation_day TEXT DEFAULT 'Saturday',
  plan_generation_time TEXT DEFAULT '18:00',
  
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
  
  ingredients TEXT,
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

-- Meal Plans
CREATE TABLE meal_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  family_id UUID NOT NULL REFERENCES families(id) ON DELETE CASCADE,
  
  week_start_date DATE NOT NULL,
  plan JSONB NOT NULL,
  
  selected BOOLEAN DEFAULT FALSE,
  selected_at TIMESTAMP,
  variant INT DEFAULT 1,
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_family_id ON users(family_id);
CREATE INDEX idx_recipes_family_id ON recipes(family_id);
CREATE INDEX idx_recipes_active ON recipes(active) WHERE active = TRUE;
CREATE INDEX idx_recipe_usage_recipe_id ON recipe_usage(recipe_id);
CREATE INDEX idx_meal_plans_family_id ON meal_plans(family_id);
CREATE INDEX idx_meal_plans_week_start ON meal_plans(week_start_date);
