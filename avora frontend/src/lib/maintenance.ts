import { kv } from '@vercel/kv';

/**
 * Check the current maintenance mode status.
 * 
 * Returns:
 *   maintenanceMode: true if maintenance mode is active, false otherwise.
 *   Defaults to false (website online) if the KV store is unavailable
 *   (fail-safe behavior).
 */
export async function getMaintenanceStatus(): Promise<{ maintenanceMode: boolean }> {
        try {
                const value = await kv.get('maintenance_mode');
                // Default to false if not set (fail-safe: website online by default)
                const maintenanceMode = value === 'true';
                return { maintenanceMode };
        } catch (error) {
                console.error('Failed to fetch maintenance mode:', error);
                // Fail-safe: if KV is unavailable, default to website online
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

                // Toggle the maintenance state
                const current = await kv.get('maintenance_mode');
                const newValue = current === 'true' ? false : true;
                await kv.set('maintenance_mode', newValue.toString());

                return { maintenanceMode: newValue };
        } catch (error) {
                console.error('Failed to toggle maintenance mode:', error);
                return { maintenanceMode: false, error: 'Failed to toggle maintenance mode' };
        }
}