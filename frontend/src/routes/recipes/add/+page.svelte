<script lang="ts">
	import { goto } from '$app/navigation';
	import { addRecipeByUrl } from '$lib/api/client';
	import type { Recipe } from '$lib/api/types';

	let url = $state('');
	let loading = $state(false);
	let error = $state('');
	let result = $state<Recipe | null>(null);

	async function handleSubmit() {
		if (!url.trim()) return;
		loading = true;
		error = '';
		result = null;
		try {
			const { recipe } = await addRecipeByUrl(url.trim());
			result = recipe;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to import recipe';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Add Recipe - DinnerBot</title>
</svelte:head>

<div class="mb-6 flex items-center gap-4">
	<a href="/recipes" class="text-sm text-stone-400 hover:text-stone-600">&larr; Recipes</a>
	<h1 class="text-2xl font-bold text-stone-800">Add Recipe</h1>
</div>

{#if !result}
	<div class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
		<p class="mb-4 text-sm text-stone-500">
			Paste a recipe URL and we'll extract the title, ingredients, and instructions automatically.
		</p>
		<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="flex gap-3">
			<input
				type="url"
				bind:value={url}
				placeholder="https://www.example.com/recipe/..."
				disabled={loading}
				class="flex-1 rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
			/>
			<button
				type="submit"
				disabled={loading || !url.trim()}
				class="rounded-md bg-amber-500 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
			>
				{loading ? 'Importing...' : 'Import'}
			</button>
		</form>
		{#if loading}
			<div class="mt-4 flex items-center gap-2 text-sm text-stone-500">
				<div class="h-4 w-4 animate-spin rounded-full border-2 border-stone-300 border-t-amber-500"></div>
				Extracting recipe — this may take a moment...
			</div>
		{/if}
		{#if error}
			<p class="mt-4 text-sm text-red-600">{error}</p>
		{/if}
	</div>
{:else}
	<div class="rounded-lg border border-green-200 bg-green-50 p-6 shadow-sm">
		<div class="mb-4 flex items-center justify-between">
			<h2 class="text-lg font-semibold text-stone-800">Recipe added!</h2>
			<div class="flex gap-2">
				<button
					onclick={() => { url = ''; result = null; }}
					class="rounded-md bg-white px-4 py-2 text-sm font-medium text-stone-700 shadow-sm transition-colors hover:bg-stone-50"
				>
					Add Another
				</button>
				<button
					onclick={() => goto('/recipes')}
					class="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600"
				>
					View Recipes
				</button>
			</div>
		</div>
		<dl class="grid gap-2 text-sm">
			<div>
				<dt class="font-medium text-stone-600">Title</dt>
				<dd class="text-stone-800">{result.title}</dd>
			</div>
			{#if result.prep_time || result.cook_time}
				<div>
					<dt class="font-medium text-stone-600">Time</dt>
					<dd class="text-stone-800">
						{result.prep_time ? `${result.prep_time}m prep` : ''}
						{result.prep_time && result.cook_time ? ' + ' : ''}
						{result.cook_time ? `${result.cook_time}m cook` : ''}
					</dd>
				</div>
			{/if}
			{#if result.servings}
				<div>
					<dt class="font-medium text-stone-600">Servings</dt>
					<dd class="text-stone-800">{result.servings}</dd>
				</div>
			{/if}
		</dl>
	</div>
{/if}
