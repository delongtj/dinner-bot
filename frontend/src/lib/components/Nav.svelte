<script lang="ts">
	import { page } from '$app/state';
	import { getAuth } from '$lib/auth.svelte';

	const auth = getAuth();

	const links = [
		{ href: '/', label: 'Home' },
		{ href: '/plan', label: 'Plan' },
		{ href: '/recipes', label: 'Recipes' },
		{ href: '/grocery', label: 'Grocery' },
		{ href: '/settings', label: 'Settings' }
	];

	function isActive(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}
</script>

<nav class="bg-stone-800 text-stone-100">
	<div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
		<div class="flex items-center gap-6">
			<a href="/" class="text-lg font-semibold text-amber-400">DinnerBot</a>
			<div class="flex gap-1">
				{#each links as link}
					<a
						href={link.href}
						class="rounded-md px-3 py-1.5 text-sm font-medium transition-colors {isActive(link.href)
							? 'bg-stone-700 text-amber-400'
							: 'text-stone-300 hover:bg-stone-700 hover:text-stone-100'}"
					>
						{link.label}
					</a>
				{/each}
			</div>
		</div>
		<div class="flex items-center gap-4">
			<span class="text-sm text-stone-400">{auth.user?.email}</span>
			<button
				onclick={() => auth.logout()}
				class="rounded-md bg-stone-700 px-3 py-1.5 text-sm font-medium text-stone-300 transition-colors hover:bg-stone-600 hover:text-stone-100"
			>
				Logout
			</button>
		</div>
	</div>
</nav>
