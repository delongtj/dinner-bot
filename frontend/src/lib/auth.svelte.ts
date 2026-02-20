import { auth } from '$lib/firebase';
import { GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';
import type { User } from 'firebase/auth';

let user = $state<User | null>(null);
let loading = $state(!auth ? false : true);

if (auth) {
	onAuthStateChanged(auth, (firebaseUser) => {
		user = firebaseUser;
		loading = false;
	});
}

function login() {
	if (!auth) throw new Error('Firebase not configured');
	const provider = new GoogleAuthProvider();
	return signInWithPopup(auth, provider);
}

function logout() {
	if (!auth) throw new Error('Firebase not configured');
	return signOut(auth);
}

export function getAuth() {
	return {
		get user() {
			return user;
		},
		get loading() {
			return loading;
		},
		login,
		logout
	};
}
