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

export async function toggleMaintenance(
	password: string
): Promise<{ maintenanceMode: boolean; error?: string }> {
	try {
		const res = await fetch('/api/admin/maintenance/toggle', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ password }),
		});
		if (!res.ok) {
			const data = await res.json().catch(() => ({}));
			return { maintenanceMode: false, error: data.error || 'Failed to toggle maintenance mode' };
		}
		const data = await res.json();
		return { maintenanceMode: data?.maintenanceMode === true || data?.maintenanceMode === 'true' };
	} catch (error) {
		console.error('Failed to toggle maintenance mode:', error);
		return { maintenanceMode: false, error: 'Failed to toggle maintenance mode' };
	}
}