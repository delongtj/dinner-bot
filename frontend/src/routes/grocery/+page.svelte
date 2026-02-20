<script lang="ts">
	import { getGroceryList } from '$lib/api/client';
	import type { GroceryItem } from '$lib/api/types';

	let items = $state<GroceryItem[]>([]);
	let loading = $state(true);
	let error = $state('');
	let copied = $state(false);

	async function load() {
		try {
			const { grocery_list } = await getGroceryList();
			items = grocery_list?.items ?? [];
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load grocery list';
		} finally {
			loading = false;
		}
	}

	load();

	function groupByCategory(items: GroceryItem[]): Record<string, GroceryItem[]> {
		const groups: Record<string, GroceryItem[]> = {};
		for (const item of items) {
			const cat = item.category || 'Other';
			if (!groups[cat]) groups[cat] = [];
			groups[cat].push(item);
		}
		return groups;
	}

	function formatItem(item: GroceryItem): string {
		const parts: string[] = [];
		if (item.quantity) parts.push(String(item.quantity));
		if (item.unit) parts.push(item.unit);
		parts.push(item.name);
		return parts.join(' ');
	}

	function copyList() {
		const grouped = groupByCategory(items);
		const text = Object.entries(grouped)
			.map(([cat, catItems]) => {
				const lines = catItems.map((i) => `  - ${formatItem(i)}`).join('\n');
				return `${cat}:\n${lines}`;
			})
			.join('\n\n');

		navigator.clipboard.writeText(text);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<svelte:head>
	<title>Grocery List - DinnerBot</title>
</svelte:head>

<div class="mb-6 flex items-center justify-between">
	<h1 class="text-2xl font-bold text-stone-800">Grocery List</h1>
	{#if items.length > 0}
		<button
			onclick={copyList}
			class="rounded-md bg-stone-700 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-stone-600"
		>
			{copied ? 'Copied!' : 'Copy List'}
		</button>
	{/if}
</div>

{#if loading}
	<div class="flex justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-amber-500"></div>
	</div>
{:else if error}
	<div class="rounded-lg border border-red-200 bg-red-50 p-6">
		<p class="text-sm text-red-600">{error}</p>
	</div>
{:else if items.length === 0}
	<div class="rounded-lg border border-stone-200 bg-white p-8 text-center shadow-sm">
		<p class="mb-2 text-stone-500">No grocery list yet.</p>
		<p class="text-sm text-stone-400">Finalize a meal plan to generate one.</p>
	</div>
{:else}
	{@const grouped = groupByCategory(items)}
	<div class="space-y-4">
		{#each Object.entries(grouped) as [category, catItems]}
			<div class="rounded-lg border border-stone-200 bg-white p-4 shadow-sm">
				<h2 class="mb-2 text-sm font-semibold uppercase tracking-wide text-stone-500">{category}</h2>
				<ul class="space-y-1">
					{#each catItems as item}
						<li class="flex items-baseline justify-between text-sm">
							<span class="text-stone-800">{item.name}</span>
							<span class="ml-4 text-stone-400">
								{#if item.quantity}{item.quantity}{/if}
								{#if item.unit} {item.unit}{/if}
							</span>
						</li>
					{/each}
				</ul>
			</div>
		{/each}
	</div>
{/if}
