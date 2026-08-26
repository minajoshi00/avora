/**
 * Maintenance mode helpers.
 *
 * NOTE: This module runs inside the browser (it is imported by client-side
 * React components). Do NOT import server-only SDKs here — they reference
 * Node.js globals (e.g. `process`) and crash the web app in the browser.
 *
 * Instead we call the maintenance endpoints over HTTP, exactly like the rest
 * of the front end (App.tsx / MaintenancePage use `/api/admin/maintenance/status`).
 *
 * Returns:
 *   maintenanceMode: true if maintenance mode is active, false otherwise.
 *   Defaults to false (website online) if the backend is unavailable
 *   (fail-safe behavior).
 */
export async function getMaintenanceStatus(): Promise<{ maintenanceMode: boolean }> {
	try {
		const res = await fetch('/api/admin/maintenance/status', { cache: 'no-store' });
		if (!res.ok) {
			return { maintenanceMode: false };
		}
		const data = await res.json();
		// Default to false if not set (fail-safe: website online by default)
		return { maintenanceMode: data?.maintenanceMode === true || data?.maintenanceMode === 'true' };
	} catch (error) {
		console.error('Failed to fetch maintenance mode:', error);
		// Fail-safe: if backend is unavailable, default to website online
		return { maintenanceMode: false };
	}
}

/**
 * Toggle the maintenance mode.
 *
 * Requires admin password validation.
 * The password is validated against the expected value provided by the caller.
 *
 * @param expectedPassword - The admin password to validate against (from MAINTENANCE_ADMIN_PASSWORD env var)
 * @returns maintenanceMode: the new maintenance mode state.
 * @returns error: if the toggle fails or authentication fails.
 */
export async function toggleMaintenance(
	options?: { expectedPassword?: string; password?: string }
): Promise<{ maintenanceMode: boolean; error?: string }> {
	try {
		const expectedPassword = options?.expectedPassword;
		const password = options?.password;

		if (!expectedPassword || !password) {
			return { maintenanceMode: false, error: 'Missing password parameters.' };
		}

		// Validate password against expected value
		if (password !== expectedPassword) {
			return { maintenanceMode: false, error: 'Unauthorized. Invalid admin password.' };
		}

		const res = await fetch('/api/admin/maintenance', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ password }),
		});
		if (!res.ok) {
			return { maintenanceMode: false, error: 'Failed to toggle maintenance mode' };
		}
		const data = await res.json();
		return { maintenanceMode: data?.maintenanceMode === true || data?.maintenanceMode === 'true' };
	} catch (error) {
		console.error('Failed to toggle maintenance mode:', error);
		return { maintenanceMode: false, error: 'Failed to toggle maintenance mode' };
	}
}