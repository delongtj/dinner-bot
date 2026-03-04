import { auth } from '$lib/firebase';
const PUBLIC_API_BASE_URL = import.meta.env.PUBLIC_API_BASE_URL ?? '';
import type {
	Recipe,
	PlanningSession,
	ChatMessage,
	MealPlan,
	GroceryList,
	FamilyConfig,
	UserInfo
} from './types';

async function getHeaders(): Promise<HeadersInit> {
	const token = await auth?.currentUser?.getIdToken();
	return {
		'Content-Type': 'application/json',
		...(token ? { Authorization: `Bearer ${token}` } : {})
	};
}

class ApiError extends Error {
	status: number;
	constructor(message: string, status: number) {
		super(message);
		this.status = status;
	}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
	const headers = await getHeaders();
	const res = await fetch(`${PUBLIC_API_BASE_URL}${path}`, {
		...options,
		headers: { ...headers, ...(options.headers || {}) }
	});

	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw new ApiError(body.error || `Request failed: ${res.status}`, res.status);
	}

	return res.json();
}

export { ApiError };

// User & Registration
export function getMe(): Promise<UserInfo> {
	return request('/me');
}

export function register(name?: string, inviteCode?: string): Promise<UserInfo> {
	return request('/register', {
		method: 'POST',
		body: JSON.stringify({ name, invite_code: inviteCode })
	});
}

export function createInvite(): Promise<{ code: string; expires_at: string }> {
	return request('/create_invite', {
		method: 'POST',
		body: JSON.stringify({})
	});
}

// Recipes
export function listRecipes(): Promise<Recipe[]> {
	return request('/list_recipes');
}

export function addRecipeByUrl(url: string): Promise<{ recipe: Recipe }> {
	return request('/add_recipe', {
		method: 'POST',
		body: JSON.stringify({ url })
	});
}

export function addRecipeManual(data: Partial<Recipe>): Promise<{ recipe: Recipe }> {
	return request('/add_recipe', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

// Planning
export function createPlanningSession(): Promise<PlanningSession> {
	return request('/create_planning_session', {
		method: 'POST',
		body: JSON.stringify({})
	});
}

export function sendPlanningMessage(
	sessionId: string,
	message: string
): Promise<{ session_id: string; message: ChatMessage }> {
	return request('/planning_chat', {
		method: 'POST',
		body: JSON.stringify({ session_id: sessionId, message })
	});
}

export function finalizePlan(
	sessionId: string
): Promise<{ plan_id: string; plan: Record<string, unknown>; grocery_list: unknown; calendar_sync: unknown }> {
	return request('/finalize_plan', {
		method: 'POST',
		body: JSON.stringify({ session_id: sessionId })
	});
}

export function abandonPlan(sessionId: string): Promise<{ session_id: string; status: string }> {
	return request('/abandon_plan', {
		method: 'POST',
		body: JSON.stringify({ session_id: sessionId })
	});
}

// Config
export function getConfig(): Promise<{ config: FamilyConfig | null }> {
	return request('/get_config');
}

export function setupConfig(config: Partial<FamilyConfig>): Promise<{ config: FamilyConfig }> {
	return request('/setup_config', {
		method: 'POST',
		body: JSON.stringify(config)
	});
}

// Grocery
export function getGroceryList(): Promise<{ grocery_list: GroceryList | null }> {
	return request('/get_grocery');
}
