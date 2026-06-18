/**
 * Athena SCIP - Central Configuration
 * Single source of truth for API URLs, icons, and settings
 */
const CONFIG = {
    // API Configuration
    API_URL: 'https://athena-scip-api.onrender.com',
    
    // Supabase Configuration
    SUPABASE_URL: 'https://catpprgdbvenutyyjqbx.supabase.co',
    SUPABASE_KEY: 'sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py',
    
    // Display Configuration
    ICONS: {
        home: '🏠',
        recommendations: '💡',
        events: '📰',
        analytics: '📊',
        logout: '🚪',
        login: '🔒',
        warning: '⚠️',
        success: '✅',
        error: '❌',
        loading: '⏳',
        refresh: '🔄',
        export: '📥',
        filter: '🔍',
        chart: '📈',
        price: '💰',
        risk: '⚠️',
        shipping: '🚢',
        weather: '🌤️',
        country: '🌍',
        commodity: '🛢️',
        calendar: '📅',
        time: '🕐',
        location: '📍',
        source: '📡',
        severity: '🚨',
        urgency: '⚡',
        action: '⚙️',
        cost: '💲',
        leadTime: '⏱️',
        alternative: '🔄',
        scenario: '🎯'
    },
    
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

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}