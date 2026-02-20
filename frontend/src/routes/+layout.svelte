<script lang="ts">
	import '../app.css';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { getAuth } from '$lib/auth.svelte';
	import Nav from '$lib/components/Nav.svelte';

	let { children } = $props();
	const auth = getAuth();

	$effect(() => {
		if (!auth.loading && !auth.user && page.url.pathname !== '/login') {
			goto('/login');
		}
	});
</script>

{#if auth.loading}
	<div class="flex h-screen items-center justify-center bg-stone-50">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-amber-500"></div>
	</div>
{:else if !auth.user}
	{@render children()}
{:else}
	<div class="min-h-screen bg-stone-50">
		<Nav />
		<main class="mx-auto max-w-5xl px-4 py-8">
			{@render children()}
		</main>
	</div>
{/if}
