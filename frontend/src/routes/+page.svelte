<svelte:head>
	<title>DinnerBot</title>
</svelte:head>

<h1 class="mb-6 text-2xl font-bold text-stone-800">Dashboard</h1>

<div class="grid gap-4 sm:grid-cols-2">
	<a
		href="/plan"
		class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
	>
		<h2 class="mb-2 text-lg font-semibold text-stone-800">Plan Meals</h2>
		<p class="text-sm text-stone-500">Start an interactive meal planning session for the week.</p>
	</a>

	<a
		href="/recipes"
		class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
	>
		<h2 class="mb-2 text-lg font-semibold text-stone-800">Recipes</h2>
		<p class="text-sm text-stone-500">Browse your recipe library or add new ones.</p>
	</a>

	<a
		href="/grocery"
		class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
	>
		<h2 class="mb-2 text-lg font-semibold text-stone-800">Grocery List</h2>
		<p class="text-sm text-stone-500">View the aggregated grocery list for your meal plan.</p>
	</a>

	<a
		href="/settings"
		class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
	>
		<h2 class="mb-2 text-lg font-semibold text-stone-800">Settings</h2>
		<p class="text-sm text-stone-500">Configure family preferences, calendars, and dietary needs.</p>
	</a>
</div>
