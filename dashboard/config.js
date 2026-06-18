/**
 * Athena SCIP - Central Configuration
 * Single source of truth for API URLs, icons, and settings
 */

// Use window to prevent duplicate declaration
if (typeof window.CONFIG === 'undefined') {
    window.CONFIG = {
        // API Configuration
        API_URL: 'https://athena-scip-api.onrender.com',
        
        // Supabase Configuration
        SUPABASE_URL: 'https://catpprgdbvenutyyjqbx.supabase.co',
        SUPABASE_KEY: 'sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py',
        
        // Default Settings
        DEFAULT_DAYS: 14,
        DEFAULT_EVENTS_LIMIT: 100,
        DEFAULT_RECOMMENDATIONS_LIMIT: 50,
        MAX_EXPORT_LIMIT: 10000,
        
        // Color Palette (for charts and severity)
        COLORS: {
            critical: '#dc2626',
            high: '#f97316',
            medium: '#eab308',
            low: '#22c55e',
            info: '#3b82f6',
            chart: [
                '#dc2626', '#f97316', '#eab308', '#22c55e',
                '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6',
                '#f59e0b', '#6366f1', '#06b6d4', '#84cc16'
            ]
        }
    };
}

// Reference for use in other files
const CONFIG = window.CONFIG;