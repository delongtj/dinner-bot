<script lang="ts">
	import { goto } from '$app/navigation';
	import { getAuth } from '$lib/auth.svelte';

	const auth = getAuth();
	let error = $state('');

	$effect(() => {
		if (!auth.loading && auth.user) {
			goto('/');
		}
	});

	async function handleLogin() {
		error = '';
		try {
			await auth.login();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Sign-in failed';
		}
	}
</script>

<svelte:head>
	<title>Sign In - DinnerBot</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-stone-50">
	<div class="w-full max-w-sm rounded-lg border border-stone-200 bg-white p-8 shadow-sm">
		<h1 class="mb-2 text-center text-2xl font-bold text-stone-800">DinnerBot</h1>
		<p class="mb-8 text-center text-sm text-stone-500">Meal planning for your family</p>

		<button
			onclick={handleLogin}
			class="flex w-full items-center justify-center gap-2 rounded-md bg-amber-500 px-4 py-2.5 font-medium text-white transition-colors hover:bg-amber-600"
		>
			Sign in with Google
		</button>

		{#if error}
			<p class="mt-4 text-center text-sm text-red-600">{error}</p>
		{/if}
	</div>
</div>
