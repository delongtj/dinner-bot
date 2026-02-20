<script lang="ts">
	import { goto } from '$app/navigation';
	import {
		createPlanningSession,
		sendPlanningMessage,
		finalizePlan,
		abandonPlan
	} from '$lib/api/client';
	import type { ChatMessage } from '$lib/api/types';

	let sessionId = $state<string | null>(null);
	let messages = $state<ChatMessage[]>([]);
	let input = $state('');
	let loading = $state(false);
	let starting = $state(false);
	let finalizing = $state(false);
	let error = $state('');

	let chatContainer = $state<HTMLDivElement | null>(null);

	function scrollToBottom() {
		if (chatContainer) {
			// Use tick-like delay to let DOM update
			setTimeout(() => {
				chatContainer.scrollTop = chatContainer.scrollHeight;
			}, 0);
		}
	}

	async function startSession() {
		starting = true;
		error = '';
		try {
			const result = await createPlanningSession();
			sessionId = result.session_id;
			messages = result.messages ?? [];
			scrollToBottom();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to start session';
		} finally {
			starting = false;
		}
	}

	async function send() {
		if (!input.trim() || !sessionId || loading) return;
		const text = input.trim();
		input = '';
		error = '';

		messages.push({ role: 'user', content: text });
		scrollToBottom();

		loading = true;
		try {
			const result = await sendPlanningMessage(sessionId, text);
			messages.push(result.message);
			scrollToBottom();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to send message';
		} finally {
			loading = false;
		}
	}

	async function handleFinalize() {
		if (!sessionId) return;
		finalizing = true;
		error = '';
		try {
			await finalizePlan(sessionId);
			goto('/grocery');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to finalize plan';
			finalizing = false;
		}
	}

	async function handleAbandon() {
		if (!sessionId) return;
		try {
			await abandonPlan(sessionId);
		} catch {
			// Ignore errors on abandon
		}
		sessionId = null;
		messages = [];
		error = '';
	}
</script>

<svelte:head>
	<title>Plan Meals - DinnerBot</title>
</svelte:head>

{#if !sessionId}
	<div class="flex flex-col items-center justify-center py-16">
		<h1 class="mb-2 text-2xl font-bold text-stone-800">Plan Your Meals</h1>
		<p class="mb-8 text-stone-500">Start a conversation to plan dinners for the week.</p>
		<button
			onclick={startSession}
			disabled={starting}
			class="rounded-md bg-amber-500 px-6 py-3 font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
		>
			{starting ? 'Starting...' : "Let's Plan"}
		</button>
		{#if error}
			<p class="mt-4 text-sm text-red-600">{error}</p>
		{/if}
	</div>
{:else}
	<div class="flex h-[calc(100vh-10rem)] flex-col">
		<!-- Header -->
		<div class="mb-4 flex items-center justify-between">
			<h1 class="text-xl font-bold text-stone-800">Meal Planning</h1>
			<div class="flex gap-2">
				<button
					onclick={handleAbandon}
					disabled={finalizing}
					class="rounded-md bg-stone-200 px-4 py-2 text-sm font-medium text-stone-700 transition-colors hover:bg-stone-300 disabled:opacity-50"
				>
					Start Over
				</button>
				<button
					onclick={handleFinalize}
					disabled={finalizing || loading}
					class="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
				>
					{finalizing ? 'Finalizing...' : 'Lock It In'}
				</button>
			</div>
		</div>

		<!-- Messages -->
		<div
			bind:this={chatContainer}
			class="flex-1 space-y-4 overflow-y-auto rounded-lg border border-stone-200 bg-white p-4"
		>
			{#each messages as msg}
				<div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
					<div
						class="max-w-[80%] rounded-lg px-4 py-2.5 text-sm {msg.role === 'user'
							? 'bg-amber-500 text-white'
							: 'bg-stone-100 text-stone-800'}"
					>
						<p class="whitespace-pre-wrap">{msg.content}</p>
					</div>
				</div>
			{/each}
			{#if loading}
				<div class="flex justify-start">
					<div class="rounded-lg bg-stone-100 px-4 py-2.5">
						<div class="flex gap-1">
							<div class="h-2 w-2 animate-bounce rounded-full bg-stone-400"></div>
							<div class="h-2 w-2 animate-bounce rounded-full bg-stone-400" style="animation-delay: 0.1s"></div>
							<div class="h-2 w-2 animate-bounce rounded-full bg-stone-400" style="animation-delay: 0.2s"></div>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- Input -->
		{#if error}
			<p class="mt-2 text-sm text-red-600">{error}</p>
		{/if}
		<form onsubmit={(e) => { e.preventDefault(); send(); }} class="mt-3 flex gap-3">
			<input
				type="text"
				bind:value={input}
				placeholder="Type a message..."
				disabled={loading || finalizing}
				class="flex-1 rounded-md border border-stone-300 px-4 py-2.5 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-50"
			/>
			<button
				type="submit"
				disabled={loading || !input.trim() || finalizing}
				class="rounded-md bg-amber-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
			>
				Send
			</button>
		</form>
	</div>
{/if}
