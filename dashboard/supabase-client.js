/**
 * Athena SCIP - Supabase Client Singleton
 * Single source of truth for Supabase client
 */

// Check if already exists to prevent duplicate declaration
if (typeof window.supabaseClient === 'undefined') {
    // Use CONFIG from config.js
    const _CONFIG = window.CONFIG || CONFIG;
    
    window.supabaseClient = supabase.createClient(
        _CONFIG.SUPABASE_URL || 'https://catpprgdbvenutyyjqbx.supabase.co',
        _CONFIG.SUPABASE_KEY || 'sb_publishable_ykiqckKEQw2m8XXvX4cGnQ_5ijzb7Py'
    );
    console.log('✅ Supabase client initialized');
}

// Export for use in other files
const supabaseClient = window.supabaseClient;