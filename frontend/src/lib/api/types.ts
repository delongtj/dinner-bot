export interface Recipe {
	id: string;
	family_id: string;
	url: string | null;
	title: string;
	prep_time: number | null;
	cook_time: number | null;
	servings: number;
	ingredients: Ingredient[];
	instructions: string | null;
	cuisine_type: string[];
	meal_type: string;
	complexity: string;
	dietary_flags: string[];
	seasonal_relevance: string;
	rating: number | null;
	active: boolean;
	created_at: string;
	updated_at: string;
}

export interface Ingredient {
	name: string;
	quantity: number | null;
	unit: string | null;
	category: string | null;
}

export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	timestamp?: string;
}

export interface PlanningSession {
	id: string;
	family_id: string;
	meal_plan_id: string | null;
	messages: ChatMessage[];
	context: Record<string, unknown>;
	status: 'active' | 'finalized' | 'abandoned';
	created_at: string;
	updated_at: string;
}

export interface GroceryItem {
	name: string;
	quantity: number | null;
	unit: string | null;
	category: string | null;
	recipe_source: string | null;
}

export interface GroceryList {
	id: string;
	meal_plan_id: string;
	items: GroceryItem[];
	created_at: string;
	updated_at: string;
}

export interface MealPlan {
	id: string;
	family_id: string;
	week_start_date: string;
	plan: Record<string, unknown>;
	finalized: boolean;
	finalized_at: string | null;
	created_at: string;
	updated_at: string;
}

export interface FamilyConfig {
	id: string;
	family_id: string;
	personal_calendar_ids: string[];
	shared_calendar_id: string | null;
	zip_code: string | null;
	cuisine_preferences: string[];
	dietary_restrictions: string[];
	target_prep_time: number | null;
	serving_size: number;
	created_at: string;
	updated_at: string;
}
