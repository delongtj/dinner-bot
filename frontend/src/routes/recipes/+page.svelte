<script lang="ts">
	import { listRecipes } from '$lib/api/client';
	import type { Recipe } from '$lib/api/types';

	let recipes = $state<Recipe[]>([]);
	let loading = $state(true);
	let error = $state('');

	async function load() {
		try {
			recipes = await listRecipes();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load recipes';
		} finally {
			loading = false;
		}
	}

	load();

	function complexityColor(c: string): string {
		if (c === 'quick') return 'bg-green-100 text-green-700';
		if (c === 'involved') return 'bg-orange-100 text-orange-700';
		return 'bg-stone-100 text-stone-600';
	}
</script>

<svelte:head>
	<title>Recipes - DinnerBot</title>
</svelte:head>

<div class="mb-6 flex items-center justify-between">
	<h1 class="text-2xl font-bold text-stone-800">Recipes</h1>
	<a
		href="/recipes/add"
		class="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600"
	>
		Add Recipe
	</a>
</div>

{#if loading}
	<div class="flex justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-amber-500"></div>
	</div>
{:else if error}
	<div class="rounded-lg border border-red-200 bg-red-50 p-6">
		<p class="text-sm text-red-600">{error}</p>
	</div>
{:else if recipes.length === 0}
	<div class="rounded-lg border border-stone-200 bg-white p-8 text-center shadow-sm">
		<p class="mb-2 text-stone-500">No recipes yet.</p>
		<a href="/recipes/add" class="text-sm font-medium text-amber-600 hover:text-amber-700">
			Add your first recipe
		</a>
	</div>
{:else}
	<div class="grid gap-3">
		{#each recipes as recipe}
			<div class="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
				<div class="flex items-start justify-between">
					<div>
						<h2 class="font-semibold text-stone-800">{recipe.title}</h2>
						<div class="mt-1 flex flex-wrap gap-2 text-xs">
							{#if recipe.cuisine_type?.length}
								{#each recipe.cuisine_type as c}
									<span class="rounded-full bg-amber-50 px-2 py-0.5 text-amber-700">{c}</span>
								{/each}
							{/if}
							{#if recipe.complexity}
								<span class="rounded-full px-2 py-0.5 {complexityColor(recipe.complexity)}">
									{recipe.complexity}
								</span>
							{/if}
							{#if recipe.dietary_flags?.length}
								{#each recipe.dietary_flags as d}
									<span class="rounded-full bg-blue-50 px-2 py-0.5 text-blue-700">{d}</span>
								{/each}
							{/if}
						</div>
					</div>
					<div class="text-right text-xs text-stone-400">
						{#if recipe.prep_time}
							<span>Prep {recipe.prep_time}m</span>
						{/if}
						{#if recipe.cook_time}
							<span class="ml-2">Cook {recipe.cook_time}m</span>
						{/if}
						{#if recipe.servings}
							<div>Serves {recipe.servings}</div>
						{/if}
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}
