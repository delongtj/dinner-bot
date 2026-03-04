<script lang="ts">
	import { goto } from '$app/navigation';
	import { register } from '$lib/api/client';

	let mode = $state<'create' | 'join'>('create');
	let name = $state('');
	let familyName = $state('');
	let inviteCode = $state('');
	let loading = $state(false);
	let error = $state('');

	async function handleCreate() {
		loading = true;
		error = '';
		try {
			await register(name || undefined);
			goto('/');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}

	async function handleJoin() {
		if (!inviteCode.trim()) {
			error = 'Please enter an invite code';
			return;
		}
		loading = true;
		error = '';
		try {
			await register(name || undefined, inviteCode.trim());
			goto('/');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to join family';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Setup - DinnerBot</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-stone-50 px-4">
	<div class="w-full max-w-md">
		<h1 class="mb-2 text-center text-2xl font-bold text-stone-800">Welcome to DinnerBot</h1>
		<p class="mb-8 text-center text-sm text-stone-500">Set up your account to get started</p>

		<div class="mb-6 flex rounded-lg border border-stone-200 bg-white p-1">
			<button
				onclick={() => { mode = 'create'; error = ''; }}
				class="flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors {mode === 'create' ? 'bg-amber-500 text-white' : 'text-stone-600 hover:text-stone-800'}"
			>
				Create a Family
			</button>
			<button
				onclick={() => { mode = 'join'; error = ''; }}
				class="flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors {mode === 'join' ? 'bg-amber-500 text-white' : 'text-stone-600 hover:text-stone-800'}"
			>
				Join a Family
			</button>
		</div>

		<div class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
			<div class="space-y-4">
				<label class="block">
					<span class="text-sm font-medium text-stone-700">Your Name</span>
					<input
						type="text"
						bind:value={name}
						placeholder="Tyler"
						class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
					/>
				</label>

				{#if mode === 'join'}
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Invite Code</span>
						<input
							type="text"
							bind:value={inviteCode}
							placeholder="ABC12345"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm tracking-widest uppercase focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
						<span class="mt-1 text-xs text-stone-400">Ask your family member for their invite code</span>
					</label>
				{/if}

				{#if error}
					<p class="text-sm text-red-600">{error}</p>
				{/if}

				<button
					onclick={() => mode === 'create' ? handleCreate() : handleJoin()}
					disabled={loading}
					class="w-full rounded-md bg-amber-500 px-4 py-2.5 font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
				>
					{#if loading}
						Setting up...
					{:else if mode === 'create'}
						Create Family
					{:else}
						Join Family
					{/if}
				</button>
			</div>
		</div>
	</div>
</div>
