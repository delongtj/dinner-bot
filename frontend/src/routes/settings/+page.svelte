<script lang="ts">
	import { getConfig, setupConfig, getMe, createInvite } from '$lib/api/client';
	import type { FamilyConfig, UserInfo } from '$lib/api/types';

	let loading = $state(true);
	let saving = $state(false);
	let error = $state('');
	let success = $state('');

	// Family info
	let familyName = $state('');
	let members = $state<{ email: string; name: string | null }[]>([]);
	let inviteCode = $state('');
	let inviteExpires = $state('');
	let inviteLoading = $state(false);
	let inviteError = $state('');

	// Config fields
	let zipCode = $state('');
	let servingSize = $state(2);
	let targetPrepTime = $state('');
	let cuisinePreferences = $state('');
	let dietaryRestrictions = $state('');
	let sharedCalendarId = $state('');
	let personalCalendarIds = $state('');

	async function load() {
		try {
			const [meResult, configResult] = await Promise.all([getMe(), getConfig()]);

			familyName = meResult.family?.name ?? '';
			members = meResult.members ?? [];

			const config = configResult.config;
			if (config) {
				zipCode = config.zip_code ?? '';
				servingSize = config.serving_size ?? 2;
				targetPrepTime = config.target_prep_time?.toString() ?? '';
				cuisinePreferences = (config.cuisine_preferences ?? []).join(', ');
				dietaryRestrictions = (config.dietary_restrictions ?? []).join(', ');
				sharedCalendarId = config.shared_calendar_id ?? '';
				personalCalendarIds = (config.personal_calendar_ids ?? []).join(', ');
			}
		} catch (e) {
			// No config yet — that's fine, user will fill in the form
		} finally {
			loading = false;
		}
	}

	load();

	function splitComma(s: string): string[] {
		return s
			.split(',')
			.map((x) => x.trim())
			.filter(Boolean);
	}

	async function handleSave() {
		saving = true;
		error = '';
		success = '';
		try {
			await setupConfig({
				zip_code: zipCode || null,
				serving_size: servingSize,
				target_prep_time: targetPrepTime ? parseInt(targetPrepTime) : null,
				cuisine_preferences: splitComma(cuisinePreferences),
				dietary_restrictions: splitComma(dietaryRestrictions),
				shared_calendar_id: sharedCalendarId || null,
				personal_calendar_ids: splitComma(personalCalendarIds)
			});
			success = 'Settings saved.';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save settings';
		} finally {
			saving = false;
		}
	}

	async function handleGenerateInvite() {
		inviteLoading = true;
		inviteError = '';
		inviteCode = '';
		try {
			const result = await createInvite();
			inviteCode = result.code;
			inviteExpires = new Date(result.expires_at).toLocaleDateString();
		} catch (e) {
			inviteError = e instanceof Error ? e.message : 'Failed to generate invite';
		} finally {
			inviteLoading = false;
		}
	}

	async function copyInviteCode() {
		await navigator.clipboard.writeText(inviteCode);
	}
</script>

<svelte:head>
	<title>Settings - DinnerBot</title>
</svelte:head>

<h1 class="mb-6 text-2xl font-bold text-stone-800">Settings</h1>

{#if loading}
	<div class="flex justify-center py-12">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-stone-300 border-t-amber-500"></div>
	</div>
{:else}
	<div class="space-y-6">
		<div class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
			<h2 class="mb-4 text-lg font-semibold text-stone-800">Family</h2>
			<p class="mb-3 text-sm text-stone-600">{familyName}</p>

			<div class="mb-4">
				<h3 class="mb-2 text-sm font-medium text-stone-700">Members</h3>
				<ul class="space-y-1">
					{#each members as member}
						<li class="text-sm text-stone-600">
							{member.name ?? 'No name'} — {member.email}
						</li>
					{/each}
				</ul>
			</div>

			<div>
				<button
					onclick={handleGenerateInvite}
					disabled={inviteLoading}
					class="rounded-md bg-stone-100 px-4 py-2 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-200 disabled:opacity-50"
				>
					{inviteLoading ? 'Generating...' : 'Generate Invite Code'}
				</button>

				{#if inviteCode}
					<div class="mt-3 flex items-center gap-2">
						<code class="rounded bg-stone-100 px-3 py-1.5 text-lg font-mono tracking-widest text-stone-800">{inviteCode}</code>
						<button
							onclick={copyInviteCode}
							class="rounded-md bg-amber-500 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-amber-600"
						>
							Copy
						</button>
					</div>
					<p class="mt-1 text-xs text-stone-400">Expires {inviteExpires}</p>
				{/if}

				{#if inviteError}
					<p class="mt-2 text-sm text-red-600">{inviteError}</p>
				{/if}
			</div>
		</div>

		<form onsubmit={(e) => { e.preventDefault(); handleSave(); }} class="space-y-6">
			<div class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
				<h2 class="mb-4 text-lg font-semibold text-stone-800">Household</h2>
				<div class="grid gap-4 sm:grid-cols-2">
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Zip Code</span>
						<input
							type="text"
							bind:value={zipCode}
							placeholder="30301"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
					</label>
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Serving Size</span>
						<input
							type="number"
							bind:value={servingSize}
							min="1"
							max="20"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
					</label>
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Target Prep Time (minutes)</span>
						<input
							type="number"
							bind:value={targetPrepTime}
							placeholder="30"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
					</label>
				</div>
			</div>

			<div class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
				<h2 class="mb-4 text-lg font-semibold text-stone-800">Preferences</h2>
				<div class="grid gap-4">
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Cuisine Preferences</span>
						<input
							type="text"
							bind:value={cuisinePreferences}
							placeholder="Italian, Mexican, Thai"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
						<span class="mt-1 text-xs text-stone-400">Comma-separated</span>
					</label>
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Dietary Restrictions</span>
						<input
							type="text"
							bind:value={dietaryRestrictions}
							placeholder="Gluten-free, Nut allergy"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
						<span class="mt-1 text-xs text-stone-400">Comma-separated</span>
					</label>
				</div>
			</div>

			<div class="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
				<h2 class="mb-4 text-lg font-semibold text-stone-800">Google Calendar</h2>
				<div class="grid gap-4">
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Shared Calendar ID</span>
						<input
							type="text"
							bind:value={sharedCalendarId}
							placeholder="family@group.calendar.google.com"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
					</label>
					<label class="block">
						<span class="text-sm font-medium text-stone-700">Personal Calendar IDs</span>
						<input
							type="text"
							bind:value={personalCalendarIds}
							placeholder="you@gmail.com, spouse@gmail.com"
							class="mt-1 block w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
						/>
						<span class="mt-1 text-xs text-stone-400">Comma-separated — used to check for busy days</span>
					</label>
				</div>
			</div>

			{#if error}
				<p class="text-sm text-red-600">{error}</p>
			{/if}
			{#if success}
				<p class="text-sm text-green-600">{success}</p>
			{/if}

			<button
				type="submit"
				disabled={saving}
				class="rounded-md bg-amber-500 px-6 py-2.5 font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
			>
				{saving ? 'Saving...' : 'Save Settings'}
			</button>
		</form>
	</div>
{/if}
